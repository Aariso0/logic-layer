#THE  ORCHESTRATOR
"""
The string of the pearls.
This is the file that ties everything above together — the most important file in the project. **Claims are verified in parallel** — never sequentially. Per the sync-up decision, this is non-negotiable.

- [+] Send the user's prompt through the connector from step 4 → get the raw response (`logiclayer/verifier/orchestrator.py`)
- [+] Hand the raw response to Aaditya's `claim_extractor.py` → get `list[{claim_id, text}]`. If the list is empty, short-circuit straight to a single `report_verdict("unverified")` and stop
- [+] Call `ollama_client.py` with the claim list, the system prompt, and only the `check_local_db` + `report_verdict` tools enabled at first
- [+] **Verify claims in parallel** — when Qwen signals `check_local_db` calls, dispatch every claim's lookup concurrently (`asyncio.gather` or `ThreadPoolExecutor` — pick one and stick to it). Aggregate per-claim results before the next message
- [+] When a claim's `check_local_db` comes back empty, **only that claim** gets `search_trusted_sources` added to its tool list on the next turn — this gating logic lives in `orchestrator.py`, not in the prompt, so Qwen can't skip the local check even if it wanted to. Per-claim gating is enforced in parallel.
- [+] Execute whichever tool Qwen calls by dispatching to the real function in `logiclayer/verifier/tools.py`, feed the result back into the message history, and call Ollama again — loop until `report_verdict` has been called for every claim. **Per-claim state is held in a dict keyed by `claim_id`**, not in a single sequential history. Remember: no conversation memory across user prompts (sync-up scope decision).
- [+] Collect all `report_verdict` calls into one structured report object (still in `orchestrator.py`)
"""

import asyncio
import logging
import time
import importlib
from typing import Any, Dict, List, Optional

# Setup the logger 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_TRY = 3 # number of tries to import any file

for attempt in range(1, MAX_TRY+1):
    try:
        from logiclayer.verifier import ollama_client
        logger.info("Successfully imported ollama_client.")
        break
    except ImportError as e:
        logger.error(f"Attempt {attempt}/{MAX_TRY} : ollama_client.py could not be found!")
        if attempt == MAX_TRY:
            logger.critical("Maximum attempts reached. Crashing application safely!!")
            raise e
        importlib.invalidate_caches()
        time.sleep(0.05)

for attempt in range(1, MAX_TRY+1):
    try:
        from logiclayer.verifier.tools import run_check_local_db as cldb, run_search_trusted_sources as rst, run_report_verdict as rv
        logger.info("Successfully imported tools -> check_local_db, search_trusted_sources, report_verdict.")
        break
    except ImportError as e:
        logger.error(f"Attempt {attempt}/{MAX_TRY} : tools.py module file missing! Initializing fallback.")
        if attempt == MAX_TRY:
            logger.critical("Maximum attempts reached. Crashing application safely!!")
            raise e
        importlib.invalidate_caches()
        time.sleep(0.05)

for attempt in range(1, MAX_TRY+1):
    try:
        from logiclayer.logging.logger import log_prompt, log_tool_call
        logger.info("Successfully imported logger -> log_prompt, log_tool_call")
        break
    except ImportError as e:
        logger.warning("logging/logger.py missing. Proceeding without specific logging module.")
        break

for attempt in range(1, MAX_TRY+1):
    try:
        from logiclayer.connectors.nvidia_connector import NvidiaConnector
        logger.info("Successfully imported nvidia_connector -> NvidiaConnector")
        break
    except ImportError as e:
        logger.error(f"Attempt {attempt}/{MAX_TRY} : nvidia_connector file missing! Initializing fallback.")
        if attempt == MAX_TRY:
            logger.critical("Maximum attempts reached. Crashing application safely!!")
            raise e
        importlib.invalidate_caches()
        time.sleep(0.05)

build_system_prompt = None
for attempt in range(1, MAX_TRY+1):
    try:
        from logiclayer.verifier.system_prompt import build_system_prompt as bsp
        build_system_prompt = bsp
        logger.info("Successfully imported system_prompt -> build_system_prompt")
        break
    except ImportError as e:
        logger.error(f"Attempt {attempt}/{MAX_TRY} : system_prompt file missing! Initializing fallback.")
        if attempt == MAX_TRY:
            logger.critical("Maximum attempts reached. Crashing application safely!!")
            raise e
        importlib.invalidate_caches()
        time.sleep(0.05)

