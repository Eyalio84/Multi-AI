import React, { useState } from 'react';
import { KGDatabase, KGCompareResult } from '../../types/kg';
import * as api from '../../services/apiService';

interface Props {
  databases: KGDatabase[];
}

const KGComparePanel: React.FC<Props> = ({ databases }) => {
  const [dbA, setDbA] = useState('');
  const [dbB, setDbB] = useState('');
  const [result, setResult] = useState<KGCompareResult | null>(null);
  const [diffResult, setDiffResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const doCompare = async () => {
    if (!dbA || !dbB) return;
    setLoading(true);
    setError('');
    try {
      const [comp, diff] = await Promise.all([
        api.compareKGs(dbA, dbB),
        api.diffKGs(dbA, dbB),
      ]);
      setResult(comp);
      setDiffResult(diff);
    } catch (e: any) {
      setError(e.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  const Select = ({ value, onChange, label }: { value: string; onChange: (v: string) => void; label: string }) => (
    <div className="flex-1">
      <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="w-full px-2 py-1.5 rounded text-sm focus:outline-none"
        style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}>
        <option value="">Select...</option>
        {databases.map(db => (
          <option key={db.id} value={db.id}>{db.filename}</option>
        ))}
      </select>
    </div>
  );

  return (
    <div className="flex-1 overflow-y-auto p-3 space-y-4">
      <h3 className="text-sm font-bold" style={{ color: 'var(--t-text)' }}>Compare Knowledge Graphs</h3>

      <div className="flex gap-3 items-end">
        <Select value={dbA} onChange={setDbA} label="Database A" />
        <span className="text-xs pb-2" style={{ color: 'var(--t-muted)' }}>vs</span>
        <Select value={dbB} onChange={setDbB} label="Database B" />
        <button onClick={doCompare} disabled={loading || !dbA || !dbB}
          className="t-btn px-4 py-1.5 rounded text-sm"
          style={{ background: 'var(--t-primary)', color: '#fff', opacity: !dbA || !dbB ? 0.5 : 1 }}>
          {loading ? '...' : 'Compare'}
        </button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {result && (
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded" style={{ background: 'var(--t-surface2)' }}>
            <p className="text-[10px]" style={{ color: 'var(--t-muted)' }}>Shared Nodes</p>
            <p className="text-xl font-bold" style={{ color: 'var(--t-primary)' }}>{result.shared_nodes}</p>
          </div>
          <div className="p-3 rounded" style={{ background: 'var(--t-surface2)' }}>
            <p className="text-[10px]" style={{ color: 'var(--t-muted)' }}>Jaccard Similarity</p>
            <p className="text-xl font-bold" style={{ color: 'var(--t-primary)' }}>
              {(result.jaccard_similarity * 100).toFixed(1)}%
            </p>
          </div>
          <div className="p-3 rounded" style={{ background: 'var(--t-surface2)' }}>
            <p className="text-[10px]" style={{ color: 'var(--t-muted)' }}>Unique to A</p>
            <p className="text-xl font-bold" style={{ color: 'var(--t-accent1, var(--t-text))' }}>{result.unique_a}</p>
          </div>
          <div className="p-3 rounded" style={{ background: 'var(--t-surface2)' }}>
            <p className="text-[10px]" style={{ color: 'var(--t-muted)' }}>Unique to B</p>
            <p className="text-xl font-bold" style={{ color: 'var(--t-accent1, var(--t-text))' }}>{result.unique_b}</p>
          </div>
        </div>
      )}

      {diffResult && (
        <div>
          <h4 className="text-xs font-bold mb-2" style={{ color: 'var(--t-text)' }}>Diff Details</h4>
          <pre className="p-3 rounded text-[10px] overflow-x-auto" style={{
            background: 'var(--t-surface2)', color: 'var(--t-text2)', maxHeight: 300,
          }}>
            {JSON.stringify(diffResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default KGComparePanel;
