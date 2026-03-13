"""Domain exceptions for the Möbius-Shear framework."""

from __future__ import annotations


class MobiusMachineError(Exception):
    """Base exception for all domain-level failures."""


class CrashError(MobiusMachineError):
    """Execution crashed due to undefined transition or invalid arithmetic."""


class SelectorError(CrashError):
    """Arithmetic selector could not determine a unique valid transition."""
