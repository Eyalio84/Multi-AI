import React, { useState, useRef, useEffect } from 'react';
import { Expert, ExpertMessage, ExpertSource, ExpertConversation } from '../../types';
import * as api from '../../services/apiService';

interface ExpertChatProps {
  expert: Expert;
}

const ExpertChat: React.FC<ExpertChatProps> = ({ expert }) => {
  const [messages, setMessages] = useState<ExpertMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [sources, setSources] = useState<ExpertSource[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ExpertConversation[]>([]);
  const [showSources, setShowSources] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([]);
    setConversationId(null);
    setSources([]);
    api.listExpertConversations(expert.id).then(setConversations).catch(() => {});
  }, [expert.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversation = async (convId: string) => {
    try {
      const conv = await api.getExpertConversation(expert.id, convId);
      setMessages(conv.messages || []);
      setConversationId(convId);
      const lastAssistant = [...(conv.messages || [])].reverse().find((m: ExpertMessage) => m.author === 'assistant');
      if (lastAssistant?.sources) setSources(lastAssistant.sources);
    } catch { /* ignore */ }
  };

  const handleSend = async () => {
    if (!input.trim() || streaming) return;
    const query = input.trim();
    setInput('');
    setStreaming(true);
    setSources([]);

    const userMsg: ExpertMessage = {
      id: Date.now().toString(), conversation_id: conversationId || '',
      author: 'user', content: query, sources: [], retrieval_meta: {},
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    const history = messages.map(m => ({ role: m.author === 'user' ? 'user' : 'model', content: m.content }));

    try {
      const stream = await api.streamExpertChat(expert.id, query, conversationId || undefined, history);
      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let assistantText = '';
      let buffer = '';

      const assistantMsg: ExpertMessage = {
        id: (Date.now() + 1).toString(), conversation_id: conversationId || '',
        author: 'assistant', content: '', sources: [], retrieval_meta: {},
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMsg]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'content') {
              assistantText += data.text;
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { ...updated[updated.length - 1], content: assistantText };
                return updated;
              });
            } else if (data.type === 'sources') {
              setSources(data.nodes || []);
            } else if (data.type === 'conversation_id') {
              setConversationId(data.id);
            }
          } catch { /* ignore parse errors */ }
        }
      }
    } catch (e: any) {
      setMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0) {
          updated[updated.length - 1] = { ...updated[updated.length - 1], content: `Error: ${e.message}` };
        }
        return updated;
      });
    } finally {
      setStreaming(false);
      api.listExpertConversations(expert.id).then(setConversations).catch(() => {});
    }
  };

  return (
    <div className="flex h-full">
      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Conversation picker */}
        {conversations.length > 0 && (
          <div className="flex items-center gap-1 p-2 overflow-x-auto" style={{ borderBottom: '1px solid var(--t-border)' }}>
            <button onClick={() => { setMessages([]); setConversationId(null); setSources([]); }}
              className="text-[10px] px-2 py-1 rounded whitespace-nowrap"
              style={{ background: !conversationId ? 'var(--t-primary)' : 'var(--t-surface2)', color: !conversationId ? '#fff' : 'var(--t-muted)' }}>
              New
            </button>
            {conversations.slice(0, 10).map(c => (
              <button key={c.id} onClick={() => loadConversation(c.id)}
                className="text-[10px] px-2 py-1 rounded whitespace-nowrap truncate max-w-[120px]"
                style={{ background: conversationId === c.id ? 'var(--t-primary)' : 'var(--t-surface2)', color: conversationId === c.id ? '#fff' : 'var(--t-muted)' }}>
                {c.title || `Conv ${c.id.slice(0, 6)}`}
              </button>
            ))}
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="text-center py-12" style={{ color: 'var(--t-muted)' }}>
              <div className="text-2xl mb-2">
                <span style={{ color: expert.color }}>
                  {expert.persona_name || expert.name}
                </span>
              </div>
              <div className="text-xs">Ask anything backed by the <strong>{expert.kg_db_id}</strong> knowledge graph</div>
            </div>
          )}
          {messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.author === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className="max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap"
                style={{
                  background: msg.author === 'user' ? 'var(--t-primary)' : 'var(--t-surface2)',
                  color: msg.author === 'user' ? '#fff' : 'var(--t-text)',
                }}>
                {msg.content || (streaming && msg.author === 'assistant' ? '...' : '')}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-3" style={{ borderTop: '1px solid var(--t-border)' }}>
          <div className="flex gap-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder={`Ask ${expert.persona_name || expert.name}...`}
              className="flex-1 text-sm px-3 py-2 rounded border outline-none"
              style={{ background: 'var(--t-bg)', borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
              disabled={streaming}
            />
            <button onClick={handleSend} disabled={streaming || !input.trim()}
              className="px-4 py-2 rounded text-sm font-medium"
              style={{ background: streaming ? 'var(--t-surface2)' : 'var(--t-primary)', color: '#fff' }}>
              {streaming ? '...' : 'Send'}
            </button>
            <button onClick={() => setShowSources(!showSources)}
              className="px-2 py-2 rounded text-xs border"
              style={{ borderColor: showSources ? expert.color : 'var(--t-border)', color: showSources ? expert.color : 'var(--t-muted)' }}>
              Sources{sources.length > 0 ? ` (${sources.length})` : ''}
            </button>
          </div>
        </div>
      </div>

      {/* Sources panel */}
      {showSources && (
        <div className="w-64 overflow-y-auto p-3 space-y-2" style={{ borderLeft: '1px solid var(--t-border)', background: 'var(--t-surface)' }}>
          <div className="text-xs font-semibold" style={{ color: 'var(--t-text)' }}>Retrieved Sources</div>
          {sources.length === 0 ? (
            <div className="text-xs" style={{ color: 'var(--t-muted)' }}>No sources yet. Send a message.</div>
          ) : (
            sources.map((s, i) => (
              <div key={i} className="p-2 rounded text-xs space-y-1" style={{ background: 'var(--t-surface2)' }}>
                <div className="font-medium truncate" style={{ color: 'var(--t-text)' }}>{s.name}</div>
                <div className="flex gap-1">
                  <span className="px-1 rounded" style={{ background: 'var(--t-bg)', color: 'var(--t-muted)' }}>{s.type}</span>
                  <span style={{ color: expert.color }}>{(s.score * 100).toFixed(0)}%</span>
                </div>
                <div style={{ color: 'var(--t-muted)' }}>{s.method}</div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default ExpertChat;
