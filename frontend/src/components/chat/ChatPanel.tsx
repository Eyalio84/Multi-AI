import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MessageItem from './MessageItem';
import LoadingIndicator from './LoadingIndicator';
import ModelSelector from '../ModelSelector';
import ConversationSidebar from './ConversationSidebar';
import { useChat } from '../../hooks/useChat';
import { useAppContext } from '../../context/AppContext';
import { ChatMode, MessageAuthor } from '../../types/index';

const ChatPanel: React.FC<{ defaultMode?: ChatMode }> = ({ defaultMode = 'chat' }) => {
  const {
    projects, selectedProjectIds, filesByProject, activePersona, useWebSearch, customAiStyles,
    activeProvider, activeModel, thinkingEnabled, thinkingBudget,
    aiCreateFile, aiUpdateFile, aiDeleteFile,
  } = useAppContext();

  const navigate = useNavigate();
  const [mode] = useState<ChatMode>(defaultMode);
  const [prompt, setPrompt] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const selectedProjects = projects.filter(p => selectedProjectIds.has(p.id));
  const aiFileOperations = {
    listFiles: async (projectId: string) => (filesByProject.get(projectId) || []).map(f => f.path),
    createFile: aiCreateFile,
    readFile: async (projectId: string, path: string) => {
      const file = (filesByProject.get(projectId) || []).find(f => f.path === path);
      return file ? file.content : null;
    },
    updateFile: aiUpdateFile,
    deleteFile: aiDeleteFile,
  };

  const budget = thinkingEnabled ? thinkingBudget : 0;
  const { messages, isLoading, statusText, sendMessage, clearMessages, conversationId, injectionMeta } = useChat(
    selectedProjects, activePersona, activeProvider, activeModel, useWebSearch, customAiStyles, budget, aiFileOperations
  );

  const messagesEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, statusText]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading || !prompt.trim()) return;
    sendMessage(prompt, mode);
    setPrompt('');
  };

  const handleLoadConversation = (historyMessages: any[]) => {
    // Clear and load past messages — for now just clear (full load would need setMessages exposed)
    clearMessages();
    setSidebarOpen(false);
  };

  return (
    <main className="flex-1 flex h-full" style={{ background: 'var(--t-bg)' }}>
      <ConversationSidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onLoadConversation={handleLoadConversation}
      />

      <div className="flex-1 flex flex-col h-full relative">
        <div className="p-2 border-b flex items-center gap-2" style={{ borderColor: 'var(--t-border)' }}>
          <ModelSelector />
          {injectionMeta && (
            <div className="flex items-center gap-1">
              {injectionMeta.memories && (
                <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'var(--t-primary)', color: '#fff', opacity: 0.8 }}>
                  Memory
                </span>
              )}
              {injectionMeta.skills && (
                <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'var(--t-accent1, var(--t-primary))', color: '#fff', opacity: 0.8 }}>
                  Skills
                </span>
              )}
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {messages.length === 0 && (
              <div className="max-w-2xl mx-auto mt-8 px-4">
                {/* Hero */}
                <div className="text-center mb-8">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-medium mb-4" style={{ background: 'var(--t-surface2)', color: 'var(--t-primary)' }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
                    {activeProvider === 'claude' ? 'Claude' : 'Gemini'} ready
                  </div>
                  <h1 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--t-text)' }}>
                    What can I help you build?
                  </h1>
                  <p className="text-sm mt-2" style={{ color: 'var(--t-muted)' }}>
                    Dual-model AI with 33 agents, 30 tools, 57 knowledge graphs, and persistent memory.
                  </p>
                </div>

                {/* Capability cards */}
                <div className="grid grid-cols-2 gap-2 mb-6">
                  {[
                    { icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4', label: 'Code', desc: 'Write, review & refactor', path: '/coding' },
                    { icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z', label: '33 Agents', desc: 'Autonomous workflows', path: '/agents' },
                    { icon: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101', label: '57 KGs', desc: 'Graph-RAG search', path: '/kg-studio' },
                    { icon: 'M11.42 15.17l-5.384 3.18.96-5.593L2.7 8.574l5.61-.814L11.42 2.5l2.507 5.26 5.61.814-4.296 4.183.96 5.593z', label: '30 Tools', desc: 'Cost, code & ML', path: '/tools' },
                  ].map(card => (
                    <button
                      key={card.label}
                      className="t-btn text-left p-3 rounded-lg border transition-all"
                      style={{ borderColor: 'var(--t-border)', background: 'var(--t-surface)' }}
                      onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--t-primary)'}
                      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--t-border)'}
                      onClick={() => navigate(card.path)}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <svg className="h-4 w-4" style={{ color: 'var(--t-primary)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d={card.icon} />
                        </svg>
                        <span className="text-xs font-semibold" style={{ color: 'var(--t-text)' }}>{card.label}</span>
                      </div>
                      <p className="text-[11px]" style={{ color: 'var(--t-muted)' }}>{card.desc}</p>
                    </button>
                  ))}
                </div>

                {/* Quick prompts */}
                <div className="space-y-1.5">
                  <p className="text-[10px] font-medium uppercase tracking-wider mb-2" style={{ color: 'var(--t-muted)' }}>Try asking</p>
                  {[
                    'Review this code for security issues and performance',
                    'Build me a REST API with auth and database',
                    'What tools should I use to reduce my API costs by 90%?',
                    'Analyze my project architecture and suggest improvements',
                  ].map(suggestion => (
                    <button
                      key={suggestion}
                      onClick={() => { setPrompt(suggestion); }}
                      className="t-btn w-full text-left px-3 py-2 rounded-lg border text-xs transition-all"
                      style={{ borderColor: 'var(--t-border)', color: 'var(--t-text2)', background: 'transparent' }}
                      onMouseEnter={e => { e.currentTarget.style.background = 'var(--t-surface)'; e.currentTarget.style.borderColor = 'var(--t-primary)'; }}
                      onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'var(--t-border)'; }}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>

                {/* Footer stats */}
                <div className="flex justify-center gap-4 mt-6 text-[10px]" style={{ color: 'var(--t-muted)', opacity: 0.6 }}>
                  <span>Memory-enabled</span>
                  <span>|</span>
                  <span>53 Playbooks</span>
                  <span>|</span>
                  <span>5 Themes</span>
                </div>
              </div>
            )}
            {messages.map(msg => <MessageItem key={msg.id} message={msg} />)}
            {isLoading && <LoadingIndicator text={statusText} />}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="p-3 border-t" style={{ background: 'var(--t-bg)', borderColor: 'var(--t-border)' }}>
          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <input
              type="text"
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              placeholder={mode === 'coding' ? 'Ask about code...' : 'Ask anything...'}
              className="w-full p-3 rounded-lg focus:outline-none focus:ring-2 text-sm"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', '--tw-ring-color': 'var(--t-primary)' } as React.CSSProperties}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !prompt.trim()}
              className="t-btn p-3 rounded-lg transition-colors min-w-11 min-h-11 flex items-center justify-center"
              style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
            </button>
          </form>
        </div>
      </div>
    </main>
  );
};

export default ChatPanel;
