import React, { useState, useRef, useCallback } from 'react';
import * as api from '../../services/apiService';
import type { GameProject } from '../../types/game';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Props {
  game: GameProject;
}

const GameChat: React.FC<Props> = ({ game }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const send = useCallback(async () => {
    if (!input.trim() || streaming) return;
    const query = input.trim();
    setInput('');

    const userMsg: Message = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setStreaming(true);

    try {
      const stream = await api.streamGameChat(game.id, query, undefined, messages);
      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let assistantText = '';

      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const lines = decoder.decode(value, { stream: true }).split('\n');
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'content') {
              assistantText += data.text;
              setMessages(prev => {
                const copy = [...prev];
                copy[copy.length - 1] = { role: 'assistant', content: assistantText };
                return copy;
              });
            }
          } catch {}
        }
      }
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}` }]);
    } finally {
      setStreaming(false);
      scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [input, streaming, game.id, messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {messages.length === 0 && (
          <div className="text-center py-8" style={{ color: 'var(--t-muted)' }}>
            <div className="text-sm">Chat with GameForge about your game</div>
            <div className="text-xs mt-1">Ask about Phaser 3 APIs, game mechanics, or code help</div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className="max-w-[80%] px-3 py-2 rounded-lg text-sm whitespace-pre-wrap"
              style={{
                background: m.role === 'user' ? 'var(--t-primary)' : 'var(--t-surface)',
                color: m.role === 'user' ? '#fff' : 'var(--t-text)',
              }}
            >
              {m.content || (streaming && i === messages.length - 1 ? '...' : '')}
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
      </div>

      <div className="p-2 border-t flex gap-2" style={{ borderColor: 'var(--t-border)' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Ask about your game..."
          className="flex-1 min-w-0 px-3 py-2 rounded text-sm"
          style={{ background: 'var(--t-surface)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
        />
        <button
          onClick={send}
          disabled={streaming || !input.trim()}
          className="flex-shrink-0 px-3 py-2 rounded text-sm font-medium"
          style={{ background: 'var(--t-primary)', color: '#fff', opacity: streaming ? 0.5 : 1 }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default GameChat;
