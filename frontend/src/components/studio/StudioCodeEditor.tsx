/** StudioCodeEditor — Textarea-based code editor with line numbers */
import React, { useCallback, useRef, useEffect } from 'react';
import { useStudio } from '../../context/StudioContext';
import StudioEditorTabs from './StudioEditorTabs';

const StudioCodeEditor: React.FC = () => {
  const { files, activeTab, updateFile } = useStudio();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  const currentFile = activeTab ? files[activeTab] : null;

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (activeTab) {
      updateFile(activeTab, e.target.value);
    }
  }, [activeTab, updateFile]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = e.currentTarget;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const value = textarea.value;
      const newValue = value.substring(0, start) + '  ' + value.substring(end);
      if (activeTab) updateFile(activeTab, newValue);
      requestAnimationFrame(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 2;
      });
    }
    // Bracket auto-close
    const pairs: Record<string, string> = { '(': ')', '{': '}', '[': ']', "'": "'", '"': '"', '`': '`' };
    if (pairs[e.key]) {
      const textarea = e.currentTarget;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      if (start === end) {
        e.preventDefault();
        const value = textarea.value;
        const newValue = value.substring(0, start) + e.key + pairs[e.key] + value.substring(end);
        if (activeTab) updateFile(activeTab, newValue);
        requestAnimationFrame(() => {
          textarea.selectionStart = textarea.selectionEnd = start + 1;
        });
      }
    }
    // Enter key: auto-indent
    if (e.key === 'Enter') {
      const textarea = e.currentTarget;
      const start = textarea.selectionStart;
      const value = textarea.value;
      const lineStart = value.lastIndexOf('\n', start - 1) + 1;
      const currentLine = value.substring(lineStart, start);
      const indentMatch = currentLine.match(/^(\s*)/);
      const indent = indentMatch ? indentMatch[1] : '';
      const lastChar = value[start - 1];
      const extraIndent = lastChar === '{' || lastChar === '(' || lastChar === '[' ? '  ' : '';

      if (extraIndent) {
        e.preventDefault();
        const newValue = value.substring(0, start) + '\n' + indent + extraIndent + value.substring(start);
        if (activeTab) updateFile(activeTab, newValue);
        requestAnimationFrame(() => {
          const pos = start + 1 + indent.length + extraIndent.length;
          textarea.selectionStart = textarea.selectionEnd = pos;
        });
      }
    }
  }, [activeTab, updateFile]);

  // Sync scroll between line numbers and textarea
  const handleScroll = useCallback(() => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  }, []);

  // Focus textarea when active tab changes
  useEffect(() => {
    if (activeTab && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [activeTab]);

  const lineCount = currentFile ? currentFile.content.split('\n').length : 0;

  const getLanguageLabel = (path: string): string => {
    const ext = path.split('.').pop()?.toLowerCase() || '';
    const labels: Record<string, string> = {
      tsx: 'TypeScript JSX', ts: 'TypeScript', jsx: 'JavaScript JSX', js: 'JavaScript',
      css: 'CSS', html: 'HTML', json: 'JSON', md: 'Markdown', py: 'Python',
      sql: 'SQL', yaml: 'YAML', yml: 'YAML', txt: 'Plain Text',
    };
    return labels[ext] || ext.toUpperCase();
  };

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Tabs */}
      <StudioEditorTabs />

      {/* File info bar */}
      {currentFile && activeTab && (
        <div
          className="flex items-center justify-between px-3 h-6 flex-shrink-0"
          style={{ background: 'var(--t-surface2)', borderBottom: '1px solid var(--t-border)' }}
        >
          <span className="text-xs truncate" style={{ color: 'var(--t-muted)', fontFamily: 'var(--t-font-mono)' }}>
            {activeTab}
          </span>
          <span className="text-xs flex-shrink-0 ml-2" style={{ color: 'var(--t-muted)' }}>
            {getLanguageLabel(activeTab)} &middot; {lineCount} lines
          </span>
        </div>
      )}

      {/* Editor */}
      {currentFile ? (
        <div className="flex-1 flex overflow-hidden relative">
          {/* Line numbers */}
          <div
            ref={lineNumbersRef}
            className="flex-shrink-0 text-right pr-2 pt-2 select-none overflow-hidden"
            style={{
              width: 48,
              background: 'var(--t-surface)',
              color: 'var(--t-muted)',
              fontFamily: 'var(--t-font-mono)',
              fontSize: 13,
              lineHeight: '1.5',
              borderRight: '1px solid var(--t-border)',
            }}
          >
            {Array.from({ length: lineCount }, (_, i) => (
              <div key={i} style={{ height: '1.5em' }}>{i + 1}</div>
            ))}
          </div>

          {/* Code textarea */}
          <textarea
            ref={textareaRef}
            value={currentFile.content}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onScroll={handleScroll}
            spellCheck={false}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            className="flex-1 resize-none p-2 outline-none"
            style={{
              background: 'var(--t-bg)',
              color: 'var(--t-text)',
              fontFamily: 'var(--t-font-mono)',
              fontSize: 13,
              lineHeight: '1.5',
              tabSize: 2,
              border: 'none',
              caretColor: 'var(--t-primary)',
            }}
          />
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1} style={{ color: 'var(--t-muted)' }}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          <p className="text-sm" style={{ color: 'var(--t-muted)' }}>
            Select a file from the tree to edit
          </p>
          <p className="text-xs" style={{ color: 'var(--t-muted)', opacity: 0.6 }}>
            Or switch to Chat mode to generate code
          </p>
        </div>
      )}
    </div>
  );
};

export default StudioCodeEditor;
