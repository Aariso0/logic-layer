# logiclayer/cli/commands/query.py
import typer
from logiclayer.connectors.nvidia_connector import NvidiaConnector
from logiclayer.verifier.orchestrator import verify as run_verification
from logiclayer.verifier.ollama_client import OllamaClient
from logiclayer.reporting.formatter import format_report
from logiclayer.cli.prompt import SYSTEM_PROMPT

AGENT_REGISTRY = {
    "nvidia": NvidiaConnector,
}

app = typer.Typer()


@app.command()
def query(
    prompt: str = typer.Argument(..., help="The prompt to send to the agent"),
    agent: str = typer.Option(..., "--agent", help="Agent name e.g. nvidia")
):
    """
    Send a prompt to an agent and verify the response.
    logiclayer query "<prompt>" --agent <name>
    """
    # Step 1 — connector
    typer.echo(f"Sending prompt to {agent}...")

    if agent not in AGENT_REGISTRY:
        typer.echo(f"Unknown agent: '{agent}'. Available agents: {list(AGENT_REGISTRY.keys())}")
        raise typer.Exit(1)

    connector = AGENT_REGISTRY[agent]()

    try:
        raw_response = connector.send(prompt)

        if raw_response is None:
            typer.echo("Error: Connector returned no response.")
            raise typer.Exit(code=1)

        if isinstance(raw_response, str) and not raw_response.strip():
            typer.echo("Error: Connector returned an empty response.")
            raise typer.Exit(code=1)

        typer.echo(f"\nRaw response received from {agent}.")

        typer.echo("Verifying claims in parallel...")
        verdicts = verify(raw_response, SYSTEM_PROMPT, OllamaClient())
    except RuntimeError as e:
        typer.echo(f"\nConnector error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"\nUnexpected error from connector: {e}")
        raise typer.Exit(1)

    # Step 2 — orchestrator
    typer.echo("Verifying claims in parallel...")
    verdicts = run_verification(raw_response, SYSTEM_PROMPT, OllamaClient())

    # Step 3 — formatter
    report = format_report(verdicts)
    typer.echo(report)