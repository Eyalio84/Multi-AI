import React, { useState } from 'react';
import { Expert } from '../../types';
import * as api from '../../services/apiService';

interface ExpertConfigProps {
  expert: Expert;
  onEdit: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
}

const ExpertConfig: React.FC<ExpertConfigProps> = ({ expert, onEdit, onDelete, onDuplicate }) => {
  const [testQuery, setTestQuery] = useState('');
  const [testResults, setTestResults] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const runTest = async () => {
    if (!testQuery.trim() || !expert.kg_db_id) return;
    setTesting(true);
    try {
      const results = await api.kgosQuery(expert.kg_db_id, testQuery, {
        alpha: expert.retrieval_alpha,
        beta: expert.retrieval_beta,
        gamma: expert.retrieval_gamma,
        delta: expert.retrieval_delta,
        limit: expert.retrieval_limit,
        methods: expert.retrieval_methods,
      });
      setTestResults(results);
    } catch (e: any) {
      setTestResults({ error: e.message });
    } finally {
      setTesting(false);
    }
  };

  const Row = ({ label, value }: { label: string; value: React.ReactNode }) => (
    <div className="flex justify-between items-start py-1.5" style={{ borderBottom: '1px solid var(--t-border)' }}>
      <span className="text-xs" style={{ color: 'var(--t-muted)' }}>{label}</span>
      <span className="text-xs text-right max-w-[60%]" style={{ color: 'var(--t-text)' }}>{value}</span>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto p-4 space-y-6">
      {/* Actions */}
      <div className="flex gap-2">
        <button onClick={onEdit} className="text-xs px-3 py-1.5 rounded font-medium" style={{ background: 'var(--t-primary)', color: '#fff' }}>Edit</button>
        <button onClick={onDuplicate} className="text-xs px-3 py-1.5 rounded border" style={{ borderColor: 'var(--t-border)', color: 'var(--t-muted)' }}>Duplicate</button>
        <button onClick={onDelete} className="text-xs px-3 py-1.5 rounded border" style={{ borderColor: '#ef4444', color: '#ef4444' }}>Delete</button>
      </div>

      {/* Configuration */}
      <section>
        <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--t-text)' }}>Configuration</h3>
        <div className="rounded-lg p-3" style={{ background: 'var(--t-surface)' }}>
          <Row label="Name" value={expert.name} />
          <Row label="Persona" value={expert.persona_name} />
          <Row label="Style" value={expert.persona_style} />
          <Row label="Primary KG" value={expert.kg_db_id || 'None'} />
          <Row label="Additional KGs" value={expert.kg_db_ids?.length ? expert.kg_db_ids.join(', ') : 'None'} />
          <Row label="Methods" value={expert.retrieval_methods?.join(', ')} />
          <Row label="Weights" value={`E:${expert.retrieval_alpha} T:${expert.retrieval_beta} G:${expert.retrieval_gamma} I:${expert.retrieval_delta}`} />
          <Row label="Result limit" value={expert.retrieval_limit} />
          <Row label="Playbook skills" value={expert.playbook_skills?.length || 0} />
          <Row label="Created" value={new Date(expert.created_at).toLocaleDateString()} />
        </div>
      </section>

      {/* Persona instructions */}
      {expert.persona_instructions && (
        <section>
          <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--t-text)' }}>Persona Instructions</h3>
          <div className="text-xs p-3 rounded-lg whitespace-pre-wrap" style={{ background: 'var(--t-surface)', color: 'var(--t-muted)' }}>
            {expert.persona_instructions}
          </div>
        </section>
      )}

      {/* Test Query */}
      <section>
        <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--t-text)' }}>Test KG-OS Query</h3>
        <div className="flex gap-2 mb-2">
          <input
            value={testQuery}
            onChange={e => setTestQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && runTest()}
            placeholder="Test a query against this expert's KG..."
            className="flex-1 text-xs px-2 py-1.5 rounded border outline-none"
            style={{ background: 'var(--t-bg)', borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
          />
          <button onClick={runTest} disabled={testing || !testQuery.trim() || !expert.kg_db_id}
            className="text-xs px-3 py-1.5 rounded"
            style={{ background: 'var(--t-primary)', color: '#fff' }}>
            {testing ? '...' : 'Test'}
          </button>
        </div>
        {testResults && (
          <div className="space-y-1">
            {testResults.error ? (
              <div className="text-xs p-2 rounded" style={{ background: '#ef444422', color: '#ef4444' }}>{testResults.error}</div>
            ) : (
              <>
                <div className="text-xs" style={{ color: 'var(--t-muted)' }}>
                  Intent: <strong>{testResults.intent}</strong> | {testResults.total} results
                </div>
                {testResults.results?.slice(0, 5).map((r: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 p-1.5 rounded text-xs" style={{ background: 'var(--t-surface)' }}>
                    <span className="font-medium truncate" style={{ color: 'var(--t-text)' }}>{r.node.name}</span>
                    <span className="flex-shrink-0" style={{ color: expert.color }}>{(r.score * 100).toFixed(0)}%</span>
                    <span className="flex-shrink-0" style={{ color: 'var(--t-muted)' }}>{r.method}</span>
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </section>
    </div>
  );
};

export default ExpertConfig;
