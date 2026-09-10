import { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Background, Controls, Handle, MiniMap, Position, ReactFlow, type NodeProps } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './styles.css';
import './timeline.css';
import './patterns.css';
import { configureProvider, getPatterns, getProviders, runEvaluation, runPlayground, type PatternDescription, type ProviderDescriptor } from './api/client';
import { mapExecution } from './flow/execution/mapExecution';
import { presets } from './flow/templates';
import type { ExecutionResult, FlowNodeData } from './flow/types';

const labels: Record<string, string> = { request: 'Request', rate_limit: 'Rate Limit', security: 'Prompt Security', routing: 'Model Router', token_budget: 'Token Budget', cache_lookup: 'Response Cache', provider_call: 'LLM Provider', retry: 'Retry Controller', fallback: 'Fallback', validation: 'Structured Validation', correction: 'Correction', completion: 'Response' };
type Config = { prompt: string; complexity: 'simple' | 'medium' | 'high'; structured_output: boolean; failure_mode: 'none' | 'transient_once' | 'exhaust_primary' | 'unavailable'; simulate_invalid_output: boolean; enable_cache: boolean; enable_rate_limit: boolean; enable_security_check: boolean; routing_mode: 'automatic' | 'fixed'; provider?: string; fallback_provider?: string; client_id: string };
const initial: Config = { prompt: 'Summarize why bounded retries are useful.', complexity: 'simple', structured_output: false, failure_mode: 'none', simulate_invalid_output: false, enable_cache: true, enable_rate_limit: true, enable_security_check: true, routing_mode: 'automatic', client_id: 'local' };

function StageNode({ data }: NodeProps) {
  const node = data as FlowNodeData;
  const icon = node.status === 'succeeded' ? '✓' : node.status === 'blocked' ? '⛔' : node.status === 'skipped' ? '—' : '◈';
  return <div className={`node ${node.status}`}><Handle type="target" position={Position.Left} /><div className="node-title"><span aria-hidden="true">{icon}</span>{node.label}</div><div className="node-status">{node.status.replace('_', ' ')}</div>{node.info && <div className="node-info">{node.info}</div>}<Handle type="source" position={Position.Right} /></div>;
}

function ProviderSettings({ onConnected }: { onConnected: (providers: ProviderDescriptor[]) => void }) {
  const [form, setForm] = useState({ base_url: 'https://api.openai.com/v1', api_key: '', model: 'gpt-4o-mini', fast_model: '', quality_model: '' });
  const [status, setStatus] = useState('');
  const [saving, setSaving] = useState(false);
  const update = (part: Partial<typeof form>) => setForm((current) => ({ ...current, ...part }));
  const connect = async () => {
    setSaving(true); setStatus('');
    try {
      onConnected(await configureProvider(form));
      setForm((current) => ({ ...current, api_key: '' }));
      setStatus('Connected for this backend session.');
    } catch (reason) {
      setStatus(reason instanceof Error ? reason.message : 'Could not configure provider.');
    } finally { setSaving(false); }
  };
  return <details className="provider-settings"><summary>Configure real LLM provider</summary><p>Credentials stay in backend memory and are never returned to the browser.</p><label>Base URL<input value={form.base_url} onChange={(event) => update({ base_url: event.target.value })} placeholder="https://api.openai.com/v1" /></label><label>API key<input type="password" value={form.api_key} onChange={(event) => update({ api_key: event.target.value })} autoComplete="off" /></label><label>Default model<input value={form.model} onChange={(event) => update({ model: event.target.value })} /></label><div className="row"><label>Fast model<input value={form.fast_model} onChange={(event) => update({ fast_model: event.target.value })} placeholder="Optional" /></label><label>Quality model<input value={form.quality_model} onChange={(event) => update({ quality_model: event.target.value })} placeholder="Optional" /></label></div><button type="button" onClick={() => void connect()} disabled={saving || !form.api_key || !form.base_url || !form.model}>{saving ? 'Connecting…' : 'Connect provider'}</button>{status && <div className="provider-status" role="status">{status}</div>}</details>;
}

