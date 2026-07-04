import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from logiclayer.verifier.orchestrator import OrchestrationEngine

@pytest.fixture
def mock_connector():
    """Provides an isolated mock for the external agent connector stream."""
    connector = MagicMock()
    connector.send = AsyncMock(return_value={"text": "Isolated Mock Trace Stream Output"})
    return connector

@pytest.fixture
def engine(mock_connector):
    """Provides a cleanly generated OrchestrationEngine instance with injected dependency."""
    return OrchestrationEngine(agent_connector=mock_connector)


# ==============================================================================
# FAULT-TOLERANT TEST EXECUTION SUITE
# ==============================================================================

@pytest.mark.asyncio
@patch('logiclayer.verifier.orchestrator.extract_claims')
@patch('logiclayer.verifier.orchestrator.build_system_prompt', new_callable=AsyncMock)
@patch('logiclayer.verifier.orchestrator.ollama_client.chat')
@patch('logiclayer.verifier.orchestrator.ollama_client.extract_tool_calls')
@patch('logiclayer.verifier.orchestrator.cldb', new_callable=AsyncMock)
@patch('logiclayer.verifier.orchestrator.rst', new_callable=AsyncMock)
@patch('logiclayer.verifier.orchestrator.rv', new_callable=AsyncMock)
async def test_worker_pool_routes_to_correct_buckets_immediately(
    mock_rv, mock_rst, mock_cldb, mock_extract_tool_calls, mock_chat, mock_sys_prompt, mock_extract_claims, engine
):
    """
    Tests that multiple claims are processed in parallel by the worker pool
    and are instantly appended to their correct verified/wrong/unverified buckets
    regardless of completion order or worker execution interleaving.
    """
    # 1. Provide the list of target test claims
    mock_extract_claims.return_value = [
        "Claim One: Local Hit", 
        "Claim Two: Web Hit", 
        "Claim Three: Unverified Fallback"
    ]
    mock_sys_prompt.return_value = [{"role": "system", "content": "Test context"}]
    
    # 2. DYNAMIC WORKER MOCK: Route mock tool calls based on the message conversation content.
    # This prevents parallel workers from stealing each other's linear side-effects!
    def smart_extract_tool_calls(response):
        messages = response.get("messages", [])
        if not messages:
            return []
            
        # Inspect the last user message to know which claim this worker is tracking
        last_user_content = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        
        # Build turn counts by checking how many assistant entries exist for this claim context
        assistant_turns = sum(1 for m in messages if m.get("role") == "assistant")
        
        if "Claim One" in last_user_content:
            if assistant_turns == 0:
                return [{"name": "check_local_db", "arguments": {"claim": "Claim One: Local Hit"}}]
            elif assistant_turns == 1:
                return [{"name": "report_verdict", "arguments": {"verdict": "verified", "evidence": "DB Match"}}]
                
        elif "Claim Two" in last_user_content:
            if assistant_turns == 0:
                return [{"name": "check_local_db", "arguments": {"claim": "Claim Two: Web Hit"}}]
            elif assistant_turns == 1:
                return [{"name": "search_trusted_sources", "arguments": {"claim": "Claim Two: Web Hit"}}]
            elif assistant_turns == 2:
                return [{"name": "report_verdict", "arguments": {"verdict": "wrong", "evidence": "Web Contradiction"}}]
                
        elif "Claim Three" in last_user_content:
            if assistant_turns == 0:
                return [{"name": "check_local_db", "arguments": {"claim": "Claim Three: Unverified Fallback"}}]
            elif assistant_turns == 1:
                return [{"name": "search_trusted_sources", "arguments": {"claim": "Claim Three: Unverified Fallback"}}]
            elif assistant_turns == 2:
                return [] # Empty tool list triggers fallback unverified status logic cleanly
                
        return []

    mock_extract_tool_calls.side_effect = smart_extract_tool_calls
    
    # Simulate chat returning the running message payload back to the extract tool
    mock_chat.side_effect = lambda messages, tools: {"message": {"role": "assistant"}, "messages": messages}
    
    mock_cldb.side_effect = lambda claim: {"verdict": "verified", "evidence": "DB Match"} if "One" in claim else {}
    mock_rst.return_value = {"verdict": "wrong", "evidence": "Web Contradiction"}

    # 3. Run execution pipeline
    result = await engine.process_response_stream("Execute Test")
    
    # 4. Assert by searching for records dynamically
    verified_claims = [r["claim"] for r in result["categorized_verdicts"]["verified"]]
    wrong_claims = [r["claim"] for r in result["categorized_verdicts"]["wrong"]]
    unverified_claims = [r["claim"] for r in result["categorized_verdicts"]["unverified"]]

    assert "Claim One: Local Hit" in verified_claims
    assert "Claim Two: Web Hit" in wrong_claims
    assert "Claim Three: Unverified Fallback" in unverified_claims
    
    assert mock_rv.call_count == 3


@pytest.mark.asyncio
@patch('logiclayer.verifier.orchestrator.extract_claims')
@patch('logiclayer.verifier.orchestrator.build_system_prompt', new_callable=AsyncMock)
@patch('logiclayer.verifier.orchestrator.ollama_client.chat')
async def test_ollama_crash_safely_routes_to_unverified_bucket(
    mock_chat, mock_sys_prompt, mock_extract_claims, engine
):
    """Tests that a dropped client connection defaults safely to the unverified bucket."""
    mock_extract_claims.return_value = ["Crashed Server Claim"]
    mock_sys_prompt.return_value = [{"role": "system", "content": "Context"}]
    mock_chat.side_effect = Exception("Ollama connection timed out or refused.")
    
    result = await engine.process_response_stream("Execute Test")
    
    assert len(result["categorized_verdicts"]["unverified"]) == 1
    record = result["categorized_verdicts"]["unverified"][0]
    assert record["tier_used"] == "ollama_connection_error"
    assert record["verdict"] == "unverified"


@pytest.mark.asyncio
@patch('logiclayer.verifier.orchestrator.extract_claims')
async def test_no_claims_extracted(mock_extract_claims, engine):
    """Tests zero extracted claims paths short-circuit without crashing."""
    mock_extract_claims.return_value = []
    
    result = await engine.process_response_stream("Execute Test")
    
    assert result["tier_used"] == "no_claims_extracted"
    assert len(result["categorized_verdicts"]["verified"]) == 0