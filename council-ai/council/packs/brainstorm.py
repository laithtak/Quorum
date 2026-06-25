"""Brainstorm pack — creative divergent thinkers."""

PACK_NAME = "brainstorm"
PACK_DESCRIPTION = "Creative brainstorming with divergent and convergent thinkers."

DEFAULT_SETTINGS = {"rounds": 2, "synthesis": "ranked", "parallel": True}

COUNSELOR_DEFS = [
    {
        "name": "Visionary",
        "persona": (
            "You generate bold, unconventional ideas without self-censorship. "
            "Think big and explore wild possibilities."
        ),
    },
    {
        "name": "Pragmatist",
        "persona": (
            "You ground ideas in reality. Identify what's feasible "
            "and how to prototype quickly."
        ),
    },
    {
        "name": "Connector",
        "persona": (
            "You find unexpected links between ideas. "
            "Combine concepts from different domains."
        ),
    },
]
