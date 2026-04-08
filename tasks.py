from pydantic import BaseModel
from typing import List, Dict

class CourtroomTask(BaseModel):
    id: str
    difficulty: str
    case_facts: str
    evidence: List[str]
    required_evidence: List[str] # used for deterministic grading
    max_turns: int

TASKS = [
    CourtroomTask(
        id="case-001-easy",
        difficulty="easy",
        case_facts="""A simple breach of contract dispute. 
The plaintiff claims the defendant failed to deliver 100 units of electronics as per invoice #1004. 
The defendant claims they never received payment.""",
        evidence=["Invoice #1004", "Bank Transfer Receipt showing payment"],
        required_evidence=["Bank Transfer Receipt showing payment"],
        max_turns=3
    ),
    CourtroomTask(
        id="case-002-medium",
        difficulty="medium",
        case_facts="""A theft accusation in a jewelry store. 
Witness A (store clerk) claims they saw the defendant pocket a watch. 
Witness B (a customer outside) claims the defendant was outside the store at the time of the theft. 
The CCTV footage from the store was mysteriously wiped.""",
        evidence=[
            "Witness A Statement", 
            "Witness B Statement", 
            "Defendant's Alibi (Phone GPS record showing them at a cafe)", 
            "CCTV system log showing a reboot at the time of theft"
        ],
        required_evidence=["Defendant's Alibi (Phone GPS record showing them at a cafe)"],
        max_turns=5
    ),
    CourtroomTask(
        id="case-003-hard",
        difficulty="hard",
        case_facts="""A complex corporate fraud and embezzlement case. 
The CEO is accused of funneling company funds into an offshore shell company. 
The defense argues the transfers were legitimate business expenses authorized by the board. 
There are multiple encrypted emails, board meeting minutes, and financial ledgers.""",
        evidence=[
            "Board Meeting Minutes from Jan 15th",
            "Encrypted Email chain between CEO and Offshore Entity",
            "Financial Ledger Excerpt 2023 Q2",
            "Whistleblower Statement from CFO"
        ],
        required_evidence=[
            "Encrypted Email chain between CEO and Offshore Entity", 
            "Whistleblower Statement from CFO"
        ],
        max_turns=8
    )
]

def get_task(task_id: str) -> CourtroomTask:
    for task in TASKS:
        if task.id == task_id:
            return task
    # Default to easy if not found
    return TASKS[0]
