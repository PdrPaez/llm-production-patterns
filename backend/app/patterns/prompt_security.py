import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityResult:
    allowed: bool
    risk: str
    findings: list[str]


SUSPICIOUS = [(r"ignore\s+(all\s+)?previous instructions", "instruction_override"), (r"reveal|show|print.*system prompt", "system_prompt_extraction"), (r"developer message|jailbreak", "privileged_instruction_probe")]


def inspect_prompt(prompt: str, operation: str) -> SecurityResult:
    findings = [label for pattern, label in SUSPICIOUS if re.search(pattern, prompt, re.I)]
    if operation not in {"generate", "classify", "summarize"}:
        findings.append("operation_not_allowlisted")
    risk = "high" if findings else "low"
    return SecurityResult(not findings, risk, findings)
