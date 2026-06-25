"""Debate pack — adversarial pro/con deliberation."""

PACK_NAME = "debate"
PACK_DESCRIPTION = "Structured debate with advocate, critic, and moderator roles."

DEFAULT_SETTINGS = {"rounds": 2, "synthesis": "voting"}

COUNSELOR_DEFS = [
    {
        "name": "Advocate",
        "persona": (
            "You argue FOR the strongest position on the topic. "
            "Present compelling evidence and address counterarguments preemptively."
        ),
    },
    {
        "name": "Critic",
        "persona": (
            "You challenge the advocate's position. "
            "Find flaws, edge cases, and alternative viewpoints."
        ),
    },
    {
        "name": "Moderator",
        "persona": (
            "You synthesize both sides fairly. "
            "Identify where the advocate and critic agree and where they diverge."
        ),
    },
]
