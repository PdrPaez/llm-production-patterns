"""Ordered provider fallback; only transport availability failures belong here."""

from collections.abc import Iterable


def ordered_plan(primary: str, fallback: str | None, configured: Iterable[str]) -> list[str]:
    """Return a de-duplicated primary/fallback plan without hiding the transition."""
    configured_ids = set(configured)
    if primary not in configured_ids:
        raise ValueError(f"unknown primary provider: {primary}")
    plan = [primary]
    if fallback and fallback != primary:
        if fallback not in configured_ids:
            raise ValueError(f"unknown fallback provider: {fallback}")
        plan.append(fallback)
    return plan
