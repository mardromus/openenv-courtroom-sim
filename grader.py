import os
from typing import List
from openai import OpenAI
from tasks import CourtroomTask

class CourtroomGrader:
    def __init__(self, task: CourtroomTask):
        self.task = task
        self.evidence_used = set()
        
        # Initialize OpenAI client for final grading (optional, can fallback to basic if no key)
        self.api_key = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
        self.api_base_url = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
        self.model_name = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
        
        self.client = None
        if self.api_key and self.api_base_url:
            self.client = OpenAI(base_url=self.api_base_url, api_key=self.api_key)

    def evaluate_step(self, argument: str, evidence_referenced: str) -> float:
        """
        Evaluate a single step. Partial rewards for using correct evidence.
        """
        reward = 0.0
        
        # Did they use any evidence?
        if evidence_referenced:
            if evidence_referenced in self.task.evidence:
                if evidence_referenced not in self.evidence_used:
                    self.evidence_used.add(evidence_referenced)
                    # Is it the *required* evidence?
                    if evidence_referenced in self.task.required_evidence:
                        reward += 0.3 # Strong partial reward
                    else:
                        reward += 0.1 # Minor reward for using valid evidence
            else:
                # Hallucinated evidence
                reward -= 0.1
                
        # Length/substance check
        if len(argument.split()) > 10:
            reward += 0.05
            
        return round(reward, 2)

    def evaluate_final(self, history: List[str]) -> float:
        """
        Evaluate the entire episode to give a final score [0, 1].
        """
        # Base score from determinism
        score = 0.0
        
        # Were all required pieces of evidence used?
        evidence_found = sum(1 for req in self.task.required_evidence if req in self.evidence_used)
        score += (evidence_found / len(self.task.required_evidence)) * 0.5
        
        # If client available, get LLM assessment of the dialogue on remaining 0.5 points
        if self.client:
            try:
                system_prompt = """You are a highly logical courtroom judge evaluating a lawyer's argument.
Evaluate the following dialogue history of a case. 
Provide a score between 0.0 and 1.0 based on the logical consistency and persuasiveness of the lawyer (the agent).
Respond ONLY with a single float number between 0.0 and 1.0."""
                history_text = r"\n".join(history)
                user_prompt = f"Case Facts: {self.task.case_facts}\n\nHistory:\n{history_text}\n\nScore (0.0 to 1.0):"
                
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                    max_tokens=10
                )
                result_text = completion.choices[0].message.content.strip()
                try:
                    llm_score = float(result_text)
                    # Add proportional LLM score (max +0.5)
                    score += (min(max(llm_score, 0.0), 1.0) * 0.5)
                except ValueError:
                    pass
            except Exception as e:
                print(f"[DEBUG] Grader LLM failed: {e}")
        else:
            # Fallback if no LLM: full points if they used all required evidence
            score += 0.5 if evidence_found == len(self.task.required_evidence) else 0.0
            
        return min(max(round(score, 2), 0.0), 1.0)
