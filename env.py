"""
DisasterOps-Env: FastAPI Server.

Exposes the disaster response environment as an HTTP API with:
- POST /reset  — Initialize a new episode (accepts task ID in body)
- POST /step   — Execute an agent action
- GET  /state  — Return current environment state
- GET  /       — Health check
"""

import os
import uvicorn
from fastapi import FastAPI, Request
from typing import Optional

from schemas import Action, Observation, StepResult
from tasks import build_task, get_task_ids, TASK_METADATA
from grader import DisasterGrader
from disaster_sim import DisasterWorld

app = FastAPI(
    title="DisasterOps-Env",
    description="Emergency Disaster Response & Resource Coordination Environment for OpenEnv",
    version="1.0.0"
)


class EnvState:
    """Global mutable environment state (single-instance container)."""

    def __init__(self, task_id: str = "disaster-001-flood"):
        self.task_id = task_id
        self.world: DisasterWorld = build_task(task_id)
        self.grader: DisasterGrader = DisasterGrader(self.world)
        self.episode_done: bool = False
        self.last_reward: float = 0.0
        self.total_steps: int = 0


# Global state
STATE: Optional[EnvState] = None


def _ensure_state() -> EnvState:
    global STATE
    if STATE is None:
        default_task = os.getenv("DISASTER_TASK", "disaster-001-flood")
        STATE = EnvState(default_task)
    return STATE


@app.get("/")
def root():
    """Root info endpoint."""
    return {
        "status": "ok",
        "environment": "DisasterOps-Env",
        "description": "Emergency Disaster Response & Resource Coordination",
        "available_tasks": get_task_ids()
    }

@app.get("/health")
def health_check():
    """OpenEnv health endpoint."""
    return {"status": "healthy"}

@app.get("/metadata")
def metadata():
    """OpenEnv metadata endpoint."""
    return {
        "name": "DisasterOps-Env",
        "description": "Emergency Disaster Response & Resource Coordination Environment for OpenEnv"
    }

@app.get("/schema")
def schema():
    """OpenEnv schema endpoint."""
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": StepResult.model_json_schema()
    }

@app.post("/mcp")
async def mcp_stub(request: Request):
    """OpenEnv MCP stub endpoint."""
    return {"jsonrpc": "2.0"}

@app.post("/reset")
async def reset(request: Request) -> StepResult:
    """Reset the environment for a new episode."""
    global STATE

    # Parse task ID from request body
    task_id = "disaster-001-flood"
    try:
        data = await request.json()
        if isinstance(data, dict):
            task_id = data.get("task", data.get("task_id", task_id))
    except Exception:
        pass

    # Also check env var
    task_id = os.getenv("DISASTER_TASK", task_id)

    # Validate task
    available = get_task_ids()
    if task_id not in available:
        task_id = available[0]

    STATE = EnvState(task_id)

    obs = STATE.world.build_observation(
        last_action_result=f"Environment reset. Incident: {STATE.world.incident_name}. "
                           f"You are the Emergency Operations Center Coordinator. "
                           f"Assess the situation and begin response operations."
    )

    return StepResult(observation=obs, reward=0.0, done=False, error=None)


@app.post("/step")
async def step(request: Request) -> StepResult:
    """Execute an agent action in the environment."""
    state = _ensure_state()

    if state.episode_done:
        obs = state.world.build_observation("Episode already complete.")
        return StepResult(
            observation=obs,
            reward=0.0,
            done=True,
            error="Episode already terminated. Call /reset to start a new episode."
        )

    # Parse action from request body
    try:
        data = await request.json()
        if isinstance(data, dict):
            action = Action(**data)
        else:
            action = Action(command="request_sitrep")
    except Exception as e:
        obs = state.world.build_observation(f"Invalid action format: {str(e)}")
        return StepResult(
            observation=obs,
            reward=-0.02,
            done=False,
            error=f"Invalid action: {str(e)}"
        )

    # Advance the world simulation (casualties accumulate, resources work)
    # Apply custom weather hook if present
    if hasattr(state.world, '_custom_weather_hook'):
        state.world._custom_weather_hook()

    state.world.advance_time()
    state.total_steps += 1

    # Process the agent's action
    result_msg, action_reward = state.world.process_action(
        command=action.command,
        target_zone=action.target_zone,
        resource_type=action.resource_type,
        parameters=action.parameters
    )

    # Evaluate with grader
    step_reward = state.grader.evaluate_step(
        command=action.command,
        action_reward=action_reward,
        target_zone=action.target_zone,
        resource_type=action.resource_type
    )

    state.last_reward = step_reward

    # Check if episode is done
    done = state.world.is_done()
    if done:
        state.episode_done = True
        final_score = state.grader.evaluate_final()
        result_msg += f" | EPISODE COMPLETE. Final score: {final_score:.3f}"

    obs = state.world.build_observation(result_msg)

    return StepResult(
        observation=obs,
        reward=round(step_reward, 4),
        done=done,
        error=None
    )


@app.get("/state")
def get_state() -> StepResult:
    """Return current environment state."""
    state = _ensure_state()
    obs = state.world.build_observation("Current state snapshot.")
    return StepResult(
        observation=obs,
        reward=state.last_reward,
        done=state.episode_done,
        error=None
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port)
