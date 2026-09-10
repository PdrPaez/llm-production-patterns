import type { Edge, Node } from '@xyflow/react';
export type TraceSpan = { name: string; status: string; started_at_ms: number; duration_ms: number; metadata: Record<string, unknown> };
export type ExecutionResult = { response?: string | null; structured_response?: Record<string, unknown> | null; selected_provider?: string; provider?: string; routing_reason?: string; attempted_providers: string[]; attempts: number; retry_count: number; fallback_used: boolean; cache_hit: boolean; security: Record<string, unknown>; rate_limit: Record<string, unknown>; token_budget: Record<string, unknown>; trace_id: string; latency_ms: number; execution: Record<string, unknown>; trace: TraceSpan[] };
export type FlowNodeData = { label: string; status: string; info?: string };
export type FlowGraph = { nodes: Node<FlowNodeData>[]; edges: Edge[] };
