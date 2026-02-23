import React, { useState } from 'react';
import { Expert } from '../../types';
import ExpertCard from './ExpertCard';

interface ExpertListProps {
  experts: Expert[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  loading: boolean;
}

const ExpertList: React.FC<ExpertListProps> = ({ experts, selectedId, onSelect, onCreate, loading }) => {
  const [search, setSearch] = useState('');

  const filtered = experts.filter(e =>
    e.name.toLowerCase().includes(search.toLowerCase()) ||
    e.kg_db_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full" style={{ borderRight: '1px solid var(--t-border)' }}>
      <div className="p-3 space-y-2" style={{ borderBottom: '1px solid var(--t-border)' }}>
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold" style={{ color: 'var(--t-text)' }}>Experts</span>
          <button
            onClick={onCreate}
            className="text-xs px-2 py-1 rounded font-medium"
            style={{ background: 'var(--t-primary)', color: '#fff' }}
          >
            + New
          </button>
        </div>
        <input
          type="text"
          placeholder="Search experts..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full text-xs px-2 py-1.5 rounded border outline-none"
          style={{ background: 'var(--t-bg)', borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
        />
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {loading ? (
          <div className="text-xs text-center py-4" style={{ color: 'var(--t-muted)' }}>Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="text-xs text-center py-4" style={{ color: 'var(--t-muted)' }}>
            {experts.length === 0 ? 'No experts yet. Create one!' : 'No matches'}
          </div>
        ) : (
          filtered.map(expert => (
            <ExpertCard
              key={expert.id}
              expert={expert}
              isSelected={selectedId === expert.id}
              onClick={() => onSelect(expert.id)}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default ExpertList;
