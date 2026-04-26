"""Core Nexus Agent exceptions."""

from __future__ import annotations


class NexusAgentError(Exception):
    """Base exception for Nexus Agent."""


class BudgetExceededError(NexusAgentError):
    """Raised when a purchase exceeds the configured budget."""


class PolicyViolationError(NexusAgentError):
    """Raised when a purchase fails policy evaluation."""


class WalletError(NexusAgentError):
    """Raised for wallet and signing backend failures."""
