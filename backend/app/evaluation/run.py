import asyncio
import json
from pathlib import Path

from ..gateway import Gateway
from ..schemas import PlaygroundRequest


async def run_evaluation(gateway: Gateway | None = None) -> dict:
    engine = gateway or Gateway()
    cases = json.loads((Path(__file__).parent / "dataset.json").read_text(encoding="utf-8"))
    results = []
    for case in cases:
        expected = {key: case.pop(key) for key in list(case) if key.startswith("expected_")}
        name = case.pop("name")
        if name == "cache-hit":
            first = await engine.run(PlaygroundRequest(**case, client_id=f"eval-{name}"))
            actual = await engine.run(PlaygroundRequest(**case, client_id=f"eval-{name}"))
            passed = not first.cache_hit and actual.cache_hit and actual.attempts == 0
        elif name == "rate-limit":
            actual = None
            for index in range(engine.settings.rate_limit_capacity + 1):
                rate_case = {**case, "client_id": f"eval-{name}", "prompt": f"{case['prompt']} {index}"}
                actual = await engine.run(PlaygroundRequest(**rate_case))
            passed = actual is not None and actual.rate_limit.get("allowed") is False
        else:
            actual = await engine.run(PlaygroundRequest(**case, client_id=f"eval-{name}"))
            passed = True
            if "expected_provider" in expected:
                passed &= actual.provider == expected["expected_provider"]
            if "expected_reason" in expected:
                passed &= actual.routing_reason == expected["expected_reason"]
            if "expected_category" in expected:
                passed &= actual.structured_response is not None and actual.structured_response.category == expected["expected_category"]
            if "expected_attempts" in expected:
                passed &= actual.attempts == expected["expected_attempts"]
            if "expected_retry_count" in expected:
                passed &= actual.retry_count == expected["expected_retry_count"]
            if "expected_fallback" in expected:
                passed &= actual.fallback_used is expected["expected_fallback"]
            if "expected_dropped_context" in expected:
                passed &= actual.token_budget.get("dropped_context_blocks") == expected["expected_dropped_context"]
            if "expected_allowed" in expected:
                passed &= actual.security.get("allowed") is expected["expected_allowed"] and actual.attempts == 0
            if "expected_span" in expected:
                passed &= any(span.name == expected["expected_span"] for span in actual.trace)
        results.append({"name": name, "passed": bool(passed)})
    return {"passed": all(item["passed"] for item in results), "total": len(results), "results": results}


if __name__ == "__main__":
    outcome = asyncio.run(run_evaluation())
    print(json.dumps(outcome, indent=2))
    raise SystemExit(0 if outcome["passed"] else 1)
