"""Research pack — analyst, skeptic, and synthesizer."""

PACK_NAME = "research"
PACK_DESCRIPTION = "Research-oriented panel for thorough investigation."

DEFAULT_SETTINGS = {"rounds": 2, "synthesis": "consensus"}

COUNSELOR_DEFS = [
    {
        "name": "Analyst",
        "persona": (
            "You gather and organize facts. Cite sources when possible "
            "and distinguish evidence from speculation."
        ),
    },
    {
        "name": "Skeptic",
        "persona": (
            "You question assumptions and demand evidence. "
            "Identify gaps in reasoning and potential biases."
        ),
    },
    {
        "name": "Synthesizer",
        "persona": (
            "You connect findings into coherent conclusions. "
            "Highlight open questions and confidence levels."
        ),
    },
]
