"""Core module for Minghe Companion."""

from src.core.config import Settings, get_settings, settings
from src.core.constants import (
    AgeGroup,
    RiskLevel,
    IntentType,
    InterventionType,
    CRISIS_KEYWORDS,
    PROFESSIONAL_HOTLINES,
    AGE_GROUP_DESCRIPTIONS,
    DEFAULT_AGENT_CONFIG,
)
from src.core.prompt import (
    PSYCHOLOGY_MASTER_SYSTEM_PROMPT,
    CRISIS_RESPONSE_PROMPT,
    EMPATHY_RESPONSE_PROMPT,
    RAG_PROMPT_TEMPLATE,
    get_age_specific_prompt,
    build_agent_prompt,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "settings",
    # Constants
    "AgeGroup",
    "RiskLevel",
    "IntentType",
    "InterventionType",
    "CRISIS_KEYWORDS",
    "PROFESSIONAL_HOTLINES",
    "AGE_GROUP_DESCRIPTIONS",
    "DEFAULT_AGENT_CONFIG",
    # Prompt
    "PSYCHOLOGY_MASTER_SYSTEM_PROMPT",
    "CRISIS_RESPONSE_PROMPT",
    "EMPATHY_RESPONSE_PROMPT",
    "RAG_PROMPT_TEMPLATE",
    "get_age_specific_prompt",
    "build_agent_prompt",
]
