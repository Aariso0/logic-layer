# logiclayer/cli/commands/kb.py
"""
Knowledge base CLI commands.
logiclayer kb add-fact --file <fact.json>
logiclayer kb refresh
"""

import json
import sqlite3
import typer
from pathlib import Path
from logiclayer.knowledge_base.schema import Fact
from logiclayer.knowledge_base.loader import load_data, load_sources, DB_PATH
from logiclayer.scheduler.jobs import refresh_knowledge_base

app = typer.Typer()


@app.command("add-fact")
def add_fact(
    file: str = typer.Option(..., "--file", help="Path to fact JSON file")
):
    """
    Add a new fact to the knowledge base.
    logiclayer kb add-fact --file <fact.json>
    """
    fact_path = Path(file)

    # Step 1 — check file exists and is JSON
    if not fact_path.exists():
        typer.echo(f"File not found: {file}")
        raise typer.Exit(1)

    if fact_path.suffix != ".json":
        typer.echo("File must be a .json file.")
        raise typer.Exit(1)

    # Step 2 — load and validate against Pydantic schema
    with open(fact_path) as f:
        raw = json.load(f)

    try:
        fact = Fact(**raw)
    except Exception as e:
        typer.echo(f"Invalid fact schema: {e}")
        raise typer.Exit(1)

    # Step 3 — check source_id exists (orphan check)
    with sqlite3.connect(DB_PATH) as conn:
        source_ids = load_sources(conn)

        if fact.source_id not in source_ids:
            typer.echo(
                f"Orphan fact — source_id '{fact.source_id}' "
                f"does not exist in sources."
            )
            raise typer.Exit(code=1)

    # Step 4 — save to local-knowledge-base/facts/
    output_path = Path("local-knowledge-base/facts") / fact_path.name
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(fact.model_dump(), f, indent=2)

    conn.close()
    typer.echo(f"Fact '{fact.fact_id}' saved to {output_path}")


@app.command("refresh")
def refresh():
    """
    Refresh the knowledge base — re-validates stale facts.
    logiclayer kb refresh
    """
    typer.echo("Refreshing knowledge base...")
    refresh_knowledge_base()
    typer.echo("Knowledge base refresh complete.")