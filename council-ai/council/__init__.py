"""Council AI — multi-model deliberation framework."""

from .counselor import Counselor
from .memory import ConversationMemory
from .middleware import Middleware, MiddlewareStack
from .models import TurnRecord
from .orchestrator import Orchestrator, SynthesisStrategy, DeliberationResult
from .config import load_config, build_from_dict, build_quick, build_middleware_stack
from .packs import load_pack, list_packs, PACK_REGISTRY
from .providers.base import ProviderConfig, Message, CompletionResult
from .providers import create_provider, available_providers
from .synthesis import (
    SynthesisEngine,
    SingleSynthesizer,
    VotingSynthesizer,
    ConsensusChecker,
    RankedSynthesizer,
    build_synthesis_engine,
    SYNTHESIS_PROMPT,
)
from .usage import TokenUsage, CounselorUsage, calculate_cost, COST_TABLE

__version__ = "1.0.0"

__all__ = [
    "Counselor",
    "Orchestrator",
    "SynthesisStrategy",
    "DeliberationResult",
    "TurnRecord",
    "ConversationMemory",
    "Middleware",
    "MiddlewareStack",
    "ProviderConfig",
    "Message",
    "CompletionResult",
    "TokenUsage",
    "CounselorUsage",
    "calculate_cost",
    "COST_TABLE",
    "create_provider",
    "available_providers",
    "load_config",
    "build_from_dict",
    "build_quick",
    "build_middleware_stack",
    "load_pack",
    "list_packs",
    "PACK_REGISTRY",
    "SynthesisEngine",
    "SingleSynthesizer",
    "VotingSynthesizer",
    "ConsensusChecker",
    "RankedSynthesizer",
    "build_synthesis_engine",
    "SYNTHESIS_PROMPT",
]
