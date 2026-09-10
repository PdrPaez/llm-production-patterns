from typing import Any, Literal

from pydantic import BaseModel, Field

FailureMode = Literal["none", "transient_once", "exhaust_primary", "unavailable"]


class ProviderRequest(BaseModel):
    system_instructions: str = ""
    user_content: str
    retained_messages: list[str] = Field(default_factory=list)
    retained_context_blocks: list[str] = Field(default_factory=list)
    structured_output: bool = False
    output_schema: str | None = None
    max_output_tokens: int = 256
    temperature: float = 0
    failure_mode: FailureMode = "none"
    simulate_invalid_output: bool = False
    request_id: str = ""
    correction: bool = False
    failure_attempts: int = 0


class ProviderResponse(BaseModel):
    text: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float


class SupportTicketAnalysis(BaseModel):
    category: Literal["billing", "technical", "account", "other"]
    priority: Literal["low", "medium", "high"]
    summary: str
    requires_human: bool


class PlaygroundRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)
    complexity: Literal["simple", "medium", "high"] = "simple"
    structured_output: bool = False
    failure_mode: FailureMode = "none"
    simulate_invalid_output: bool = False
    enable_cache: bool = True
    enable_rate_limit: bool = True
    enable_security_check: bool = True
    requested_operation: str = "generate"
    max_context_tokens: int = 1024
    reserved_output_tokens: int = 256
    temperature: float = 0
    context_blocks: list[str] = Field(default_factory=list)
    routing_mode: Literal["automatic", "fixed"] = "automatic"
    provider: str | None = None
    fallback_provider: str | None = None
    client_id: str = "playground"


class TraceSpan(BaseModel):
    name: str
    status: str
    started_at_ms: float
    duration_ms: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlaygroundResponse(BaseModel):
    response: str | None = None
    structured_response: SupportTicketAnalysis | None = None
    selected_provider: str | None = None
    provider: str | None = None
    routing_reason: str | None = None
    attempted_providers: list[str] = Field(default_factory=list)
    attempts: int = 0
    retry_count: int = 0
    fallback_used: bool = False
    cache_hit: bool = False
    security: dict[str, Any] = Field(default_factory=dict)
    rate_limit: dict[str, Any] = Field(default_factory=dict)
    token_budget: dict[str, Any] = Field(default_factory=dict)
    trace_id: str
    latency_ms: float = 0
    execution: dict[str, Any] = Field(default_factory=dict)
    trace: list[TraceSpan] = Field(default_factory=list)
