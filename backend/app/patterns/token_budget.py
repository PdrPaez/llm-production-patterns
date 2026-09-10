from dataclasses import dataclass


def estimate_tokens(text: str) -> int:
    return max(0, len(text) // 4)


@dataclass(frozen=True)
class BudgetResult:
    prompt: str
    retained_context: list[str]
    estimated_tokens: int
    reserved_output_tokens: int
    removed_context: list[str]


def apply_budget(system: str, prompt: str, context: list[str], max_context: int, reserved_output: int) -> BudgetResult:
    protected = estimate_tokens(system) + estimate_tokens(prompt)
    available = max_context - reserved_output - protected
    retained, removed, used = [], [], 0
    for block in context:
        cost = estimate_tokens(block)
        if used + cost <= max(0, available):
            retained.append(block); used += cost
        else:
            removed.append(block)
    total = protected + used
    if protected > max_context - reserved_output:
        raise ValueError("protected input exceeds token budget")
    return BudgetResult(prompt, retained, total, reserved_output, removed)
