"""
DisasterOps-Env: Baseline Inference Script.

Runs an LLM agent against the disaster response environment using the OpenAI client.
Follows the mandatory [START], [STEP], [END] output format.

Usage:
    export HF_TOKEN="your_token"
    python inference.py

Environment variables:
    API_BASE_URL    LLM API endpoint (default: HF router)
    MODEL_NAME      Model identifier (default: Qwen/Qwen2.5-72B-Instruct)
    HF_TOKEN        API key
    TASK_ID         Specific task to run (default: runs all 5)
    DISASTER_TASK   Alternative task env var
"""

import asyncio
import json
import os
import re
import subprocess
import socket
import sys
import textwrap
import time
from typing import Dict, Any, List, Optional

import httpx
from openai import OpenAI

# ── Required Hackathon Variables ──
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

# Optional — if you use from_docker_image():
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

TASK_NAME = (os.getenv("TASK_ID") or os.getenv("TASK_NAME") or
             os.getenv("OPENENV_TASK") or os.getenv("TASK") or
             os.getenv("DISASTER_TASK"))  # None means run all tasks
BENCHMARK = "disasterops-env"
TEMPERATURE = 0.6
MAX_TOKENS = 300
SUCCESS_THRESHOLD = 0.3

ALL_TASKS = [
    "disaster-001-flood",
    "disaster-002-earthquake",
    "disaster-003-hurricane",
    "disaster-004-cascading",
    "disaster-005-megadisaster",
]

TASK_MAX_STEPS = {
    "disaster-001-flood": 8,
    "disaster-002-earthquake": 10,
    "disaster-003-hurricane": 12,
    "disaster-004-cascading": 14,
    "disaster-005-megadisaster": 16,
}

ANALYST_SYSTEM_PROMPT = textwrap.dedent("""
You are the Intelligence Analyst at an Emergency Operations Center (EOC).
Your job is to read the raw data from the field, calculate where people are in the most danger, and write a <thought_process> outlining the priorities.
Pay close attention to cascading warnings, budget remaining, and wind directions which carry chemical spills.

You do NOT issue commands. You must output your analysis enclosed in <thought_process> tags, followed by a succinct SUMMARY of the top 3 priorities.
""").strip()

CHIEF_SYSTEM_PROMPT = textwrap.dedent("""
You are the Operations Chief at an Emergency Operations Center (EOC).
You receive the Intelligence Analyst's report and must decide on ONE action to take this step.
Analyze the report and your operational budget in a <thought_process> block.
Then output exactly ONE JSON action object.

ACTION COSTS:
- Helicopter deploy: $15,000
- Evacuate Zone: $10,000
- Truck/Rescue/Medical deploy: $5,000
- Open Shelter: $15,000
- Call Mutual Aid: $100,000

AVAILABLE ACTIONS (respond with JSON):
{
  "command": "<action_type>",
  "target_zone": "<zone_id>",
  "resource_type": "<resource_type_if_needed>",
  "parameters": {}
}

ACTION TYPES:
- deploy_resource: Send a resource unit to a zone. Requires target_zone and resource_type.
  resource_type options: medical_team, rescue_squad, helicopter, supply_truck
- evacuate_zone: Begin evacuation of a zone. Requires target_zone.
- open_shelter: Open an emergency shelter. Optionally target_zone.
- request_sitrep: Get situation report. Optionally target_zone.
- call_mutual_aid: Request additional resources (arrive in 2 steps).
- recall_resource: Pull back a deployed resource. Requires target_zone.

STRATEGY:
1. PRIORITIZE critical zones with trapped people — they die without help
2. If budget is low, prioritize cheap actions like request_sitrep or truck deployments
3. HEED WARNINGS about cascading events — evacuate threatened zones BEFORE disaster strikes

Respond with your <thought_process> first, then ONLY valid JSON.
""").strip()


# ── Logging Functions ──

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_clean = action.replace("\n", " ").replace('"', "'")[:200]
    print(f"[STEP] step={step} action={action_clean} reward={reward:.2f} done={done_val} error={error_val}",
          flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.3f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
          flush=True)


