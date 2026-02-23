import React, { useState } from 'react';
import * as api from '../../services/apiService';

interface Props {
  dbId: string | null;
}

const KGIngestPanel: React.FC<Props> = ({ dbId }) => {
  const [text, setText] = useState('');
  const [method, setMethod] = useState<'ai' | 'lightrag' | 'manual'>('ai');
  const [source, setSource] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleIngest = async () => {
    if (!dbId || !text.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const data = await api.ingestKGText(dbId, text.trim(), method, source || undefined);
      setResult(data);
      setText('');
    } catch (e: any) {
      setError(e.message || 'Ingestion failed');
    } finally {
      setLoading(false);
    }
  };

  if (!dbId) return (
    <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--t-muted)' }}>
      Select a database to ingest content
    </div>
  );

  return (
    <div className="flex-1 flex flex-col p-3 gap-3 overflow-y-auto">
      <h3 className="text-sm font-bold" style={{ color: 'var(--t-text)' }}>Ingest Text</h3>
      <p className="text-xs" style={{ color: 'var(--t-muted)' }}>
        Extract entities and relationships from text and add them to the knowledge graph.
      </p>

      <div>
        <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Method</label>
        <div className="flex gap-1">
          {(['ai', 'lightrag', 'manual'] as const).map(m => (
            <button key={m} onClick={() => setMethod(m)}
              className="t-btn px-3 py-1 text-xs rounded"
              style={method === m
                ? { background: 'var(--t-primary)', color: '#fff' }
                : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
              {m === 'ai' ? 'AI Extract' : m === 'lightrag' ? 'LightRAG' : 'Manual'}
            </button>
          ))}
        </div>
        <p className="text-[10px] mt-1" style={{ color: 'var(--t-muted)' }}>
          {method === 'ai' && 'Uses Gemini to extract entities and relations from text'}
          {method === 'lightrag' && 'Uses LightRAG pipeline for entity extraction + community summaries'}
          {method === 'manual' && 'Stores the text as a single document node'}
        </p>
      </div>

      <div>
        <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Source (optional)</label>
        <input value={source} onChange={e => setSource(e.target.value)}
          placeholder="e.g. document.pdf, meeting notes"
          className="w-full px-3 py-1.5 rounded text-sm focus:outline-none"
          style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }} />
      </div>

      <div className="flex-1">
        <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Text to ingest</label>
        <textarea value={text} onChange={e => setText(e.target.value)}
          rows={10}
          className="w-full h-full min-h-[200px] px-3 py-2 rounded text-sm focus:outline-none"
          style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}
          placeholder="Paste text here..." />
      </div>

      <button onClick={handleIngest} disabled={loading || !text.trim()}
        className="t-btn px-4 py-2 rounded text-sm"
        style={{ background: 'var(--t-primary)', color: '#fff', opacity: loading || !text.trim() ? 0.5 : 1 }}>
        {loading ? 'Ingesting...' : 'Ingest'}
      </button>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {result && (
        <div className="p-3 rounded text-xs" style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
          <p className="font-bold mb-1" style={{ color: 'var(--t-primary)' }}>Ingestion Complete</p>
          <pre className="whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default KGIngestPanel;
