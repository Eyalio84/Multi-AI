import React from 'react';
import { Expert } from '../../types';

const ICONS: Record<string, string> = {
  brain: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
  code: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
  chart: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
  book: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
  shield: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  star: 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z',
};

interface ExpertCardProps {
  expert: Expert;
  isSelected: boolean;
  onClick: () => void;
}

const ExpertCard: React.FC<ExpertCardProps> = ({ expert, isSelected, onClick }) => {
  const iconPath = ICONS[expert.icon] || ICONS.brain;

  return (
    <button
      onClick={onClick}
      className="w-full text-left p-3 rounded-lg transition-all border"
      style={{
        background: isSelected ? expert.color + '22' : 'var(--t-surface)',
        borderColor: isSelected ? expert.color : 'var(--t-border)',
      }}
    >
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: expert.color + '33' }}>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke={expert.color} strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d={iconPath} />
          </svg>
        </div>
        <div className="min-w-0">
          <div className="text-sm font-medium truncate" style={{ color: 'var(--t-text)' }}>{expert.name}</div>
          <div className="text-xs truncate" style={{ color: 'var(--t-muted)' }}>{expert.kg_db_id || 'No KG'}</div>
        </div>
      </div>
      {expert.retrieval_methods && (
        <div className="flex gap-1 mt-2 flex-wrap">
          {expert.retrieval_methods.slice(0, 3).map(m => (
            <span key={m} className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}>{m}</span>
          ))}
        </div>
      )}
    </button>
  );
};

export default ExpertCard;
