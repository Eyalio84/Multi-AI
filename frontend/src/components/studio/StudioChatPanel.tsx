/** StudioChatPanel — Chat with studio-aware message rendering */
import React, { useState, useRef, useEffect } from 'react';
import { useStudio } from '../../context/StudioContext';
import StudioMessageItem from './StudioMessageItem';

const StudioChatPanel: React.FC = () => {
  const { messages, streamingText, streamingPlan, isStreaming, sendMessage } = useStudio();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput('');
    await sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-3" style={{ background: 'var(--t-surface2)' }}>
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} style={{ color: 'var(--t-primary)' }}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
            </div>
            <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--t-text)' }}>Describe your app</h3>
            <p className="text-xs max-w-xs" style={{ color: 'var(--t-muted)' }}>
              Tell me what you want to build. I'll generate a complete React app with live preview.
            </p>
            <div className="mt-4 space-y-1.5">
              {[
                'Build a todo app with categories and due dates',
                'Create a weather dashboard with charts',
                'Make a markdown note-taking app',
              ].map(suggestion => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="block w-full text-left text-xs px-3 py-2 rounded transition-colors"
                  style={{ background: 'var(--t-surface)', color: 'var(--t-text2)', border: '1px solid var(--t-border)' }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <StudioMessageItem key={msg.id} message={msg} />
        ))}

        {/* Streaming indicator */}
        {isStreaming && streamingText && (
          <StudioMessageItem
            message={{
              id: '__streaming__',
              role: 'assistant',
              content: streamingText,
              timestamp: new Date().toISOString(),
              plan: streamingPlan || undefined,
            }}
            isStreaming
          />
        )}

        {isStreaming && !streamingText && (
          <div className="flex items-center gap-2 px-3 py-2 rounded" style={{ background: 'var(--t-surface)' }}>
            <div className="flex gap-1">
              <div className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--t-primary)', animationDelay: '0ms' }} />
              <div className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--t-primary)', animationDelay: '150ms' }} />
              <div className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--t-primary)', animationDelay: '300ms' }} />
            </div>
            <span className="text-xs" style={{ color: 'var(--t-muted)' }}>AI is thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex-shrink-0 p-3 border-t" style={{ borderColor: 'var(--t-border)' }}>
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={messages.length === 0 ? 'Describe the app you want to build...' : 'Ask for changes or new features...'}
            rows={2}
            className="flex-1 resize-none rounded-lg px-3 py-2 text-sm outline-none"
            style={{
              background: 'var(--t-surface)',
              color: 'var(--t-text)',
              border: '1px solid var(--t-border)',
              fontFamily: 'var(--t-font)',
            }}
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="flex-shrink-0 p-2.5 rounded-lg transition-colors disabled:opacity-40"
            style={{ background: 'var(--t-primary)', color: '#fff' }}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
};

export default StudioChatPanel;
