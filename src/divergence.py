"""Divergence detection — ℵ-condition monitoring.

Detects when a computation is likely divergent:
- Partial quotients (shear parameters) exceeding threshold
- Stack depth growing monotonically for too long
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DivergencePolicy:
    """Policy for detecting divergent computations."""
    partial_quotient_threshold: int = 1_000_000
    depth_growth_window: int = 1024


class DivergenceMonitor:
    """Tracks divergence signals during execution."""

    def __init__(self, policy: DivergencePolicy | None = None):
        self.policy = policy or DivergencePolicy()
        self._strict_growth_count = 0
        self._previous_depth = 0
        self.diverged = False
        self.reason: str | None = None

    def check_step(self, shear_k: int, left_depth: int, right_depth: int) -> bool:
        """Check one step for divergence signals. Returns True if diverged."""
        if self.diverged:
            return True

        current_depth = left_depth + right_depth

        # Check partial quotient threshold
        if abs(shear_k) > self.policy.partial_quotient_threshold:
            self.diverged = True
            self.reason = f"partial quotient |k|={abs(shear_k)} exceeds threshold {self.policy.partial_quotient_threshold}"
            return True

        # Check monotonic depth growth
        if current_depth > self._previous_depth:
            self._strict_growth_count += 1
        else:
            self._strict_growth_count = 0
        self._previous_depth = current_depth

        if self._strict_growth_count >= self.policy.depth_growth_window:
            self.diverged = True
            self.reason = f"stack depth grew monotonically for {self._strict_growth_count} steps"
            return True

        return False
