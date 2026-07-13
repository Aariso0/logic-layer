# logiclayer/cli/main.py
import typer
from logiclayer.cli.commands import query, verify, kb, scheduler

app = typer.Typer(
    name="logiclayer",
    help="Logic Layer — verify agent responses against trusted sources."
)

app.add_typer(query.app,     name="query")
app.add_typer(verify.app,    name="verify")
app.add_typer(kb.app,        name="kb")
app.add_typer(scheduler.app, name="scheduler")

if __name__ == "__main__":
    app()