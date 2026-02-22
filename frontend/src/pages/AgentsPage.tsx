import React, { useState, useEffect } from 'react';
import * as apiService from '../services/apiService';
import { NlkeAgent } from '../types/index';

const CATEGORIES = ['ALL', 'FOUNDATION', 'DEV', 'AGENT', 'KNOWLEDGE', 'REASONING', 'SPECIALIZED', 'ORCHESTRATION'];

const categoryColors: Record<string, string> = {
  FOUNDATION: 'bg-blue-700',
  DEV: 'bg-green-700',
  AGENT: 'bg-purple-700',
  KNOWLEDGE: 'bg-yellow-700',
  REASONING: 'bg-pink-700',
  SPECIALIZED: 'bg-indigo-700',
  ORCHESTRATION: 'bg-red-700',
};

const AgentsPage: React.FC = () => {
  const [agents, setAgents] = useState<NlkeAgent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<NlkeAgent | null>(null);
  const [category, setCategory] = useState('ALL');
  const [workload, setWorkload] = useState('{\n  "goal": "",\n  "context": {}\n}');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [pipelineSteps, setPipelineSteps] = useState<string[]>([]);

  useEffect(() => {
    apiService.listAgents().then(data => setAgents(data.agents || [])).catch(() => {});
  }, []);

  const filtered = category === 'ALL' ? agents : agents.filter(a => a.category === category);

  const handleLoadExample = async () => {
    if (!selectedAgent) return;
    try {
      const data = await apiService.getAgentExample(selectedAgent.name);
      setWorkload(JSON.stringify(data.example || {}, null, 2));
    } catch {}
  };

  const handleRun = async () => {
    if (!selectedAgent) return;
    setLoading(true);
    setResult(null);
    try {
      const parsed = JSON.parse(workload);
      const data = await apiService.runAgent(selectedAgent.name, parsed);
      setResult(data.result);
    } catch (e: any) {
      setResult({ error: e.message });
    }
    setLoading(false);
  };

  const handleRunPipeline = async () => {
    if (pipelineSteps.length === 0) return;
    setLoading(true);
    setResult(null);
    try {
      const steps = pipelineSteps.map(name => ({ agent: name, workload: JSON.parse(workload) }));
      const data = await apiService.runPipeline(steps);
      setResult(data.result);
    } catch (e: any) {
      setResult({ error: e.message });
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col lg:flex-row h-full">
      {/* Agent list */}
      <div className="w-full lg:w-72 border-b lg:border-b-0 lg:border-r flex flex-col" style={{ borderColor: 'var(--t-border)' }}>
        <div className="p-2 border-b" style={{ borderColor: 'var(--t-border)' }}>
          <div className="flex flex-wrap gap-1">
            {CATEGORIES.map(c => (
              <button
                key={c}
                onClick={() => setCategory(c)}
                className={`t-btn px-2 py-0.5 text-[10px] rounded`}
                style={category === c
                  ? { background: 'var(--t-primary)', color: 'var(--t-text)' }
                  : { background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {filtered.map(agent => (
            <button
              key={agent.name}
              onClick={() => setSelectedAgent(agent)}
              className={`t-btn w-full text-left px-3 py-2 border-b`}
              style={{
                borderColor: 'var(--t-surface)',
                ...(selectedAgent?.name === agent.name ? { background: 'var(--t-surface2)' } : {}),
              }}
              onMouseEnter={e => { if (selectedAgent?.name !== agent.name) e.currentTarget.style.background = 'var(--t-surface2)'; }}
              onMouseLeave={e => { if (selectedAgent?.name !== agent.name) e.currentTarget.style.background = ''; }}
            >
              <div className="flex items-center gap-2">
                <span className={`px-1.5 py-0.5 text-[9px] rounded ${categoryColors[agent.category] || 'bg-gray-600'}`}>
                  {agent.category}
                </span>
                <span className="text-sm truncate" style={{ color: 'var(--t-text2)' }}>{agent.name}</span>
              </div>
              <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--t-muted)' }}>{agent.description}</p>
            </button>
          ))}
        </div>

        {/* Pipeline builder */}
        <div className="border-t p-2" style={{ borderColor: 'var(--t-border)' }}>
          <p className="text-xs font-semibold mb-1" style={{ color: 'var(--t-muted)' }}>Pipeline ({pipelineSteps.length} steps)</p>
          <div className="flex flex-wrap gap-1 mb-2">
            {pipelineSteps.map((s, i) => (
              <span key={i} className="px-1.5 py-0.5 text-[10px] rounded flex items-center gap-1" style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}>
                {s}
                <button onClick={() => setPipelineSteps(prev => prev.filter((_, j) => j !== i))} style={{ color: 'var(--t-error)' }}>&times;</button>
              </span>
            ))}
          </div>
          {selectedAgent && (
            <button
              onClick={() => setPipelineSteps(prev => [...prev, selectedAgent.name])}
              className="t-btn w-full px-2 py-1 text-xs rounded"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}
            >
              + Add "{selectedAgent.name}" to pipeline
            </button>
          )}
          {pipelineSteps.length > 0 && (
            <button
              onClick={handleRunPipeline}
              disabled={loading}
              className="t-btn w-full mt-1 px-2 py-1 text-xs rounded disabled:opacity-50"
              style={{ background: 'var(--t-accent1)', color: 'var(--t-text)' }}
            >
              Run Pipeline
            </button>
          )}
        </div>
      </div>

      {/* Execution panel */}
      <div className="flex-1 flex flex-col min-w-0">
        {selectedAgent ? (
          <>
            <div className="t-card p-3 border-b" style={{ background: 'var(--t-surface)', borderColor: 'var(--t-border)' }}>
              <h2 className="text-lg font-bold" style={{ color: 'var(--t-text)' }}>{selectedAgent.name}</h2>
              <p className="text-sm" style={{ color: 'var(--t-muted)' }}>{selectedAgent.description}</p>
              <span className={`inline-block mt-1 px-2 py-0.5 text-xs rounded ${categoryColors[selectedAgent.category] || 'bg-gray-600'}`}>
                {selectedAgent.category}
              </span>
            </div>

            <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
              {/* Workload editor */}
              <div className="flex-1 flex flex-col border-b lg:border-b-0 lg:border-r" style={{ borderColor: 'var(--t-border)' }}>
                <div className="flex items-center justify-between p-2 border-b" style={{ background: 'var(--t-surface)', borderColor: 'var(--t-border)' }}>
                  <span className="text-xs" style={{ color: 'var(--t-muted)' }}>Workload JSON</span>
                  <div className="flex gap-1">
                    <button onClick={handleLoadExample} className="t-btn px-2 py-0.5 text-xs rounded" style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>Example</button>
                    <button
                      onClick={handleRun}
                      disabled={loading}
                      className="t-btn px-2 py-0.5 text-xs rounded disabled:opacity-50"
                      style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}
                    >
                      {loading ? 'Running...' : 'Run'}
                    </button>
                  </div>
                </div>
                <textarea
                  value={workload}
                  onChange={e => setWorkload(e.target.value)}
                  className="flex-1 p-3 font-mono text-sm resize-none focus:outline-none"
                  style={{ background: 'var(--t-bg)', color: 'var(--t-text2)' }}
                  spellCheck={false}
                />
              </div>

              {/* Results */}
              <div className="flex-1 flex flex-col">
                <div className="p-2 border-b" style={{ background: 'var(--t-surface)', borderColor: 'var(--t-border)' }}>
                  <span className="text-xs" style={{ color: 'var(--t-muted)' }}>Results</span>
                </div>
                <div className="flex-1 overflow-y-auto p-3">
                  {loading && <div className="text-center" style={{ color: 'var(--t-muted)' }}><div className="animate-spin h-8 w-8 border-2 border-t-transparent rounded-full mx-auto" style={{ borderColor: 'var(--t-primary)', borderTopColor: 'transparent' }} /></div>}
                  {result && (
                    <pre className="text-xs whitespace-pre-wrap font-mono" style={{ color: 'var(--t-text2)' }}>
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  )}
                  {!result && !loading && <p className="text-sm text-center mt-10" style={{ color: 'var(--t-muted)' }}>Run an agent to see results</p>}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full" style={{ color: 'var(--t-muted)' }}>
            <div className="text-center">
              <p className="text-lg">33 NLKE Agents</p>
              <p className="text-sm mt-1">Select an agent from the list to get started</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentsPage;