function App() {
  const [preset, setPreset] = useState('Full Production Pipeline');
  const [config, setConfig] = useState<Config>(initial);
  const [result, setResult] = useState<ExecutionResult>();
  const [selected, setSelected] = useState('routing');
  const [replayIndex, setReplayIndex] = useState(Number.POSITIVE_INFINITY);
  const [running, setRunning] = useState(false);
  const [evaluation, setEvaluation] = useState<Record<string, unknown>>();
  const [providers, setProviders] = useState<ProviderDescriptor[]>([]);
  const [patterns, setPatterns] = useState<PatternDescription[]>([]);
  const [error, setError] = useState('');

  useEffect(() => { void Promise.all([getProviders(), getPatterns()]).then(([available, descriptions]) => { setProviders(available); setPatterns(descriptions); }).catch((reason: Error) => setError(reason.message)); }, []);
  useEffect(() => { if (!result || !Number.isFinite(replayIndex) || replayIndex >= result.trace.length - 1) return; const timer = window.setTimeout(() => setReplayIndex((index) => index + 1), 500); return () => window.clearTimeout(timer); }, [result, replayIndex]);
  const graph = useMemo(() => mapExecution(result, replayIndex), [result, replayIndex]);
  const selectedSpan = result?.trace.find((span) => span.name === selected);
  const selectedPattern = patterns.find((item) => item.title === preset) ?? patterns.find((item) => item.id === 'model-routing');
  const update = (part: Partial<Config>) => setConfig((current) => ({ ...current, ...part }));
  const choose = (name: string) => { const item = presets.find((candidate) => candidate.name === name); setPreset(name); setResult(undefined); setEvaluation(undefined); setError(''); if (item) setConfig({ ...initial, ...(item.config as Partial<Config>) }); if (name === 'Evaluation') void runEvaluation().then(setEvaluation).catch((reason: Error) => setError(reason.message)); };
  const run = async () => { setRunning(true); setError(''); try { const effective = { ...config, enable_cache: config.failure_mode === 'none' ? config.enable_cache : false }; setResult(await runPlayground(effective)); setReplayIndex(Number.POSITIVE_INFINITY); } catch (reason) { setError(reason instanceof Error ? reason.message : 'Pipeline failed'); } finally { setRunning(false); } };

  return <div className="app"><header><div><div className="eyebrow">EXECUTION ARCHITECTURE LAB</div><h1>LLM Production Patterns</h1></div><div className="ready" aria-live="polite"><span /> System ready <small>offline mocks</small></div></header><div className="shell"><aside><h3>Flow Explorer</h3><button className="primary" onClick={() => choose('Full Production Pipeline')}>◆ Full Production Pipeline</button><div className="group"><small>RELIABILITY</small>{presets.slice(1, 5).map((item) => <button className={preset === item.name ? 'selected' : ''} onClick={() => choose(item.name)} key={item.id}>{item.name}</button>)}</div><div className="group"><small>SAFETY</small>{presets.slice(5, 9).map((item) => <button className={preset === item.name ? 'selected' : ''} onClick={() => choose(item.name)} key={item.id}>{item.name}</button>)}</div><div className="group"><small>OBSERVABILITY</small>{presets.slice(9).map((item) => <button className={preset === item.name ? 'selected' : ''} onClick={() => choose(item.name)} key={item.id}>{item.name}</button>)}</div></aside><main>{error && <div className="error" role="alert">{error}</div>}<section className="canvas-wrap"><div className="canvas-head"><div><span className="pill">LIVE TRACE</span><strong>{preset}</strong></div><button onClick={() => result && setReplayIndex(0)} disabled={!result}>Replay execution</button></div><div className="canvas" aria-label="Execution flow graph"><ReactFlow nodes={graph.nodes} edges={graph.edges} nodeTypes={{ stage: StageNode }} fitView onNodeClick={(_, node) => setSelected(node.id)}><Background color="#203047" gap={24} /><Controls /><MiniMap nodeColor={(node) => node.data?.status === 'succeeded' ? '#5eead4' : '#334155'} /></ReactFlow></div></section><section className="bottom"><div className="panel config"><h3>Configuration</h3><ProviderSettings onConnected={setProviders} /><label>Prompt<textarea value={config.prompt} onChange={(event) => update({ prompt: event.target.value })} /></label><div className="row"><label>Complexity<select value={config.complexity} onChange={(event) => update({ complexity: event.target.value as Config['complexity'] })}><option>simple</option><option>medium</option><option>high</option></select></label><label>Failure simulation<select value={config.failure_mode} onChange={(event) => update({ failure_mode: event.target.value as Config['failure_mode'] })}><option value="none">None</option><option value="transient_once">Transient once</option><option value="exhaust_primary">Exhaust primary</option><option value="unavailable">Unavailable</option></select></label></div><div className="row"><label>Routing<select value={config.routing_mode} onChange={(event) => update({ routing_mode: event.target.value as Config['routing_mode'] })}><option value="automatic">Automatic</option><option value="fixed">Fixed</option></select></label><label>Provider<select value={config.provider ?? ''} disabled={config.routing_mode !== 'fixed'} onChange={(event) => update({ provider: event.target.value || undefined })}><option value="">Auto</option>{providers.map((provider) => <option key={provider.id} value={provider.id} disabled={!provider.available}>{provider.label}{provider.available ? '' : ' (not configured)'}</option>)}</select></label></div><label>Fallback<select value={config.fallback_provider ?? ''} onChange={(event) => update({ fallback_provider: event.target.value || undefined })}><option value="">Automatic opposite tier</option>{providers.filter((provider) => provider.tier !== 'failure').map((provider) => <option key={provider.id} value={provider.id} disabled={!provider.available}>{provider.label}</option>)}</select></label><div className="checks"><label><input type="checkbox" checked={config.structured_output} onChange={(event) => update({ structured_output: event.target.checked })} /> Structured output</label><label><input type="checkbox" checked={config.simulate_invalid_output} onChange={(event) => update({ simulate_invalid_output: event.target.checked })} /> Invalid first output</label><label><input type="checkbox" checked={config.enable_cache} onChange={(event) => update({ enable_cache: event.target.checked })} /> Cache</label><label><input type="checkbox" checked={config.enable_security_check} onChange={(event) => update({ enable_security_check: event.target.checked })} /> Security</label></div><button className="run" onClick={() => void run()} disabled={running}>{running ? 'Running…' : 'Run pipeline ↗'}</button></div><div className="panel inspector"><div className="tabs"><b>Inspector</b><span>Trace</span><span>Output</span></div>{selectedPattern && <details className="pattern-doc" open><summary>{selectedPattern.title} documentation</summary><p><b>Problem:</b> {selectedPattern.problem}</p><p><b>Pattern:</b> {selectedPattern.pattern}</p><p><b>Implementation:</b> {selectedPattern.implementation}</p><p><b>Trade-offs:</b> {selectedPattern.trade_offs}</p></details>}{selectedSpan ? <><h2>{labels[selected] ?? selected}</h2><div className="metric"><span>Status</span><b>{selectedSpan.status}</b></div><div className="metric"><span>Duration</span><b>{selectedSpan.duration_ms.toFixed(2)} ms</b></div><pre>{JSON.stringify(selectedSpan.metadata, null, 2)}</pre></> : evaluation ? <><h2>Evaluation</h2><pre>{JSON.stringify(evaluation, null, 2)}</pre></> : result ? <><h2>Execution summary</h2><div className="badges"><span>{result.provider}</span><span>{result.attempts} provider calls</span><span>{result.retry_count} retries</span><span>{result.cache_hit ? 'Cache hit' : 'Cache miss'}</span></div><p>{result.response ?? JSON.stringify(result.structured_response)}</p><h3>Trace timeline</h3>{result.trace.map((span) => <button className="timeline" onClick={() => setSelected(span.name)} key={`${span.name}-${span.started_at_ms}`}><span>{span.started_at_ms.toFixed(1)} ms</span>{labels[span.name] ?? span.name}<b>{span.status}</b></button>)}</> : <div className="empty">Run a preset to inspect the real backend trace.</div>}</div></section></main></div></div>;
}

createRoot(document.getElementById('root')!).render(<App />);
