import { describe, expect, it } from 'vitest';
import { mapExecution } from './mapExecution';
import type { ExecutionResult } from '../types';

const result = (overrides: Partial<ExecutionResult> = {}): ExecutionResult => ({
  attempted_providers: ['mock_fast'], attempts: 1, retry_count: 0, fallback_used: false, cache_hit: false,
  security: { allowed: true }, rate_limit: { allowed: true }, token_budget: {}, trace_id: 'trace', latency_ms: 1,
  execution: {}, trace: [{ name: 'request', status: 'succeeded', started_at_ms: 0, duration_ms: 1, metadata: {} }], ...overrides,
});

describe('mapExecution', () => {
  it('maps backend spans to node states without routing decisions', () => {
    const graph = mapExecution(result({ routing_reason: 'high_complexity', selected_provider: 'mock_quality' }));
    expect(graph.nodes.find((node) => node.id === 'request')?.data.status).toBe('succeeded');
    expect(graph.nodes.find((node) => node.id === 'routing')?.data.status).toBe('idle');
  });

  it('keeps downstream nodes skipped after a security block', () => {
    const graph = mapExecution(result({ security: { allowed: false } }));
    expect(graph.nodes.find((node) => node.id === 'provider_call')?.data.status).toBe('skipped');
  });

  it('replay limits visible completed spans', () => {
    const graph = mapExecution(result({ trace: [{ name: 'request', status: 'succeeded', started_at_ms: 0, duration_ms: 1, metadata: {} }, { name: 'security', status: 'succeeded', started_at_ms: 1, duration_ms: 1, metadata: {} }] }), 0);
    expect(graph.nodes.find((node) => node.id === 'security')?.data.status).toBe('idle');
  });
});
