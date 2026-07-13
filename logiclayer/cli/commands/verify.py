# logiclayer/cli/commands/verify.py
"""
Verify CLI command.
logiclayer verify <file.json>
Skips the connector — feeds a saved transcript straight into the orchestrator.
"""

import json
import typer
from pathlib import Path
from logiclayer.verifier.orchestrator import verify as run_verification
from logiclayer.verifier.ollama_client import OllamaClient
from logiclayer.reporting.formatter import format_report
from logiclayer.cli.prompt import SYSTEM_PROMPT

app = typer.Typer()


@app.command()
def verify(
    file: str = typer.Argument(..., help="Path to saved transcript JSON file")
):
    """
    Verify a saved transcript without calling the connector.
    logiclayer verify <file.json>
    """
    transcript_path = Path(file)

    # Step 1 — check file exists
    if not transcript_path.exists():
        typer.echo(f"File not found: {file}")
        raise typer.Exit(1)

    if transcript_path.suffix != ".json":
        typer.echo("File must be a .json file.")
        raise typer.Exit(1)

    # Step 2 — load transcript
    try:
        with open(transcript_path) as f:
            transcript = json.load(f)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON file.")
        typer.echo(f"Reason: {e}")
        raise typer.Exit(code=1)
    except OSError as e:
        typer.echo(f"Error: Unable to read file.")
        typer.echo(f"Reason: {e}")
        raise typer.Exit(code=1)

    # Step 3 — extract raw response from transcript
    raw_response = transcript.get("raw_response")

    if not raw_response:
        typer.echo("Transcript missing 'raw_response' field.")
        raise typer.Exit(1)

    typer.echo(f"Loaded transcript: {file}")
    typer.echo("Verifying claims in parallel...")

    # Step 4 — feed straight into orchestrator (skip connector)
    verdicts = run_verification(raw_response, SYSTEM_PROMPT, OllamaClient())

    # Step 5 — format and print report
    report = format_report(verdicts)
    typer.echo(report)