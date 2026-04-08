import asyncio
import os
import textwrap
import httpx
from typing import List, Optional, Dict, Any
from openai import OpenAI
import subprocess
import time
import socket

# Required Hackathon Variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

TASK_NAME = os.getenv("COURTROOM_TASK", "case-001-easy")
BENCHMARK = "courtroom-sim"
MAX_STEPS = 8
TEMPERATURE = 0.7
MAX_TOKENS = 150
SUCCESS_SCORE_THRESHOLD = 0.5 

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an AI Lawyer operating in an Indian Courtroom Environment.
    Your goal is to present logically sound arguments and reference specific evidence to win the case.
    The environment expects a JSON-like representation of your action.
    Reply with exactly one valid JSON string containing "argument" (your spoken reasoning) and "evidence_referenced" (a string matching exactly the name of the evidence from the available list, or null if no evidence).
    Example: {"argument": "The witness testimony directly contradicts...", "evidence_referenced": "Witness A Statement"}
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    # Normalize action string for single line logging
    action_str = action.replace('\n', ' ').replace('"', "'")
    print(f"[STEP] step={step} action=\"{action_str}\" reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def build_user_prompt(step: int, last_obs: Dict[str, Any], history: List[str]) -> str:
    history_block = "\n".join(history[-4:]) if history else "None"
    evidence_list = "\n".join([f"- {e}" for e in last_obs.get('evidence', [])])
    return textwrap.dedent(
        f"""
        Step: {step}
        Case Facts: {last_obs.get('case_facts', '')}
        Available Evidence:
        {evidence_list}
        Judge Last Response: {last_obs.get('judge_response', '')}
        Previous dialogue:
        {history_block}
        
        Send your next valid JSON action.
        """
    ).strip()

def get_model_action(client: OpenAI, step: int, last_obs: Dict[str, Any], history: List[str]) -> Dict[str, Any]:
    user_prompt = build_user_prompt(step, last_obs, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"} if "Qwen" not in MODEL_NAME else None # Optional JSON mode if supported
        )
        text = completion.choices[0].message.content.strip()
        import json
        try:
            return json.loads(text)
        except:
            # Fallback parsing
            return {"argument": text, "evidence_referenced": None}
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return {"argument": "I rest my case.", "evidence_referenced": None}

class ProcessEnvClient:
    def __init__(self, port=7860):
        self.port = port
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.process = None
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def start_server(self):
        # Only start if port is not already bound
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', self.port)) != 0:
                self.process = subprocess.Popen(["python", "-m", "uvicorn", "env:app", "--host", "127.0.0.1", "--port", str(self.port)])
                
                # Robust wait for up to 10 seconds for the server to be ready
                for _ in range(20):
                    time.sleep(0.5)
                    try:
                        resp = httpx.get(self.base_url)
                        if resp.status_code == 200:
                            break
                    except Exception:
                        pass
    
    async def reset(self):
        resp = await self.client.post("/reset")
        return resp.json()

    async def step(self, action: Dict[str, Any]):
        resp = await self.client.post("/step", json=action)
        return resp.json()
        
    async def close(self):
        await self.client.aclose()
        if self.process:
            self.process.terminate()

async def main():
    if not HF_TOKEN:
        print("[DEBUG] WARNING: HF_TOKEN not set, OpenAI calls may fail.", flush=True)
    
    # Use a dummy key if none provided so the client init doesn't instantly crash
    safe_api_key = HF_TOKEN or "dummy_key_for_testing"
    client = OpenAI(base_url=API_BASE_URL, api_key=safe_api_key)
    
    env = ProcessEnvClient(port=7860)
    await env.start_server()

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset()
        last_obs = result["observation"]
        
        for step in range(1, MAX_STEPS + 1):
            if result.get("done", False):
                break

            action_dict = get_model_action(client, step, last_obs, history)
            action_str = action_dict.get("argument", "") + " | " + str(action_dict.get("evidence_referenced", ""))
            
            result = await env.step(action_dict)
            obs = result["observation"]
            reward = result.get("reward", 0.0)
            done = result.get("done", False)
            error = result.get("error", None)

            rewards.append(reward)
            steps_taken = step
            last_obs = obs
            
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)
            history.append(f"Step {step}: Action: {action_str} -> reward {reward:+.2f}")

            if done:
                break

        score = sum(rewards)
        score = min(max(score, 0.01), 0.99) # Clamp score exactly between [0.01, 0.99]
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)
        
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
