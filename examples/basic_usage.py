"""Example: Using Council AI as a Python library."""

import asyncio
from council import (
    Counselor,
    Orchestrator,
    ProviderConfig,
    create_provider,
    build_quick,
)


async def example_quick():
    """Quickest way — all models on one provider."""
    orchestrator = build_quick(
        models=["gpt-4o-mini", "gpt-4o"],
        provider="openai",
        rounds=2,
    )
    result = await orchestrator.deliberate("What's the best way to learn a new programming language?")
    print(result.final_response)


async def example_mixed():
    """Mix providers — cloud + local models together."""
    counselors = [
        Counselor(
            name="Cloud",
            provider=create_provider(ProviderConfig(provider="openai", model="gpt-4o")),
            persona="You focus on industry best practices and mainstream solutions.",
        ),
        Counselor(
            name="Local",
            provider=create_provider(ProviderConfig(provider="ollama", model="llama3.1")),
            persona="You focus on privacy, open-source alternatives, and self-hosted solutions.",
        ),
    ]

    orchestrator = Orchestrator(counselors=counselors, rounds=2)
    result = await orchestrator.deliberate("How should a startup handle user data?")

    # Print the full deliberation transcript
    print(result.transcript)


async def example_streaming():
    """Stream the deliberation as it happens."""
    from council import TurnRecord

    orchestrator = build_quick(
        models=["llama3.1", "mistral"],
        provider="ollama",
        rounds=2,
    )

    async for item in orchestrator.deliberate_stream("Explain quantum computing simply."):
        if isinstance(item, TurnRecord):
            print(f"\n--- {item.counselor_name} (Round {item.round}) ---")
            print(item.content)
        else:
            print(f"\n{'='*50}")
            print(f"FINAL: {item}")


if __name__ == "__main__":
    asyncio.run(example_quick())
