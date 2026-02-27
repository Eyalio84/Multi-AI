/** StudioMessageItem — Message renderer with file badges, inline code blocks */
import React, { useState } from 'react';
import type { StudioMessage } from '../../types/studio';

interface Props {
  message: StudioMessage;
  isStreaming?: boolean;
}

const StudioMessageItem: React.FC<Props> = ({ message, isStreaming }) => {
  const [showPlan, setShowPlan] = useState(false);
  const [showThinking, setShowThinking] = useState(false);
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  // Simple markdown-ish rendering for code blocks
  const renderContent = (text: string) => {
    const parts: React.ReactNode[] = [];
    const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(
          <span key={lastIndex} className="whitespace-pre-wrap">{text.slice(lastIndex, match.index)}</span>
        );
      }
      parts.push(
        <div key={match.index} className="my-2 rounded overflow-hidden" style={{ background: 'var(--t-bg)' }}>
          {match[1] && (
            <div className="text-xs px-2 py-1" style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}>
              {match[1]}
            </div>
          )}
          <pre className="text-xs p-2 overflow-x-auto" style={{ color: 'var(--t-text2)', fontFamily: 'var(--t-font-mono)' }}>
            {match[2]}
          </pre>
        </div>
      );
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) {
      parts.push(
        <span key={lastIndex} className="whitespace-pre-wrap">{text.slice(lastIndex)}</span>
      );
    }

    return parts.length > 0 ? parts : <span className="whitespace-pre-wrap">{text}</span>;
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${isStreaming ? 'animate-pulse-subtle' : ''}`}
        style={{
          background: isUser ? 'var(--t-primary)' : isSystem ? 'var(--t-error)' : 'var(--t-surface)',
          color: isUser || isSystem ? '#fff' : 'var(--t-text)',
          border: isUser || isSystem ? 'none' : '1px solid var(--t-border)',
        }}
      >
        {/* Thinking collapsible */}
        {message.thinking && (
          <div className="mb-2">
            <button
              onClick={() => setShowThinking(!showThinking)}
              className="flex items-center gap-1 text-xs font-medium opacity-70 hover:opacity-100 transition-opacity"
            >
              <svg className={`w-3 h-3 transition-transform ${showThinking ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} style={{ color: 'var(--t-warning)' }}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
              </svg>
              Thought process
            </button>
            {showThinking && (
              <div className="mt-1 text-xs p-2 rounded whitespace-pre-wrap" style={{ background: 'var(--t-bg)', color: 'var(--t-muted)', maxHeight: '200px', overflow: 'auto' }}>
                {message.thinking}
              </div>
            )}
          </div>
        )}

        {/* Plan collapsible */}
        {message.plan && (
          <div className="mb-2">
            <button
              onClick={() => setShowPlan(!showPlan)}
              className="flex items-center gap-1 text-xs font-medium opacity-70 hover:opacity-100 transition-opacity"
            >
              <svg className={`w-3 h-3 transition-transform ${showPlan ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
              Plan
            </button>
            {showPlan && (
              <div className="mt-1 text-xs p-2 rounded" style={{ background: 'var(--t-bg)', color: 'var(--t-text2)' }}>
                {message.plan}
              </div>
            )}
          </div>
        )}

        {/* Message content */}
        <div className="leading-relaxed">
          {renderContent(message.content)}
        </div>

        {/* File badges */}
        {message.files && message.files.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.files.map(f => (
              <span
                key={f.path}
                className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded"
                style={{
                  background: f.action === 'delete' ? 'var(--t-error)' : 'var(--t-success)',
                  color: '#fff',
                }}
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {f.path}
              </span>
            ))}
          </div>
        )}

        {/* Deps badge */}
        {message.deps && Object.keys(message.deps).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {Object.entries(message.deps).map(([name, ver]) => (
              <span
                key={name}
                className="text-xs px-2 py-0.5 rounded"
                style={{ background: 'var(--t-accent1)', color: '#fff' }}
              >
                {name}@{ver}
              </span>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <div className="mt-1 text-xs opacity-40">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default StudioMessageItem;
