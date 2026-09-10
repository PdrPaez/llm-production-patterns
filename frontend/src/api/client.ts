import type { ExecutionResult } from '../flow/types';

export type PatternDescription = { id: string; title: string; problem: string; pattern: string; implementation: string; trade_offs: string; production_considerations: string };
export type ProviderDescriptor = { id: string; label: string; tier: string; type: string; available: boolean };

const API = 'http://127.0.0.1:8000';

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`);
  if (!response.ok) throw new Error(`GET ${path} failed with ${response.status}`);
  return response.json() as Promise<T>;
}

export function getPatterns(): Promise<PatternDescription[]> { return getJson('/api/patterns'); }
export function getProviders(): Promise<ProviderDescriptor[]> { return getJson('/api/providers'); }
export function getHealth(): Promise<{ status: string }> { return getJson('/health'); }
export async function runPlayground(payload: object): Promise<ExecutionResult> {
  const response = await fetch(`${API}/api/playground/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail ?? `Playground failed with ${response.status}`);
  if (body.rate_limit && body.rate_limit.allowed === false) throw new Error(`Rate limit exceeded. Retry in ${body.rate_limit.retry_after ?? 1}s.`);
  return body as ExecutionResult;
}
export function runEvaluation(): Promise<Record<string, unknown>> {
  return fetch(`${API}/api/evaluation/run`, { method: 'POST' }).then(async (response) => {
    if (!response.ok) throw new Error(`Evaluation failed with ${response.status}`);
    return response.json() as Promise<Record<string, unknown>>;
  });
}
