import json

from pydantic import ValidationError

from ..schemas import SupportTicketAnalysis


def parse_ticket(text: str) -> SupportTicketAnalysis:
    return SupportTicketAnalysis.model_validate(json.loads(text))


def validation_errors(error: ValidationError) -> list[str]:
    return [f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in error.errors()]