# ── LLM Interaction ──

def build_user_prompt(step: int, obs: Dict[str, Any], history: List[str]) -> str:
    """Build context-rich prompt from observation."""
    # Extract key info from observation
    zone_statuses = obs.get("zone_statuses", {})
    resource_pool = obs.get("resource_pool", {})
    warnings = obs.get("pending_warnings", [])
    sitreps = obs.get("situation_reports", [])
    casualty_summary = obs.get("casualty_summary", {})
    last_result = obs.get("last_action_result", "")
    weather = obs.get("weather_conditions", "clear")
    wind = obs.get("wind_direction", "none")
    budget = obs.get("operational_budget", 0.0)
    roads = obs.get("road_network", {})
    shelters = obs.get("shelter_status", {})
    deployed = obs.get("deployed_resources", [])
    available_actions = obs.get("available_actions", [])
    max_steps = obs.get("max_steps", 10)

    # Format critical zones
    critical_zones = []
    for zid, z in zone_statuses.items():
        if isinstance(z, dict) and z.get("status") in ("critical", "affected"):
            critical_zones.append(
                f"  - {z.get('name', zid)} [{zid}]: status={z['status']}, "
                f"trapped={z.get('trapped_people', 0)}, "
                f"casualties={z.get('casualties', 0)}, "
                f"damage={z.get('damage_level', 0):.0%}, "
                f"access={z.get('accessibility', '?')}, "
                f"resources_on_scene={len(z.get('resources_present', []))}"
            )

    zones_text = "\n".join(critical_zones) if critical_zones else "  No critical/affected zones"

    # Format resources
    res_text = (f"  Available: med={resource_pool.get('medical_teams', 0)}, "
                f"rescue={resource_pool.get('rescue_squads', 0)}, "
                f"heli={resource_pool.get('helicopters', 0)}, "
                f"trucks={resource_pool.get('supply_trucks', 0)}")

    # Format warnings
    warn_text = "\n".join(f"  {w}" for w in warnings) if warnings else "  None"

    # Format latest sitreps
    sitrep_text = ""
    for sr in sitreps[-3:]:
        if isinstance(sr, dict):
            sitrep_text += f"  [{sr.get('severity', '?')}] {sr.get('report', '')}\n"

    # Blocked roads
    blocked = [f"  {k}: {v}" for k, v in roads.items() if v in ("blocked", "flooded", "destroyed")]
    blocked_text = "\n".join(blocked) if blocked else "  All roads passable"

    # Deployed resources
    dep_text = "\n".join(f"  {d.get('unit_id')}->{d.get('zone')}" for d in deployed) if deployed else "  None"

    # History
    hist_text = "\n".join(history[-3:]) if history else "  None"

    # Casualty summary
    cas = casualty_summary
    cas_text = (f"  At risk: {cas.get('total_population_at_risk', '?')}, "
                f"Evacuated: {cas.get('total_evacuated', 0)}, "
                f"Casualties: {cas.get('total_casualties', 0)}, "
                f"Trapped: {cas.get('total_trapped', 0)}")

    return textwrap.dedent(f"""
Step {step}/{max_steps} | Weather: {weather} | Wind: {wind}
Remaining Budget: ${budget:,.2f}
Last action result: {last_result}

═══ CRITICAL/AFFECTED ZONES ═══
{zones_text}

═══ RESOURCES ═══
{res_text}
Deployed:
{dep_text}

═══ WARNINGS ═══
{warn_text}

═══ BLOCKED ROADS ═══
{blocked_text}

═══ CASUALTY SUMMARY ═══
{cas_text}

═══ LATEST SITREPS ═══
{sitrep_text}
═══ RECENT HISTORY ═══
{hist_text}

Available actions: {', '.join(available_actions)}
Respond with a single JSON action object. Think about what saves the most lives RIGHT NOW.
    """).strip()


