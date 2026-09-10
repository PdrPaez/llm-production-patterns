from dataclasses import dataclass

from ..config import get_settings


@dataclass(frozen=True)
class RoutingDecision:
    provider: str
    reason: str
    signals: dict


class ModelRouter:
    def choose(self, *, prompt: str, complexity: str, structured_output: bool) -> RoutingDecision:
        estimated = max(1, len(prompt) // 4)
        if structured_output:
            provider, reason = "mock_quality", "structured_output_required"
        elif complexity == "high":
            provider, reason = "mock_quality", "high_complexity"
        elif estimated >= get_settings().routing_quality_threshold_tokens:
            provider, reason = "mock_quality", "large_input"
        else:
            provider, reason = "mock_fast", "simple_request"
        return RoutingDecision(provider, reason, {"complexity": complexity, "structured_output": structured_output, "estimated_input_tokens": estimated})
