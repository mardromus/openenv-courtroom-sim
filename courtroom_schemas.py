from pydantic import BaseModel
from typing import List, Optional, Dict

class Observation(BaseModel):
    case_facts: str
    evidence: List[str]
    history: List[str]
    judge_response: str
    current_turn: int
    is_verdict_reached: bool
    verdict: Optional[str] = None

class Action(BaseModel):
    argument: str
    evidence_referenced: Optional[str] = None

class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    error: Optional[str] = None
