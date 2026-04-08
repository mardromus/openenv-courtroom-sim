import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any

from courtroom_schemas import Action, Observation, StepResult
from tasks import get_task
from grader import CourtroomGrader

app = FastAPI(title="Multi-Agent Indian Courtroom RL Environment")

class EnvState:
    def __init__(self):
        self.task_id = os.getenv("COURTROOM_TASK", "case-001-easy")
        self.task = get_task(self.task_id)
        self.grader = CourtroomGrader(self.task)
        self.history = []
        self.current_turn = 0
        self.is_verdict_reached = False
        self.verdict = None

# Global state for simplicity in a single-instance container
SIM_STATE = EnvState()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Courtroom Environment Server Running"}

@app.post("/reset")
async def reset(request: Request) -> StepResult:
    # Accept anything to avoid 422 Unprocessable Entity, but extract task if present
    from fastapi import Request
    global SIM_STATE
    try:
        data = await request.json()
        task_id = data.get("task", "case-001-easy") if isinstance(data, dict) else "case-001-easy"
        os.environ["COURTROOM_TASK"] = task_id
    except:
        pass
    
    SIM_STATE = EnvState()
    
    obs = Observation(
        case_facts=SIM_STATE.task.case_facts,
        evidence=SIM_STATE.task.evidence,
        history=SIM_STATE.history,
        judge_response="The court is now in session. The plaintiff may present their opening argument.",
        current_turn=SIM_STATE.current_turn,
        is_verdict_reached=SIM_STATE.is_verdict_reached,
        verdict=SIM_STATE.verdict
    )
    return StepResult(observation=obs, reward=0.0, done=False, error=None)

@app.post("/step")
def step(action: Action) -> StepResult:
    global SIM_STATE
    
    if SIM_STATE.is_verdict_reached:
        return _build_step_result(0.0, True, "Environment already terminated.")
    
    SIM_STATE.current_turn += 1
    
    # Process the action
    SIM_STATE.history.append(f"Lawyer: {action.argument} [Evidence: {action.evidence_referenced}]")
    
    # Calculate step reward
    reward = SIM_STATE.grader.evaluate_step(action.argument, action.evidence_referenced)
    
    judge_response = "The court notes your argument."
    if action.evidence_referenced and action.evidence_referenced not in SIM_STATE.task.evidence:
        judge_response = "Objection. That evidence is not part of the record."
    
    SIM_STATE.history.append(f"Judge: {judge_response}")
    
    done = False
    
    # Termination condition
    if SIM_STATE.current_turn >= SIM_STATE.task.max_turns:
        done = True
        SIM_STATE.is_verdict_reached = True
        SIM_STATE.verdict = "The court will now deliberate."
        
        # Give final score at the end
        final_score = SIM_STATE.grader.evaluate_final(SIM_STATE.history)
        reward += final_score # add the final bonus
    
    return _build_step_result(reward, done, None, judge_response)

@app.get("/state")
def state() -> StepResult:
    return _build_step_result(0.0, SIM_STATE.is_verdict_reached, None, "Current state")

def _build_step_result(reward: float, done: bool, error: str = None, judge_response: str = "") -> StepResult:
    obs = Observation(
        case_facts=SIM_STATE.task.case_facts,
        evidence=SIM_STATE.task.evidence,
        history=SIM_STATE.history,
        judge_response=judge_response,
        current_turn=SIM_STATE.current_turn,
        is_verdict_reached=SIM_STATE.is_verdict_reached,
        verdict=SIM_STATE.verdict
    )
    return StepResult(observation=obs, reward=reward, done=done, error=error)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
