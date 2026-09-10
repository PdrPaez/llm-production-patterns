import type { Edge, Node } from '@xyflow/react';
import type { ExecutionResult, FlowGraph, FlowNodeData } from '../types';
const stages = ['request', 'rate_limit', 'security', 'routing', 'token_budget', 'cache_lookup', 'provider_call', 'retry', 'fallback', 'validation', 'correction', 'completion'];
const labels: Record<string, string> = { request: 'Request', rate_limit: 'Rate Limit', security: 'Prompt Security', routing: 'Model Router', token_budget: 'Token Budget', cache_lookup: 'Response Cache', provider_call: 'LLM Provider', retry: 'Retry Controller', fallback: 'Fallback', validation: 'Structured Validation', correction: 'Correction', completion: 'Response' };
export function mapExecution(result?: ExecutionResult, replayIndex = Number.POSITIVE_INFINITY): FlowGraph {
  const spans = result?.trace ?? []; const completed = new Map(spans.slice(0, replayIndex + 1).map((span) => [span.name, span]));
  const nodes: Node<FlowNodeData>[] = stages.map((stage, index) => { const span = completed.get(stage); const status = span?.status ?? (result && result.security.allowed === false && index > 2 ? 'skipped' : 'idle'); const info = stage === 'routing' ? result?.routing_reason : stage === 'provider_call' ? result?.provider : stage === 'cache_lookup' ? (result?.cache_hit ? 'HIT' : 'MISS') : undefined; return { id: stage, type: 'stage', position: { x: (index % 4) * 230, y: Math.floor(index / 4) * 150 }, data: { label: labels[stage], status, info } }; });
  const edges: Edge[] = stages.slice(0, -1).map((stage, index) => ({ id: `e-${stage}`, source: stage, target: stages[index + 1], label: completed.get(stages[index + 1])?.status === 'cache_hit' ? 'hit' : undefined, animated: Boolean(completed.get(stages[index + 1])) })); return { nodes, edges };
}
