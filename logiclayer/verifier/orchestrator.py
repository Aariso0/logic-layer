#The ORCHESTRATOR 
"""
The string of the pearls.
This is the file that actually ties everything above together — it's the most important file in the project.

- [ ] Send the user's prompt through the connector from step 4 → get the raw response (`logiclayer/verifier/orchestrator.py`)
- [ ] Call `ollama_client.py` with the raw response, the system prompt, and only the `check_local_db` + `report_verdict` tools enabled at first
- [ ] When a `check_local_db` tool call comes back empty for a claim, **only then** add `search_trusted_sources` to the tools list for the next turn — this gating logic lives in `orchestrator.py`, not in the prompt, so Qwen can't skip the local check even if it wanted to
- [ ] Execute whichever tool Qwen calls by dispatching to the real function in `logiclayer/verifier/tools.py`, feed the result back into the message history, and call Ollama again — loop until `report_verdict` has been called for every claim
- [ ] Collect all `report_verdict` calls into one structured report object (still in `orchestrator.py`)
"""

import asyncio
import logging
import time
import importlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

# Setup the logger 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


MAX_TRY = 3 #number of tries to import any file

for attempt in range(1, MAX_TRY+1):
    try:
        from logiclayer.verifier import ollama_client
        logger.info("Successfully imported call_ollama.")
        break
     
    except ImportError as e:
        logger.error(f"Attempt {attempt}/{MAX_TRY} : ollama_client.py could not be found!")
        if attempt == MAX_TRY:
            logger.critical("Maximum attempts reached. Crashing application safely!!")
            raise e

        importlib.invalidate_caches()
        time.sleep(0.05)
        
# Expose functions explicitly at module scope to permit clean execution & mocking access
check_local_db = None
search_trusted_sources = None
report_verdict = None

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
        # Integration with the logger module created
        from logiclayer.logging.logger import log_prompt, log_tool_call
        logger.info("Successfully imported logger -> log_prompt, log_tool_call")
        break

    except ImportError as e:
        logger.warning("logging/logger.py missing.")
        if attempt == MAX_TRY:
            logger.critical("Maximum attempts reached. Crashing application safely!!")
            raise e

        importlib.invalidate_caches()
        time.sleep(0.05)

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

