"""This is a sample mock program to check if the orchestrator is working normally"""

import asyncio
from logiclayer.verifier.orchestrator import OrchestrationEngine

class MockAgentConnector:
    async def get_latest_response(self, session_id: str) -> str:
        return "The sky is green. Water is dry."
    async def request_corrected_response(self, session_id: str, feedback: str) -> str:
        print(f" Kunal's Agent received feedback: [{feedback}]")
        return "The sky is blue. Water is wet."
    async def extract_claims(self, text: str) -> list:
        if "green" in text:
            return ["The sky is green", "Water is wet"]
        return ["The sky is blue", "Water is wet"]

async def main():
    engine = OrchestrationEngine(agent_connector=MockAgentConnector())
    result = await engine.process_response_stream(session_id="session_999")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
