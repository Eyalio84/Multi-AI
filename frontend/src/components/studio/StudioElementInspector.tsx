/** StudioElementInspector — Selected element props/styles editor */
import React, { useState, useEffect, useCallback } from 'react';
import { useStudio } from '../../context/StudioContext';

interface StyleField {
  key: string;
  label: string;
  type: 'text' | 'color' | 'number';
  unit?: string;
}

const STYLE_FIELDS: StyleField[] = [
  { key: 'color', label: 'Color', type: 'color' },
  { key: 'backgroundColor', label: 'Background', type: 'color' },
  { key: 'fontSize', label: 'Font Size', type: 'number', unit: 'px' },
  { key: 'fontWeight', label: 'Font Weight', type: 'text' },
  { key: 'padding', label: 'Padding', type: 'text' },
  { key: 'margin', label: 'Margin', type: 'text' },
  { key: 'borderRadius', label: 'Border Radius', type: 'text' },
  { key: 'border', label: 'Border', type: 'text' },
  { key: 'width', label: 'Width', type: 'text' },
  { key: 'height', label: 'Height', type: 'text' },
  { key: 'display', label: 'Display', type: 'text' },
  { key: 'gap', label: 'Gap', type: 'text' },
];

const StudioElementInspector: React.FC = () => {
  const { selectedElement, setSelectedElement, sendMessage, isStreaming, files, updateFile } = useStudio();
  const [editedStyles, setEditedStyles] = useState<Record<string, string>>({});
  const [editedText, setEditedText] = useState('');
  const [showAllProps, setShowAllProps] = useState(false);

  // Reset edited values when selected element changes
  useEffect(() => {
    if (selectedElement) {
      setEditedStyles(selectedElement.styles || {});
      setEditedText(selectedElement.text || '');
    } else {
      setEditedStyles({});
      setEditedText('');
    }
  }, [selectedElement]);

  const handleStyleChange = useCallback((key: string, value: string) => {
    setEditedStyles(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleApplyStyles = useCallback(async () => {
    if (!selectedElement || isStreaming) return;

    const changedStyles = Object.entries(editedStyles)
      .filter(([k, v]) => v !== (selectedElement.styles?.[k] || ''))
      .map(([k, v]) => `${k}: ${v}`)
      .join(', ');

    const textChanged = editedText !== (selectedElement.text || '');

    if (!changedStyles && !textChanged) return;

    let prompt = `[Visual Mode - Apply changes to ${selectedElement.componentName} <${selectedElement.elementTag}> in ${selectedElement.filePath}`;
    if (selectedElement.lineNumber) prompt += ` line ${selectedElement.lineNumber}`;
    prompt += ']\n\n';

    if (changedStyles) {
      prompt += `Update styles: ${changedStyles}\n`;
    }
    if (textChanged) {
      prompt += `Update text content to: "${editedText}"\n`;
    }

    await sendMessage(prompt);
  }, [selectedElement, editedStyles, editedText, sendMessage, isStreaming]);

  const handleClearSelection = () => {
    setSelectedElement(null);
  };

  if (!selectedElement) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4 gap-3">
        <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1} style={{ color: 'var(--t-muted)' }}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.042 21.672L13.684 16.6m0 0l-2.51 2.225.569-9.47 5.227 7.917-3.286-.672zM12 2.25V4.5m5.834.166l-1.591 1.591M20.25 10.5H18M7.757 14.743l-1.59 1.59M6 10.5H3.75m4.007-4.243l-1.59-1.59" />
        </svg>
        <p className="text-xs text-center" style={{ color: 'var(--t-muted)' }}>
          Click on an element in the preview to inspect and edit its properties
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Element info header */}
      <div
        className="flex items-center justify-between px-3 py-2 flex-shrink-0"
        style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
      >
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium" style={{ color: 'var(--t-primary)' }}>
              {selectedElement.componentName}
            </span>
            <span className="text-xs" style={{ color: 'var(--t-muted)' }}>
              &lt;{selectedElement.elementTag}&gt;
            </span>
          </div>
          {selectedElement.filePath && (
            <div className="text-xs truncate mt-0.5" style={{ color: 'var(--t-muted)', fontFamily: 'var(--t-font-mono)' }}>
              {selectedElement.filePath}
              {selectedElement.lineNumber && `:${selectedElement.lineNumber}`}
            </div>
          )}
        </div>
        <button
          onClick={handleClearSelection}
          className="p-1 rounded hover:opacity-80 flex-shrink-0"
          style={{ color: 'var(--t-muted)' }}
          title="Clear selection"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Text content */}
        {selectedElement.text !== undefined && (
          <div>
            <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--t-text2)' }}>Text Content</label>
            <textarea
              value={editedText}
              onChange={e => setEditedText(e.target.value)}
              rows={2}
              className="w-full px-2 py-1.5 rounded text-xs outline-none resize-none"
              style={{
                background: 'var(--t-surface)',
                color: 'var(--t-text)',
                border: '1px solid var(--t-border)',
                fontFamily: 'var(--t-font)',
              }}
            />
          </div>
        )}

        {/* Style fields */}
        <div>
          <label className="text-xs font-medium mb-2 block" style={{ color: 'var(--t-text2)' }}>Styles</label>
          <div className="space-y-2">
            {STYLE_FIELDS.map(field => (
              <div key={field.key} className="flex items-center gap-2">
                <label
                  className="text-xs flex-shrink-0"
                  style={{ color: 'var(--t-muted)', width: 90 }}
                >
                  {field.label}
                </label>
                <div className="flex-1 flex items-center gap-1">
                  {field.type === 'color' && (
                    <input
                      type="color"
                      value={editedStyles[field.key] || '#000000'}
                      onChange={e => handleStyleChange(field.key, e.target.value)}
                      className="w-6 h-6 rounded cursor-pointer flex-shrink-0"
                      style={{ border: '1px solid var(--t-border)' }}
                    />
                  )}
                  <input
                    type="text"
                    value={editedStyles[field.key] || ''}
                    onChange={e => handleStyleChange(field.key, e.target.value)}
                    placeholder={field.unit ? `e.g. 16${field.unit}` : ''}
                    className="flex-1 px-2 py-1 rounded text-xs outline-none"
                    style={{
                      background: 'var(--t-surface)',
                      color: 'var(--t-text)',
                      border: '1px solid var(--t-border)',
                      fontFamily: 'var(--t-font-mono)',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Props (read-only display) */}
        {selectedElement.props && Object.keys(selectedElement.props).length > 0 && (
          <div>
            <button
              onClick={() => setShowAllProps(!showAllProps)}
              className="flex items-center gap-1 text-xs font-medium mb-1"
              style={{ color: 'var(--t-text2)' }}
            >
              <svg
                className={`w-3 h-3 transition-transform ${showAllProps ? 'rotate-90' : ''}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
              Props ({Object.keys(selectedElement.props).length})
            </button>
            {showAllProps && (
              <div className="space-y-1 ml-3">
                {Object.entries(selectedElement.props).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-2 text-xs">
                    <span style={{ color: 'var(--t-primary)', fontFamily: 'var(--t-font-mono)' }}>{key}</span>
                    <span style={{ color: 'var(--t-muted)' }}>=</span>
                    <span style={{ color: 'var(--t-text)', fontFamily: 'var(--t-font-mono)' }}>
                      {typeof value === 'string' ? `"${value}"` : JSON.stringify(value)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Apply button */}
      <div className="flex-shrink-0 p-3" style={{ borderTop: '1px solid var(--t-border)' }}>
        <button
          onClick={handleApplyStyles}
          disabled={isStreaming}
          className="w-full py-2 rounded text-xs font-medium transition-colors disabled:opacity-40"
          style={{ background: 'var(--t-primary)', color: '#fff' }}
        >
          {isStreaming ? 'Applying...' : 'Apply Changes'}
        </button>
      </div>
    </div>
  );
};

export default StudioElementInspector;
