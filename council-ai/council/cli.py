"""CLI — interactive council session from the terminal."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from .config import build_quick, load_config
from .orchestrator import TurnRecord

app = typer.Typer(
    name="council",
    help="🏛️  Council AI — multi-model deliberation before every response.",
    add_completion=False,
)
console = Console()


def _print_turn(turn: TurnRecord) -> None:
    colors = ["cyan", "magenta", "green", "yellow", "blue", "red"]
    color = colors[hash(turn.counselor_name) % len(colors)]
    header = f"Round {turn.round} · {turn.counselor_name} · {turn.model}"
    console.print(Panel(
        Markdown(turn.content),
        title=f"[bold {color}]{header}[/]",
        border_style=color,
        padding=(0, 1),
    ))


def _print_final(response: str) -> None:
    console.print()
    console.print(Panel(
        Markdown(response),
        title="[bold white on blue] 🏛️  Council Response [/]",
        border_style="blue",
        padding=(1, 2),
    ))
    console.print()


async def _run_session(orchestrator, query: str, show_deliberation: bool) -> None:
    if show_deliberation:
        console.print(f"\n[dim]Deliberating with {len(orchestrator.counselors)} counselors "
                       f"over {orchestrator.rounds} round(s)...[/dim]\n")
        async for item in orchestrator.deliberate_stream(query):
            if isinstance(item, TurnRecord):
                _print_turn(item)
            else:
                _print_final(item)
    else:
        with console.status("[bold blue]Council is deliberating..."):
            result = await orchestrator.deliberate(query)
        _print_final(result.final_response)


@app.command("ask")
def ask(
    query: str = typer.Argument(..., help="The question or prompt for the council."),
    config: Path = typer.Option(None, "--config", "-c", help="Path to config file (JSON/YAML)."),
    models: str = typer.Option(None, "--models", "-m",
        help="Comma-separated model names for quick setup (e.g. gpt-4o,claude-sonnet-4-6)."),
    provider: str = typer.Option("openai", "--provider", "-p",
        help="Provider for --models shortcut."),
    rounds: int = typer.Option(2, "--rounds", "-r", help="Number of deliberation rounds."),
    show: bool = typer.Option(True, "--show/--quiet", help="Show deliberation or only final answer."),
) -> None:
    """Ask the council a question."""
    if config:
        orchestrator = load_config(config)
    elif models:
        model_list = [m.strip() for m in models.split(",")]
        orchestrator = build_quick(model_list, provider=provider, rounds=rounds)
    else:
        console.print("[red]Provide either --config or --models[/red]")
        raise typer.Exit(1)

    asyncio.run(_run_session(orchestrator, query, show))


@app.command("chat")
def chat(
    config: Path = typer.Option(None, "--config", "-c", help="Path to config file (JSON/YAML)."),
    models: str = typer.Option(None, "--models", "-m",
        help="Comma-separated model names for quick setup."),
    provider: str = typer.Option("openai", "--provider", "-p",
        help="Provider for --models shortcut."),
    rounds: int = typer.Option(2, "--rounds", "-r", help="Number of deliberation rounds."),
    show: bool = typer.Option(True, "--show/--quiet", help="Show deliberation or only final answer."),
) -> None:
    """Start an interactive council chat session."""
    if config:
        orchestrator = load_config(config)
    elif models:
        model_list = [m.strip() for m in models.split(",")]
        orchestrator = build_quick(model_list, provider=provider, rounds=rounds)
    else:
        console.print("[red]Provide either --config or --models[/red]")
        raise typer.Exit(1)

    console.print(Panel(
        "[bold]🏛️  Council AI[/bold]\n"
        f"Counselors: {', '.join(c.label for c in orchestrator.counselors)}\n"
        f"Rounds: {orchestrator.rounds}\n"
        f"Type [bold green]quit[/] or [bold green]exit[/] to leave.",
        border_style="blue",
    ))

    while True:
        try:
            query = console.input("\n[bold green]You:[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break

        asyncio.run(_run_session(orchestrator, query, show))


@app.command("providers")
def providers() -> None:
    """List available providers (based on installed SDKs)."""
    from .providers import available_providers
    available = available_providers()
    if available:
        for p in available:
            console.print(f"  [green]✓[/] {p}")
    else:
        console.print("[yellow]No provider SDKs found. Install at least one:[/]")
        console.print("  pip install openai anthropic google-genai")


if __name__ == "__main__":
    app()
