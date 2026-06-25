"""Shared data models for council deliberation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TurnRecord:
    """Record of a single counselor's turn in the deliberation."""

    counselor_name: str
    model: str
    round: int
    content: str