# Setup a direct reference for patching and orchestration fallback calls
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
        from logiclayer.reporting import formatter
        logger.info("Successfully imported reporting -> formatter")
        break

    except ImportError as e:
        logger.error(f"Attempt {attempt}/{MAX_TRY} : formatter file missing! Initializing fallback.")
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
        Processes real inputs concurrently via a batch-metered async loop.
        Guarded against schema changes and third-party script crashes.
        """
        start_time = time.perf_counter()
        
        report_payload = {
            "execution_latency_seconds": 0.0,
            "verdicts": [],
            "tier_used": None
        }

        try:
            # 1. Execute Agent Request via the Connector Instance
            try:
                raw_response = await self.agent_connector.send(prompt)
                logger.info("Successfully fetched raw output block from Agent.")

            except Exception as conn_err:
                logger.critical(f"Target Agent connector dropped execution stream: {conn_err}")
                #------Fallback mock
                logger.warning("API Key missing/ connection Failed. Used mock AI response")
                raw_response = (
                    "This is an emergeny mock AI response. The system is operating"
                    "in offline safety mode due to a missing API key configuration"
                )

            # Audit trace log capture
            try:
                log_prompt(prompt)
            except Exception:
                pass

            # 2.A build the prompt given to the ollama client by system
            system_prompt_response = []
            try:
                system_prompt_response = await build_system_prompt(raw_response)
            except Exception as e:
                logger.error(f"System prompt build-up failed: {e}.")
                system_prompt_response = ["Emergency return text"]

            # 2.B send the prompt to ollama_client and get the response in return
            # 3. Clean up and normalize incoming data structural layouts
            claims_list = []
            if isinstance(system_prompt_response, str):
                claims_list = [
                    line.strip("- *1234567890. ").strip()
                    for line in system_prompt_response.split("\n")
                    if line.strip() and len(line.strip()) > 5
                ]
            elif isinstance(system_prompt_response, dict):
                claims_list = system_prompt_response.get("claims", [])
            elif isinstance(system_prompt_response, list):
                claims_list = system_prompt_response

            total_claims_count = len(claims_list)

            if total_claims_count == 0:
                logger.warning("Zero verification targets parsed out from evaluation payload.")
                report_payload["tier_used"] = "no_claims_extracted"
                return report_payload

            # 4. Set Up Safe Metered Concurrency Grid for Async I/O Boundaries
            BATCH_SIZE = 30
            MAX_CONCURRENT_PER_BATCH = 10
            IO_TIMEOUT_SECONDS = 1.0
            concurrency_gate = asyncio.Semaphore(MAX_CONCURRENT_PER_BATCH)

            async def process_single_claim(claim_text: str, gate: asyncio.Semaphore) -> Dict[str, Any]:
                claim_record = {
                    "claim": claim_text,
                    "verdict": "unverified",
                    "evidence": None,
                    "source_url": None,
                    "correction": None,
                    "tier_used": "not_started"
                }

                async with gate:
                    # --- TIER 1: LOCAL DB GATING CHECK ---
                    try:
                        async with asyncio.timeout(IO_TIMEOUT_SECONDS):
                            db_results = await check_local_db(claim_text)
                        
                        if db_results and isinstance(db_results, dict) and db_results.get("verdict"):
                            claim_record.update({
                                "verdict": db_results.get("verdict", "verified"),
                                "evidence": db_results.get("evidence", "Match found in local database cache."),
                                "source_url": db_results.get("source_url", "local_db://cache"),
                                "correction": db_results.get("correction"),
                                "tier_used": "local_db"
                            })
                            await report_verdict(claim_record)
                            return claim_record
                    except (TimeoutError, asyncio.TimeoutError):
                        logger.warning(f"Local DB timeout for claim: {claim_text[:20]}...")
                        claim_record["tier_used"] = "timeout_failure"
                        await report_verdict(claim_record)
                        return claim_record 
                    except Exception as db_err:
                        logger.error(f"Local DB module script error handled cleanly: {db_err}")

                    # --- TIER 2: WEB SCRAMBLE FALLBACK ---
                    try:
                        async with asyncio.timeout(IO_TIMEOUT_SECONDS):
                            web_results = await search_trusted_sources(claim_text)
                        
                        if web_results and isinstance(web_results, dict) and web_results.get("verdict"):
                            claim_record.update({
                                "verdict": web_results.get("verdict", "verified"),
                                "evidence": web_results.get("evidence", "Verified via query search."),
                                "source_url": web_results.get("source_url"),
                                "correction": web_results.get("correction"),
                                "tier_used": "trusted_source_search"
                            })
                            await report_verdict(claim_record)
                            return claim_record
                    except (TimeoutError, asyncio.TimeoutError):
                        logger.warning(f"Web source timeout for claim: {claim_text[:20]}...")
                        claim_record["tier_used"] = "timeout_failure"
                    except Exception as web_err:
                        logger.error(f"Trusted sources module script error handled cleanly: {web_err}")
                        claim_record["tier_used"] = "external_script_crash"

                    # Live reporting fallback execution synchronization
                    try:
                        await report_verdict(claim_record)
                    except Exception as report_err:
                        logger.error(f"Reporting utility failed: {report_err}")

                    return claim_record

            # 5. Distribute Tasks Across Micro-Batches
            for i in range(0, total_claims_count, BATCH_SIZE):
                current_batch_chunk = claims_list[i : i + BATCH_SIZE]
                batch_tasks = [
                    process_single_claim(text, concurrency_gate)
                    for text in current_batch_chunk
                ]
                batch_results = await asyncio.gather(*batch_tasks)
                report_payload["verdicts"].extend(batch_results)

        except Exception as structural_pipeline_fault:
            logger.critical(f"Orchestration pipeline critical breakdown: {structural_pipeline_fault}")
            report_payload["tier_used"] = "pipeline_critical_failure"

        finally:
            report_payload["execution_latency_seconds"] = round(time.perf_counter() - start_time, 4)
            return report_payload