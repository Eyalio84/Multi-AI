/** StudioNewFileDialog — Modal for creating a new file */
import React, { useState, useRef, useEffect } from 'react';
import { useStudio } from '../../context/StudioContext';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const StudioNewFileDialog: React.FC<Props> = ({ isOpen, onClose }) => {
  const { addFile, openFile } = useStudio();
  const [filePath, setFilePath] = useState('');
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setFilePath('');
      setError('');
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCreate = () => {
    const trimmed = filePath.trim();
    if (!trimmed) {
      setError('File path is required');
      return;
    }
    if (!trimmed.includes('.')) {
      setError('File must have an extension (e.g. .tsx, .css)');
      return;
    }
    const cleanPath = trimmed.startsWith('/') ? trimmed.slice(1) : trimmed;
    addFile(cleanPath, '');
    openFile(cleanPath);
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleCreate();
    if (e.key === 'Escape') onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.5)' }}
      onClick={onClose}
    >
      <div
        className="rounded-lg p-4 w-full max-w-sm shadow-xl"
        style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-sm font-medium mb-3" style={{ color: 'var(--t-text)' }}>New File</h3>

        <input
          ref={inputRef}
          type="text"
          value={filePath}
          onChange={e => { setFilePath(e.target.value); setError(''); }}
          onKeyDown={handleKeyDown}
          placeholder="e.g. src/components/Button.tsx"
          className="w-full px-3 py-2 rounded text-sm outline-none mb-1"
          style={{
            background: 'var(--t-bg)',
            color: 'var(--t-text)',
            border: `1px solid ${error ? 'var(--t-error)' : 'var(--t-border)'}`,
            fontFamily: 'var(--t-font-mono)',
          }}
        />

        {error && (
          <p className="text-xs mb-2" style={{ color: 'var(--t-error)' }}>{error}</p>
        )}

        <div className="flex justify-end gap-2 mt-3">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded text-xs transition-colors"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            className="px-3 py-1.5 rounded text-xs font-medium transition-colors"
            style={{ background: 'var(--t-primary)', color: '#fff' }}
          >
            Create
          </button>
        </div>
      </div>
    </div>
  );
};

export default StudioNewFileDialog;