def get_model_action(client: OpenAI, step: int, obs: Dict[str, Any],
                     history: List[str]) -> Dict[str, Any]:
    """Get action using a Multi-Agent CoT orchestration."""
    user_prompt = build_user_prompt(step, obs, history)

    try:
        # Agent 1: Intelligence Analyst
        comp1 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=600,
            stream=False,
        )
        analyst_output = (comp1.choices[0].message.content or "").strip()
        
        # Agent 2: Operations Chief
        chief_prompt = f"{user_prompt}\n\n=== INTELLIGENCE ANALYST REPORT ===\n{analyst_output}"
        
        comp2 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": CHIEF_SYSTEM_PROMPT},
                {"role": "user", "content": chief_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=600,
            stream=False,
        )
        chief_output = (comp2.choices[0].message.content or "").strip()

        # Parse JSON from Chief response
        json_match = re.search(r'\{[^{}]*\}', chief_output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

        return json.loads(chief_output)

    except json.JSONDecodeError:
        print(f"[DEBUG] Failed to parse JSON from model response", flush=True)
        return {"command": "request_sitrep"}
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return {"command": "request_sitrep"}


# ── Environment Client ──

class ProcessEnvClient:
    """HTTP client that optionally starts the env server as a subprocess."""

    def __init__(self, port=7860):
        self.port = port
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.process = None
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', self.port)) != 0:
                self.process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "env:app",
                     "--host", "127.0.0.1", "--port", str(self.port)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                for _ in range(20):
                    time.sleep(0.5)
                    try:
                        resp = httpx.get(self.base_url)
                        if resp.status_code == 200:
                            break
                    except Exception:
                        pass

    async def reset(self, task_id: str) -> Dict:
        resp = await self.client.post("/reset", json={"task": task_id})
        resp.raise_for_status()
        return resp.json()

    async def step(self, action: Dict) -> Dict:
        resp = await self.client.post("/step", json=action)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()


# ── Main Inference Loop ──

async def run_task(client_llm: OpenAI, env: ProcessEnvClient, task_id: str) -> float:
    """Run a single task and return the final score."""
    max_steps = TASK_MAX_STEPS.get(task_id, 10)
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task_id)
        last_obs = result.get("observation", {})

        for step_num in range(1, max_steps + 1):
            if result.get("done", False):
                break

            action_dict = get_model_action(client_llm, step_num, last_obs, history)
            action_str = f"{action_dict.get('command', '?')}({action_dict.get('target_zone', '')})"

            result = await env.step(action_dict)
            obs = result.get("observation", {})
            reward = result.get("reward", 0.0)
            done = result.get("done", False)
            error = result.get("error", None)

            rewards.append(reward)
            steps_taken = step_num
            last_obs = obs

            log_step(step=step_num, action=action_str, reward=reward, done=done, error=error)

            history.append(
                f"Step {step_num}: {action_str} -> reward={reward:+.2f} | "
                f"{obs.get('last_action_result', '')[:100]}"
            )

            if done:
                break

        # Calculate final score
        score = sum(rewards)
        score = min(max(score, 0.001), 0.999)
        success = score >= SUCCESS_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Task {task_id} error: {e}", flush=True)
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


async def main() -> None:
    if not HF_TOKEN:
        print("[DEBUG] WARNING: HF_TOKEN not set, LLM calls may fail.", flush=True)

    safe_key = HF_TOKEN or "dummy_key"
    client_llm = OpenAI(base_url=API_BASE_URL, api_key=safe_key)

    env = ProcessEnvClient(port=7860)
    await env.start_server()

    # Determine which tasks to run
    if TASK_NAME and TASK_NAME in ALL_TASKS:
        tasks_to_run = [TASK_NAME]
    else:
        tasks_to_run = ALL_TASKS[:3]  # Default: run first 3 tasks

    scores = {}
    try:
        for task_id in tasks_to_run:
            score = await run_task(client_llm, env, task_id)
            scores[task_id] = score
    finally:
        await env.close()

    # Print summary
    print("\n" + "=" * 60, flush=True)
    print("DISASTEROPS-ENV BASELINE RESULTS", flush=True)
    print("=" * 60, flush=True)
    for tid, sc in scores.items():
        print(f"  {tid}: {sc:.3f}", flush=True)
    avg = sum(scores.values()) / len(scores) if scores else 0
    print(f"  Average: {avg:.3f}", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
