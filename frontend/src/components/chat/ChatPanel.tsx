import React, { useState, useRef, useEffect } from 'react';
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
              <div className="text-center mt-20" style={{ color: 'var(--t-muted)' }}>
                <p className="text-lg font-medium">Multi-AI Agentic Workspace</p>
                <p className="text-sm mt-2">Chat with Gemini or Claude. Switch models anytime.</p>
                <p className="text-xs mt-4" style={{ color: 'var(--t-muted)', opacity: 0.6 }}>
                  Conversations are now persisted with memory extraction
                </p>
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
