import React, { useState, useRef, useEffect } from 'react';
import * as api from '../../services/apiService';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: { id: string; name: string; type: string }[];
}

interface Props {
  dbId: string | null;
}

const KGRagChat: React.FC<Props> = ({ dbId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'hybrid' | 'graphrag'>('hybrid');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const sendMessage = async () => {
    if (!dbId || !input.trim() || loading) return;
    const query = input.trim();
    setInput('');
    const userMsg: ChatMessage = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const stream = await api.streamKGChat(
        dbId, query,
        messages.map(m => ({ role: m.role, content: m.content })),
        mode,
      );
      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';
      let sources: ChatMessage['sources'] = [];

      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n');
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6).trim();
          if (data === '[DONE]') continue;
          try {
            const parsed = JSON.parse(data);
            if (parsed.type === 'content') {
              assistantContent += parsed.text || '';
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: 'assistant', content: assistantContent, sources };
                return updated;
              });
            } else if (parsed.type === 'sources') {
              sources = parsed.nodes || [];
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { ...updated[updated.length - 1], sources };
                return updated;
              });
            }
          } catch { /* non-JSON line */ }
        }
      }
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  if (!dbId) return (
    <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--t-muted)' }}>
      Select a database to start a RAG chat
    </div>
  );

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Mode selector */}
      <div className="p-2 border-b flex items-center gap-2" style={{ borderColor: 'var(--t-border)' }}>
        <span className="text-[10px]" style={{ color: 'var(--t-muted)' }}>RAG Mode:</span>
        {(['hybrid', 'graphrag'] as const).map(m => (
          <button key={m} onClick={() => setMode(m)}
            className="t-btn px-2 py-0.5 text-[10px] rounded"
            style={mode === m
              ? { background: 'var(--t-primary)', color: '#fff' }
              : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
            {m === 'hybrid' ? 'Hybrid (88.5%)' : 'GraphRAG'}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-center py-8" style={{ color: 'var(--t-muted)' }}>
            <p className="text-sm">Ask questions about your knowledge graph</p>
            <p className="text-xs mt-1">Uses hybrid retrieval to find relevant nodes, then generates answers with Gemini</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className="max-w-[80%] rounded-lg px-3 py-2" style={{
              background: m.role === 'user' ? 'var(--t-primary)' : 'var(--t-surface2)',
              color: m.role === 'user' ? '#fff' : 'var(--t-text2)',
            }}>
              <p className="text-sm whitespace-pre-wrap">{m.content}</p>
              {m.sources && m.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t" style={{ borderColor: 'var(--t-border)' }}>
                  <p className="text-[10px] mb-1" style={{ color: 'var(--t-muted)' }}>Sources:</p>
                  <div className="flex flex-wrap gap-1">
                    {m.sources.map(s => (
                      <span key={s.id} className="text-[10px] px-1.5 py-0.5 rounded"
                        style={{ background: 'var(--t-surface)', color: 'var(--t-text2)' }}>
                        {s.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-lg px-3 py-2 text-sm" style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}>
              Thinking...
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-2 border-t flex gap-2" style={{ borderColor: 'var(--t-border)' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          placeholder="Ask about the knowledge graph..."
          className="flex-1 px-3 py-2 rounded text-sm focus:outline-none"
          style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}
          className="t-btn px-4 py-2 rounded text-sm"
          style={{ background: 'var(--t-primary)', color: '#fff', opacity: loading || !input.trim() ? 0.5 : 1 }}>
          Send
        </button>
      </div>
    </div>
  );
};

export default KGRagChat;
