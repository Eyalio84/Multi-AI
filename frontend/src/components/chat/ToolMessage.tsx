import React from 'react';
import { Message } from '../../types/index';

const ToolMessage: React.FC<{ message: Message }> = ({ message }) => {
  const tr = message.toolResponse;
  if (!tr) return null;

  const content = tr.response?.content;
  const isError = content?.error;

  return (
    <div
      className="t-card p-3 rounded-lg text-sm border"
      style={{
        background: isError ? 'color-mix(in srgb, var(--t-error) 15%, var(--t-surface))' : 'var(--t-surface)',
        borderColor: isError ? 'var(--t-error)' : 'var(--t-border)',
        color: 'var(--t-text)',
      }}
    >
      <div className="flex items-center gap-2 mb-1">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: 'var(--t-success)' }}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="font-mono text-xs" style={{ color: 'var(--t-success)' }}>{tr.name}</span>
      </div>
      <pre className="p-2 rounded text-xs overflow-x-auto max-h-60" style={{ background: 'var(--t-bg)', color: 'var(--t-text2)' }}>
        <code>{typeof content === 'string' ? content : JSON.stringify(content, null, 2)}</code>
      </pre>
    </div>
  );
};

export default ToolMessage;
