# logiclayer/cli/commands/scheduler.py
"""
Scheduler CLI command — starts APScheduler with cron trigger.
"""

import logging
import typer
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from logiclayer.scheduler.jobs import refresh_knowledge_base

logger = logging.getLogger(__name__)
app = typer.Typer()

@app.command("start")
def start(
    hour: int = typer.Option(2, "--hour", help="Hour to run refresh (24hr). Default 2am."),
    minute: int = typer.Option(0, "--minute", help="Minute to run refresh. Default 0.")
):
    """
    Start the APScheduler refresh job.
    logiclayer scheduler start
    """
    scheduler = BlockingScheduler()

    scheduler.add_job(
        refresh_knowledge_base,
        trigger=CronTrigger(hour=hour, minute=minute),
        id="refresh_knowledge_base",
        name="Knowledge Base Refresh",
        replace_existing=True,
    )

    typer.echo(f"Scheduler started — refresh runs daily at {hour:02d}:{minute:02d}.")
    typer.echo("Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        typer.echo("\nScheduler stopped.")
        scheduler.shutdown()