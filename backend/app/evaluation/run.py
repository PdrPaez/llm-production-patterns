import json
from pathlib import Path

from ..schemas import PlaygroundRequest


async def run_evaluation(gateway):
    cases = json.loads((Path(__file__).parent / "dataset.json").read_text(encoding="utf-8")); results = []
    for case in cases:
        expected_provider = case.pop("expected_provider"); expected_category = case.pop("expected_category", None); result = await gateway.run(PlaygroundRequest(**case, enable_cache=False, enable_rate_limit=False)); passed = result.selected_provider == expected_provider and (not expected_category or result.structured_response.category == expected_category); results.append({"name": case["prompt"], "passed": passed, "selected_provider": result.selected_provider})
    return {"passed": all(x["passed"] for x in results), "total": len(results), "results": results}


if __name__ == "__main__":
    import asyncio

    from ..gateway import Gateway
    print(json.dumps(asyncio.run(run_evaluation(Gateway())), indent=2))
