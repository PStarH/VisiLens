"""
VdWeb CLI Entry Point

Launches the VdWeb server and opens the web interface.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
import webbrowser
from pathlib import Path

import click
import uvicorn

from .server import create_app, set_initial_dataset_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.argument('filename', type=click.Path(exists=True), required=False)
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--no-browser', is_flag=True, help='Don\'t open browser automatically')
def main(filename: str | None, host: str, port: int, no_browser: bool):
    """
    VdWeb - Excel for Developers

    Launch a local web GUI for exploring data with VisiData.

    Examples:

        vdweb data.csv

        vdweb employees.parquet --port 9000

        vdweb dataset.json --no-browser
    """
    # Set initial dataset if provided
    if filename:
        file_path = Path(filename).resolve()
        if not file_path.exists():
            click.echo(f"Error: File not found: {filename}", err=True)
            sys.exit(1)

        set_initial_dataset_path(str(file_path))
        logger.info(f"Loading dataset: {file_path}")

    # Create the FastAPI app
    app = create_app()

    # Open browser after a short delay (in background thread)
    if not no_browser:
        def open_browser():
            time.sleep(1.5)  # Wait for server to start
            url = f"http://{host}:{port}"
            logger.info(f"Opening browser: {url}")
            webbrowser.open(url)

        threading.Thread(target=open_browser, daemon=True).start()

    # Display startup message
    click.echo("=" * 60)
    click.echo("VdWeb - Excel for Developers")
    click.echo("=" * 60)
    if filename:
        click.echo(f"Dataset: {filename}")
    else:
        click.echo("No dataset loaded. Use the web interface to load one.")
    click.echo(f"Server: http://{host}:{port}")
    click.echo("\nPress Ctrl+C to stop")
    click.echo("=" * 60)

    # Run the server
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=False  # Reduce noise
        )
    except KeyboardInterrupt:
        click.echo("\n\nShutting down VdWeb. Goodbye!")
        sys.exit(0)


if __name__ == '__main__':
    main()
