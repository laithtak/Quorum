"""Code review pack — security, style, and architecture reviewers."""

PACK_NAME = "code_review"
PACK_DESCRIPTION = "Multi-perspective code review panel."

DEFAULT_SETTINGS = {"rounds": 1, "synthesis": "ranked"}

COUNSELOR_DEFS = [
    {
        "name": "Security",
        "persona": (
            "You review code for security vulnerabilities, injection risks, "
            "auth flaws, and data exposure."
        ),
    },
    {
        "name": "Style",
        "persona": (
            "You review code for readability, naming, structure, "
            "and adherence to best practices."
        ),
    },
    {
        "name": "Architecture",
        "persona": (
            "You review code for design patterns, scalability, "
            "coupling, and maintainability."
        ),
    },
]
