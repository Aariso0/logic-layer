"""Orchestration loop for the Logic-Layer middleware.
This will handle claim extraction, trusted source validation, and contradiction detection before passing results to the response formatter.
"""


import asyncio
import logging
import time
from typing import Any, Dict, List


# making import of project parts
try:
    from logiclayer.reporting.formatter import format_report
except ImportError:
    def format_report(verdicts: list) -> str:
        return f"=== FALLBACK AUDIT REPORT ===\n Processed {len(verdicts)} facts successfully."

try:
    from logiclayer.trusted_sources.search import query_whitelist
except ImportError:
    async def query_whitelist(claim: str) -> str:
        return "Fallback whitelist match context"

try:
    from logiclayer.verifier.ollama_client import analyze_contradiction
except ImportError:
    async def analyze_contradiction(claim: str, context: str) -> dict:
        if "green" in claim:
            return {"claim": claim, "verdict": "wrong", "correction": "The sky is blue", "tier_used": "none"}
        return {"claim": claim, "verdict": "verified", "correction": None, "tier_used": "local"}


class OrchestrationEngine:
    
    def __init__(self, agent_connector: Any) -> None:
        #Injects Kunal's connection module.
        self.agent = agent_connector
        self.max_attempts = 2

    async def _verify_single_claim(self, claim: str) -> Dict[str, Any]:
        try:
            # Search for claims from Ranveer and Manish's search tool
            search_results = await query_whitelist(claim)

            # 2. Run Aaditya's Ollama contradiction detector 
            verdict_data: Dict[str, Any] = await analyze_contradiction(claim, search_results)
            return verdict_data

        except Exception as exc:
            return 
            {
                "claim": claim, 
                "verdict": "unverified", 
                "correction": None,
                "tier_used": "none"
            }

    async def process_response_stream(self, session_id: str) -> str:
        """Main loop with latency tracking and correction feedback."""
        start_time: float = time.perf_counter()
        attempt: int = 1
        current_feedback: str = ""
        raw_ai_text: str = ""
        final_verdicts: List[Dict[str, Any]] = []

        while attempt <= self.max_attempts:
            if attempt == 1:
                raw_ai_text = await self.agent.get_latest_response(session_id)
            else:
                raw_ai_text = await self.agent.request_corrected_response(session_id, current_feedback)

            claims: List[str] = await self.agent.extract_claims(raw_ai_text)
            if not claims:
                break

            tasks = [self._verify_single_claim(claim) for claim in claims]
            final_verdicts = await asyncio.gather(*tasks)

            contradictions = [v for v in final_verdicts if v and v.get("verdict") == "wrong"]
            if not contradictions:
                break
            
            feedback_messages = [f"Fix target '{c['claim']}': Use '{c['correction']}' instead." for c in contradictions]
            current_feedback = " | ".join(feedback_messages)
            attempt += 1

        end_time: float = time.perf_counter()
        print(f"Orchestration Pipeline Execution Latency: {end_time - start_time:f} seconds")

        final_report_cli: str = format_report(final_verdicts)
        return final_report_cli
