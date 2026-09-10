import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityResult:
    allowed: bool
    risk: str
    findings: list[str]

    def as_dict(self) -> dict:
        return {"allowed": self.allowed, "risk_level": self.risk, "reasons": self.findings, "flagged_patterns": self.findings}


SUSPICIOUS = [(r"ignore\s+(all\s+)?previous instructions", "instruction_override"), (r"reveal|show|print.*system prompt", "system_prompt_extraction"), (r"developer message|jailbreak", "privileged_instruction_probe")]


def inspect_prompt(prompt: str, operation: str) -> SecurityResult:
    findings = [label for pattern, label in SUSPICIOUS if re.search(pattern, prompt, re.I)]
    medium = bool(re.search(r"impersonate\s+(the\s+)?(system|developer)|bypass\s+(safety|security)", prompt, re.I))
    if operation not in {"generate", "classify", "summarize"}:
        findings.append("operation_not_allowlisted")
    risk = "high" if findings else "medium" if medium else "low"
    return SecurityResult(not findings or risk == "medium", risk, findings or (["suspicious_language"] if medium else []))
