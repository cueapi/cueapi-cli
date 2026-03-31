"""Terminal output formatting helpers."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def echo_error(message: str, exit_code: int = 1) -> None:
    """Print an error message and exit with non-zero code."""
    import click
    click.echo(click.style(f"Error: {message}", fg="red"), err=True)
    if exit_code:
        raise SystemExit(exit_code)


def echo_success(message: str) -> None:
    """Print a success message."""
    import click
    click.echo(click.style(message, fg="green"))


def echo_warning(message: str) -> None:
    """Print a warning message."""
    import click
    click.echo(click.style(message, fg="yellow"))


def echo_info(label: str, value: str, label_width: int = 16) -> None:
    """Print a label: value pair."""
    import click
    click.echo(f"{label:<{label_width}} {value}")


def echo_json(data: Any, indent: int = 2) -> None:
    """Pretty-print JSON data."""
    import click
    click.echo(json.dumps(data, indent=indent))


def echo_table(headers: List[str], rows: List[List[str]], widths: Optional[List[int]] = None) -> None:
    """Print a simple table with headers and rows."""
    import click

    if widths is None:
        widths = []
        for i, h in enumerate(headers):
            col_max = len(h)
            for row in rows:
                if i < len(row):
                    col_max = max(col_max, len(str(row[i])))
            widths.append(min(col_max + 2, 40))

    # Header
    header_line = ""
    for i, h in enumerate(headers):
        header_line += f"{h:<{widths[i]}}"
    click.echo(click.style(header_line, bold=True))

    # Rows
    for row in rows:
        line = ""
        for i, cell in enumerate(row):
            if i < len(widths):
                line += f"{str(cell):<{widths[i]}}"
            else:
                line += str(cell)
        click.echo(line)


def format_status(status: str) -> str:
    """Format a status string with color."""
    colors = {
        "active": "green",
        "paused": "yellow",
        "completed": "cyan",
        "failed": "red",
        "success": "green",
        "pending": "yellow",
        "delivering": "yellow",
        "retrying": "yellow",
    }
    import click
    color = colors.get(status, "white")
    return click.style(status, fg=color)