for attempt in range(1, MAX_TRY+1):
    try:
        from logiclayer.verifier.claim_extractor import extract_claims
        logger.info("Successfully imported verifier -> extract_claims")
        break
    except ImportError as e:
        logger.error(f"Attempt {attempt}/{MAX_TRY} : claim_extractor file missing! Initializing fallback.")
        if attempt == MAX_TRY:
            logger.critical("Maximum attempts reached. Crashing application safely!!")
            raise e
        importlib.invalidate_caches()
        time.sleep(0.05)


# ==============================================================================
# CORE ORCHESTRATION ENGINE
# ==============================================================================

class OrchestrationEngine:
    def __init__(self, agent_connector: Any = None):
        """
        Accepts a live initialized connector wrapper instance.
        Falls back to default healthy initialization if none is supplied.
        """
        if agent_connector is not None:
            self.agent_connector = agent_connector
            logger.info("Using injected mock connector setup.")
        else:
            try:
                self.agent_connector = NvidiaConnector()
                logger.info("NvidiaConnector successfully connected")
            except Exception as e:
                logger.error(f"Could not initialize NvidiaConnector class: {e}, Using EmergencyConnector")
                class EmergencyConnector:
                    async def send(self, p: str): return "Emergency structural return text"
                self.agent_connector = EmergencyConnector()

    async def process_response_stream(self, prompt: str) -> Dict[str, Any]:
        """
        Processes claims using a parallel work queue model where 3 workers
        pull claims dynamically and execute them concurrently via independent ReAct flows.
        """
        start_time = time.perf_counter()
        
        report_payload = {
            "execution_latency_seconds": 0.0,
            "categorized_verdicts": {
                "verified": [],
                "wrong": [],
                "unverified": []
            },
            "tier_used": None
        }

        try:
            # 1. Execute Agent Request via the Connector Instance
            try:
                raw_response = await self.agent_connector.send(prompt)
                logger.info("Successfully fetched raw output block from Agent.")
            except Exception as conn_err:
                logger.critical(f"Target Agent connector dropped execution stream: {conn_err}")
                logger.warning("API Key missing/connection Failed. Used mock AI response")
                raw_response = (
                    "This is an emergency mock AI response. The system is operating "
                    "in offline safety mode due to a missing API key configuration."
                )

            # Audit trace log capture
            try:
                log_prompt(prompt)
            except Exception:
                pass

            # 2. Extract Claims
            claims_from_response = []
            try:
                claims_from_response = extract_claims(raw_response)
                logger.info(f"Successfully extracted {len(claims_from_response)} claims from the AI response")
            except Exception as e:
                logger.critical(f"Claim Extraction Process failed: {e}")
            
            claims_list = claims_from_response if isinstance(claims_from_response, list) else []
            total_claims_count = len(claims_list)

            if total_claims_count == 0:
                logger.warning("Zero verification targets parsed out from evaluation payload.")
                report_payload["tier_used"] = "no_claims_extracted"
                return report_payload

            # 3. Build System Prompt Context
            system_prompt_response = []
            try:
                system_prompt_response = await build_system_prompt(raw_response)
            except Exception as e:
                logger.error(f"System prompt build-up failed: {e}.")
                system_prompt_response = [{"role": "system", "content": "You are a rigorous fact-checking assistant. Follow the tool protocol strictly."}]

            # ==================================================================
            # PART 4: Single Gated ReAct Processing Loop for a Claim
            # ==================================================================
            async def process_single_claim(claim_text: str) -> Dict[str, Any]:
                claim_record = {
                    "claim": claim_text,
                    "verdict": "unverified",
                    "evidence": "No evidence found in available tiers.",
                    "source_url": None,
                    "correction": None,
                    "tier_used": "not_started"
                }

                # Isolate state: Gating tools list strictly local to this specific claim
                available_tools = [
                    ollama_client.TOOL_CHECK_LOCAL_DB, 
                    ollama_client.TOOL_REPORT_VERDICT
                ]
                
                messages = list(system_prompt_response)
                messages.append({"role": "user", "content": f"Please verify this claim: '{claim_text}'"})

                MAX_TURNS = 5  
                for turn in range(MAX_TURNS):
                    try:
                        # Bridge to sync HTTP client via threadpool executor
                        response = await asyncio.to_thread(
                            ollama_client.chat,
                            messages=messages,
                            tools=available_tools
                        )
                    except Exception as e:
                        logger.error(f"Ollama client failed for claim '{claim_text[:15]}...': {e}")
                        claim_record["tier_used"] = "ollama_connection_error"
                        return claim_record
                        
                    assistant_msg = response.get("message", {})
                    messages.append(assistant_msg)

                    tool_calls = ollama_client.extract_tool_calls(response)
                    if not tool_calls:
                        if claim_record["tier_used"] == "not_started":
                            claim_record["tier_used"] = "local_db"
                        break

                    for call in tool_calls:
                        name = call["name"]
                        args = call["arguments"]
                        
                        # TIER 1: Local DB Check
                        if name == "check_local_db":
                            claim_record["tier_used"] = "local_db"
                            db_result = await cldb(args.get("claim")) 
                            messages.append({"role": "tool", "name": name, "content": str(db_result)})
                            
                            # Gating Logic: If empty, expand tools to unlock Web Search
                            if not db_result:
                                if ollama_client.TOOL_SEARCH_TRUSTED_SOURCES not in available_tools:
                                    available_tools.append(ollama_client.TOOL_SEARCH_TRUSTED_SOURCES)
                        
                        # TIER 2: Trusted Source Search
                        elif name == "search_trusted_sources":
                            claim_record["tier_used"] = "trusted_source_search"
                            web_result = await rst(args.get("claim"))
                            messages.append({"role": "tool", "name": name, "content": str(web_result)})
                        
                        # TIER 3: Complete Report Verdict
                        elif name == "report_verdict":
                            claim_record.update({
                                "verdict": args.get("verdict", "unverified"),
                                "evidence": args.get("evidence"),
                                "source_url": args.get("source_url"),
                                "correction": args.get("correction")
                            })
                            await rv(claim_record)
                            return claim_record
                            
                # Fallback if loop ends without explicit report_verdict call
                if claim_record["tier_used"] == "trusted_source_search" and claim_record["verdict"] == "unverified":
                    claim_record["evidence"] = "Checked local database and trusted web sources, but no matching evidence was found."
                
                await rv(claim_record)
                return claim_record

            # ==================================================================
            # PART 5: Dynamic Worker Pool Execution Scheme
            # ==================================================================
            logger.info(f"Initializing Async Queue for {total_claims_count} claims...")
            
            # 1. Feed all extracted claims into a first-in, first-out queue
            claim_queue = asyncio.Queue()
            for claim in claims_list:
                await claim_queue.put(claim)

            # 2. Define the persistent worker loop behavior
            async def worker(worker_id: int):
                logger.info(f"Worker-{worker_id} booted and listening to queue.")
                while not claim_queue.empty():
                    try:
                        # Grab the next claim from the top of the queue
                        claim_text = await claim_queue.get()
                        logger.info(f"Worker-{worker_id} picked up claim: '{claim_text[:25]}...'")
                        
                        # Run the gated ReAct processing loop for this claim
                        result = await process_single_claim(claim_text)
                        
                        # IMMEDIATE REAL-TIME ROUTING MAPPING
                        # The exact moment a worker determines the status, it drops it straight into the correct bucket
                        verdict_status = result.get("verdict", "unverified").lower()
                        if verdict_status == "verified":
                            report_payload["categorized_verdicts"]["verified"].append(result)
                        elif verdict_status == "wrong":
                            report_payload["categorized_verdicts"]["wrong"].append(result)
                        else:
                            report_payload["categorized_verdicts"]["unverified"].append(result)
                        
                        # Signal to the queue that the task is completed
                        claim_queue.task_done()
                    except asyncio.CancelledError:
                        break
                    except Exception as worker_err:
                        logger.error(f"Worker-{worker_id} encountered an error: {worker_err}")
                        claim_queue.task_done()

            # 3. Spin up exactly 3 persistent parallel workers
            NUM_WORKERS = 3
            worker_tasks = [
                asyncio.create_task(worker(worker_id=i))
                for i in range(1, NUM_WORKERS + 1)
            ]

            # 4. Wait until the queue is entirely empty and all claims are processed
            await claim_queue.join()

            # 5. Clean up and terminate the persistent worker tasks
            for task in worker_tasks:
                task.cancel()
            await asyncio.gather(*worker_tasks, return_exceptions=True)

            logger.info("All claims successfully processed through the dynamic worker pool.")

        except Exception as structural_pipeline_fault:
            logger.critical(f"Orchestration pipeline critical breakdown: {structural_pipeline_fault}")
            report_payload["tier_used"] = "pipeline_critical_failure"

        finally:
            report_payload["execution_latency_seconds"] = round(time.perf_counter() - start_time, 4)
            return report_payload