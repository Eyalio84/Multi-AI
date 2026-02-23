import React, { useState, useEffect } from 'react';
import { Expert } from '../../types';
import * as api from '../../services/apiService';

interface ExpertBuilderProps {
  expert?: Expert | null;
  onSave: (expert: Expert) => void;
  onCancel: () => void;
}

const ICONS = ['brain', 'code', 'chart', 'book', 'shield', 'star'];
const COLORS = ['#0ea5e9', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1', '#14b8a6'];
const STYLES = ['professional', 'casual', 'academic', 'concise', 'detailed', 'socratic'];

const ExpertBuilder: React.FC<ExpertBuilderProps> = ({ expert, onSave, onCancel }) => {
  const [databases, setDatabases] = useState<any[]>([]);
  const [form, setForm] = useState({
    name: '', description: '', kg_db_id: '', kg_db_ids: [] as string[],
    persona_name: 'Expert', persona_instructions: '', persona_style: 'professional',
    retrieval_methods: ['hybrid', 'intent'] as string[],
    retrieval_alpha: 0.35, retrieval_beta: 0.40, retrieval_gamma: 0.15, retrieval_delta: 0.10,
    retrieval_limit: 10,
    dimension_filters: {} as Record<string, any>,
    playbook_skills: [] as string[],
    icon: 'brain', color: '#0ea5e9', is_public: true,
  });

  useEffect(() => {
    api.listKGDatabases().then(setDatabases).catch(() => {});
    if (expert) {
      setForm({
        name: expert.name, description: expert.description,
        kg_db_id: expert.kg_db_id, kg_db_ids: expert.kg_db_ids || [],
        persona_name: expert.persona_name, persona_instructions: expert.persona_instructions,
        persona_style: expert.persona_style,
        retrieval_methods: expert.retrieval_methods || ['hybrid', 'intent'],
        retrieval_alpha: expert.retrieval_alpha, retrieval_beta: expert.retrieval_beta,
        retrieval_gamma: expert.retrieval_gamma, retrieval_delta: expert.retrieval_delta,
        retrieval_limit: expert.retrieval_limit,
        dimension_filters: expert.dimension_filters || {},
        playbook_skills: expert.playbook_skills || [],
        icon: expert.icon || 'brain', color: expert.color || '#0ea5e9',
        is_public: expert.is_public,
      });
    }
  }, [expert]);

  const handleSave = async () => {
    try {
      const result = expert
        ? await api.updateExpert(expert.id, form)
        : await api.createExpert(form);
      onSave(result);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const totalWeight = form.retrieval_alpha + form.retrieval_beta + form.retrieval_gamma + form.retrieval_delta;

  return (
    <div className="h-full overflow-y-auto p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold" style={{ color: 'var(--t-text)' }}>
          {expert ? 'Edit Expert' : 'Create Expert'}
        </h2>
        <div className="flex gap-2">
          <button onClick={onCancel} className="text-xs px-3 py-1.5 rounded border" style={{ borderColor: 'var(--t-border)', color: 'var(--t-muted)' }}>Cancel</button>
          <button onClick={handleSave} className="text-xs px-3 py-1.5 rounded font-medium" style={{ background: 'var(--t-primary)', color: '#fff' }}>Save</button>
        </div>
      </div>

      {/* Identity */}
      <section className="space-y-3">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--t-text)' }}>Identity</h3>
        <input
          placeholder="Expert name"
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
          className="w-full text-sm px-3 py-2 rounded border outline-none"
          style={{ background: 'var(--t-bg)', borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
        />
        <textarea
          placeholder="Description..."
          value={form.description}
          onChange={e => setForm({ ...form, description: e.target.value })}
          className="w-full text-sm px-3 py-2 rounded border outline-none resize-none"
          rows={2}
          style={{ background: 'var(--t-bg)', borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
        />
        <div className="flex gap-2 items-center">
          <span className="text-xs" style={{ color: 'var(--t-muted)' }}>Icon:</span>
          {ICONS.map(ic => (
            <button key={ic} onClick={() => setForm({ ...form, icon: ic })}
              className={`text-xs px-2 py-1 rounded border ${form.icon === ic ? 'font-bold' : ''}`}
              style={{ borderColor: form.icon === ic ? form.color : 'var(--t-border)', color: form.icon === ic ? form.color : 'var(--t-muted)' }}>
              {ic}
            </button>
          ))}
        </div>
        <div className="flex gap-1 items-center">
          <span className="text-xs" style={{ color: 'var(--t-muted)' }}>Color:</span>
          {COLORS.map(c => (
            <button key={c} onClick={() => setForm({ ...form, color: c })}
              className="w-6 h-6 rounded-full border-2"
              style={{ background: c, borderColor: form.color === c ? 'var(--t-text)' : 'transparent' }} />
          ))}
        </div>
      </section>

      {/* Knowledge Graph */}
      <section className="space-y-3">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--t-text)' }}>Knowledge Graph</h3>
        <select
          value={form.kg_db_id}
          onChange={e => setForm({ ...form, kg_db_id: e.target.value })}
          className="w-full text-sm px-3 py-2 rounded border outline-none"
          style={{ background: 'var(--t-bg)', borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
        >
          <option value="">Select primary KG...</option>
          {databases.map((db: any) => (
            <option key={db.id} value={db.id}>{db.id} ({db.filename})</option>
          ))}
        </select>
      </section>

      {/* Persona */}
      <section className="space-y-3">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--t-text)' }}>Persona</h3>
        <input
          placeholder="Persona name (e.g. PyGuru)"
          value={form.persona_name}
          onChange={e => setForm({ ...form, persona_name: e.target.value })}
          className="w-full text-sm px-3 py-2 rounded border outline-none"
          style={{ background: 'var(--t-bg)', borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
        />
        <textarea
          placeholder="Persona instructions..."
          value={form.persona_instructions}
          onChange={e => setForm({ ...form, persona_instructions: e.target.value })}
          className="w-full text-sm px-3 py-2 rounded border outline-none resize-none"
          rows={3}
          style={{ background: 'var(--t-bg)', borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
        />
        <div className="flex gap-1 flex-wrap">
          {STYLES.map(s => (
            <button key={s} onClick={() => setForm({ ...form, persona_style: s })}
              className="text-xs px-2 py-1 rounded border"
              style={{ borderColor: form.persona_style === s ? 'var(--t-primary)' : 'var(--t-border)',
                       color: form.persona_style === s ? 'var(--t-primary)' : 'var(--t-muted)',
                       background: form.persona_style === s ? 'var(--t-primary)' + '15' : 'transparent' }}>
              {s}
            </button>
          ))}
        </div>
      </section>

      {/* Retrieval Config */}
      <section className="space-y-3">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--t-text)' }}>Retrieval Weights</h3>
        <div className="text-xs" style={{ color: totalWeight > 1.05 || totalWeight < 0.95 ? 'var(--t-error)' : 'var(--t-muted)' }}>
          Sum: {totalWeight.toFixed(2)} {totalWeight > 1.05 || totalWeight < 0.95 ? '(should be ~1.0)' : ''}
        </div>
        {[
          { key: 'retrieval_alpha', label: 'Embedding (alpha)', color: '#8b5cf6' },
          { key: 'retrieval_beta', label: 'Text/BM25 (beta)', color: '#10b981' },
          { key: 'retrieval_gamma', label: 'Graph (gamma)', color: '#f59e0b' },
          { key: 'retrieval_delta', label: 'Intent (delta)', color: '#ef4444' },
        ].map(({ key, label, color }) => (
          <div key={key} className="flex items-center gap-2">
            <span className="text-xs w-32" style={{ color }}>{label}</span>
            <input
              type="range" min="0" max="1" step="0.05"
              value={(form as any)[key]}
              onChange={e => setForm({ ...form, [key]: parseFloat(e.target.value) })}
              className="flex-1"
            />
            <span className="text-xs w-8 text-right" style={{ color: 'var(--t-muted)' }}>{(form as any)[key].toFixed(2)}</span>
          </div>
        ))}
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: 'var(--t-muted)' }}>Result limit:</span>
          <input
            type="number" min={1} max={50}
            value={form.retrieval_limit}
            onChange={e => setForm({ ...form, retrieval_limit: parseInt(e.target.value) || 10 })}
            className="w-16 text-xs px-2 py-1 rounded border outline-none"
            style={{ background: 'var(--t-bg)', borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
          />
        </div>
      </section>
    </div>
  );
};

export default ExpertBuilder;
