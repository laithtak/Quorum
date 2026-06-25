"""Council AI — multi-model deliberation framework."""

from .counselor import Counselor
from .orchestrator import Orchestrator, SynthesisStrategy, DeliberationResult, TurnRecord
from .config import load_config, build_from_dict, build_quick
from .providers.base import ProviderConfig, Message
from .providers import create_provider, available_providers

__version__ = "0.1.0"

__all__ = [
    "Counselor",
    "Orchestrator",
    "SynthesisStrategy",
    "DeliberationResult",
    "TurnRecord",
    "ProviderConfig",
    "Message",
    "create_provider",
    "available_providers",
    "load_config",
    "build_from_dict",
    "build_quick",
]
