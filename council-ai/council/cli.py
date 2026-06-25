"""CLI — interactive council session from the terminal."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .config import build_quick, load_config
from .memory import ConversationMemory
from .models import TurnRecord
from .usage import CounselorUsage

load_dotenv()

app = typer.Typer(
    name="council",
    help="🏛️  Quorum — multi-model deliberation before every response.",
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


def _print_usage(usage_list: list[CounselorUsage], total_cost: float) -> None:
    if not usage_list:
        return
    table = Table(title="Token Usage", show_header=True)
    table.add_column("Counselor")
    table.add_column("Model")
    table.add_column("Prompt", justify="right")
    table.add_column("Completion", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Cost (USD)", justify="right")
    for cu in usage_list:
        table.add_row(
            cu.counselor_name,
            cu.model,
            str(cu.usage.prompt_tokens),
            str(cu.usage.completion_tokens),
            str(cu.usage.total_tokens),
            f"${cu.usage.estimated_cost_usd:.4f}",
        )
    table.add_row("", "", "", "", "[bold]Total[/]", f"[bold]${total_cost:.4f}[/]")
    console.print(table)


async def _run_session(
    orchestrator,
    query: str,
    show_deliberation: bool,
    show_usage: bool,
) -> None:
    if show_deliberation:
        console.print(
            f"\n[dim]Deliberating with {len(orchestrator.counselors)} counselors "
            f"over {orchestrator.rounds} round(s)...[/dim]\n"
        )
        async for item in orchestrator.deliberate_stream(query):
            if isinstance(item, TurnRecord):
                _print_turn(item)
            else:
                _print_final(item)
        if show_usage:
            usage_list, total_cost = orchestrator._aggregate_usage()
            _print_usage(usage_list, total_cost)
    else:
        with console.status("[bold blue]Council is deliberating..."):
            result = await orchestrator.deliberate(query)
        _print_final(result.final_response)
        if show_usage:
            _print_usage(result.usage, result.total_cost_usd)


def _build_orchestrator(
    config: Path | None,
    models: str | None,
    provider: str,
    rounds: int,
    pack: str | None,
    memory: ConversationMemory | None = None,
):
    if config:
        orch = load_config(config)
    elif models or pack:
        model_list = [m.strip() for m in models.split(",")] if models else ["gpt-4o"]
        orch = build_quick(model_list, provider=provider, rounds=rounds, pack=pack)
    else:
        console.print("[red]Provide --config, --models, or --pack[/red]")
        raise typer.Exit(1)

    if memory is not None:
        orch.memory = memory
    return orch


@app.command("ask")
def ask(
    query: str = typer.Argument(..., help="The question or prompt for the council."),
    config: Path = typer.Option(None, "--config", "-c", help="Path to config file (JSON/YAML)."),
    models: str = typer.Option(
        None, "--models", "-m",
        help="Comma-separated model names for quick setup.",
    ),
    provider: str = typer.Option("openai", "--provider", "-p", help="Provider for --models."),
    rounds: int = typer.Option(2, "--rounds", "-r", help="Number of deliberation rounds."),
    show: bool = typer.Option(True, "--show/--quiet", help="Show deliberation or only final answer."),
    pack: str = typer.Option(None, "--pack", help="Persona pack name (e.g. debate)."),
    no_usage: bool = typer.Option(False, "--no-usage", help="Suppress usage table."),
) -> None:
    """Ask the council a question."""
    orchestrator = _build_orchestrator(config, models, provider, rounds, pack)
    asyncio.run(_run_session(orchestrator, query, show, show_usage=not no_usage))


@app.command("chat")
def chat(
    config: Path = typer.Option(None, "--config", "-c", help="Path to config file (JSON/YAML)."),
    models: str = typer.Option(
        None, "--models", "-m",
        help="Comma-separated model names for quick setup.",
    ),
    provider: str = typer.Option("openai", "--provider", "-p", help="Provider for --models."),
    rounds: int = typer.Option(2, "--rounds", "-r", help="Number of deliberation rounds."),
    show: bool = typer.Option(True, "--show/--quiet", help="Show deliberation or only final answer."),
    pack: str = typer.Option(None, "--pack", help="Persona pack name (e.g. debate)."),
    no_usage: bool = typer.Option(False, "--no-usage", help="Suppress usage table."),
) -> None:
    """Start an interactive council chat session with conversation memory."""
    memory = ConversationMemory()
    orchestrator = _build_orchestrator(
        config, models, provider, rounds, pack, memory=memory
    )

    console.print(Panel(
        "[bold]🏛️  Council AI[/bold]\n"
        f"Counselors: {', '.join(c.label for c in orchestrator.counselors)}\n"
        f"Rounds: {orchestrator.rounds}\n"
        f"Memory: enabled\n"
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

        asyncio.run(_run_session(orchestrator, query, show, show_usage=not no_usage))


@app.command("providers")
def providers_cmd() -> None:
    """List available providers (based on installed SDKs)."""
    from .providers import available_providers
    available = available_providers()
    if available:
        for p in available:
            console.print(f"  [green]✓[/] {p}")
    else:
        console.print("[yellow]No provider SDKs found. Install at least one:[/]")
        console.print("  pip install openai anthropic google-genai")


@app.command("packs")
def packs_cmd() -> None:
    """List available persona packs."""
    from .packs import list_packs
    for pack in list_packs():
        console.print(f"  [cyan]{pack['name']}[/] — {pack['description']}")


if __name__ == "__main__":
    app()
