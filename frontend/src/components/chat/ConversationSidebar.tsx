import React, { useState, useEffect } from 'react';
import * as apiService from '../../services/apiService';
import { Conversation } from '../../types/memory';

interface Props {
  isOpen: boolean;
  onToggle: () => void;
  onLoadConversation: (messages: any[]) => void;
}

const ConversationSidebar: React.FC<Props> = ({ isOpen, onToggle, onLoadConversation }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      apiService.listConversations().then(data => {
        setConversations(Array.isArray(data) ? data : []);
        setLoading(false);
      }).catch(() => setLoading(false));
    }
  }, [isOpen]);

  const handleLoad = async (id: string) => {
    try {
      const data = await apiService.getConversation(id);
      if (data?.messages) {
        onLoadConversation(data.messages);
      }
    } catch {}
  };

  const handleDelete = async (id: string) => {
    try {
      await apiService.deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
    } catch {}
  };

  const formatTime = (ts: string) => {
    if (!ts) return '';
    const d = new Date(ts);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffH = diffMs / (1000 * 60 * 60);
    if (diffH < 1) return `${Math.round(diffH * 60)}m ago`;
    if (diffH < 24) return `${Math.round(diffH)}h ago`;
    return `${Math.round(diffH / 24)}d ago`;
  };

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="absolute top-14 left-2 z-10 p-2 rounded-lg"
        style={{ background: 'var(--t-surface)', color: 'var(--t-muted)', border: '1px solid var(--t-border)' }}
        title="Show conversation history"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
    );
  }

  return (
    <div
      className="w-64 border-r flex flex-col h-full flex-shrink-0"
      style={{ background: 'var(--t-surface)', borderColor: 'var(--t-border)' }}
    >
      <div className="flex items-center justify-between p-3 border-b" style={{ borderColor: 'var(--t-border)' }}>
        <span className="text-xs font-semibold" style={{ color: 'var(--t-text)' }}>History</span>
        <button onClick={onToggle} className="text-xs" style={{ color: 'var(--t-muted)' }}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="p-4 text-center text-xs" style={{ color: 'var(--t-muted)' }}>Loading...</div>
        )}
        {!loading && conversations.length === 0 && (
          <div className="p-4 text-center text-xs" style={{ color: 'var(--t-muted)' }}>No conversations yet</div>
        )}
        {conversations.map(conv => (
          <div
            key={conv.id}
            className="p-2 mx-1 my-0.5 rounded cursor-pointer group"
            style={{ color: 'var(--t-text)' }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--t-surface2)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            onClick={() => handleLoad(conv.id)}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium truncate flex-1">
                {conv.mode} ({conv.source})
              </span>
              <button
                onClick={e => { e.stopPropagation(); handleDelete(conv.id); }}
                className="hidden group-hover:block text-xs px-1"
                style={{ color: 'var(--t-error)' }}
              >
                &times;
              </button>
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px]" style={{ color: 'var(--t-muted)' }}>
                {conv.message_count} msgs
              </span>
              <span className="text-[10px]" style={{ color: 'var(--t-muted)' }}>
                {formatTime(conv.last_message_at)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ConversationSidebar;
