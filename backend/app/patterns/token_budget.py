from dataclasses import dataclass


class TokenBudgetExceededError(ValueError):
    """Protected input cannot fit without dropping trusted instructions."""


def estimate_tokens(text: str) -> int:
    """Documented approximation: characters divided by four, never exact provider usage."""
    return max(0, len(text) // 4)


@dataclass(frozen=True)
class BudgetResult:
    prompt: str
    retained_context: list[str]
    estimated_tokens: int
    reserved_output_tokens: int
    removed_context: list[str]
    system_tokens: int
    message_tokens: int
    context_tokens: int

    def as_dict(self, maximum_context_tokens: int) -> dict:
        return {"system_tokens": self.system_tokens, "message_tokens": self.message_tokens, "context_tokens": self.context_tokens, "reserved_output_tokens": self.reserved_output_tokens, "maximum_context_tokens": maximum_context_tokens, "truncated_messages": 0, "dropped_context_blocks": len(self.removed_context), "estimated_tokens": self.estimated_tokens, "retained_context": self.retained_context, "removed_context": self.removed_context}


def apply_budget(system: str, prompt: str, context: list[str], max_context: int, reserved_output: int) -> BudgetResult:
    system_tokens = estimate_tokens(system)
    message_tokens = estimate_tokens(prompt)
    protected = system_tokens + message_tokens
    if protected > max_context - reserved_output:
        raise TokenBudgetExceededError("protected input exceeds token budget")
    available = max_context - reserved_output - protected
    retained, removed, used = [], [], 0
    for block in context:
        cost = estimate_tokens(block)
        if used + cost <= available:
            retained.append(block)
            used += cost
        else:
            removed.append(block)
    return BudgetResult(prompt, retained, protected + used, reserved_output, removed, system_tokens, message_tokens, used)
