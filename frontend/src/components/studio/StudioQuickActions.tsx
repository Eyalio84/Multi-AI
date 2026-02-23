/** StudioQuickActions — Quick action buttons for the selected element */
import React from 'react';
import { useStudio } from '../../context/StudioContext';

interface QuickAction {
  label: string;
  icon: string;
  prompt: (componentName: string, elementTag: string, filePath: string) => string;
  color?: string;
}

const ACTIONS: QuickAction[] = [
  {
    label: 'Delete',
    icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16',
    prompt: (name, tag, file) => `[Visual Mode] Delete the <${tag}> element in ${name} component (${file}). Remove it entirely from the JSX.`,
    color: 'var(--t-error)',
  },
  {
    label: 'Duplicate',
    icon: 'M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z',
    prompt: (name, tag, file) => `[Visual Mode] Duplicate the <${tag}> element in ${name} component (${file}). Place the copy right after the original.`,
  },
  {
    label: 'Wrap',
    icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z',
    prompt: (name, tag, file) => `[Visual Mode] Wrap the <${tag}> element in ${name} component (${file}) inside a new <div> container. Keep all existing props and children.`,
  },
  {
    label: 'Edit Text',
    icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
    prompt: (name, tag, file) => `[Visual Mode] I want to change the text content of the <${tag}> element in ${name} component (${file}). Please show me the current text and ask what I want to change it to.`,
  },
  {
    label: 'Add Child',
    icon: 'M12 4v16m8-8H4',
    prompt: (name, tag, file) => `[Visual Mode] Add a new child element inside the <${tag}> element in ${name} component (${file}). Suggest a few options for what to add (paragraph, button, image, etc).`,
  },
  {
    label: 'Style',
    icon: 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01',
    prompt: (name, tag, file) => `[Visual Mode] Restyle the <${tag}> element in ${name} component (${file}). Make it look more modern and polished with improved spacing, colors, and typography.`,
  },
];

const StudioQuickActions: React.FC = () => {
  const { selectedElement, sendMessage, isStreaming } = useStudio();

  if (!selectedElement) return null;

  const handleAction = async (action: QuickAction) => {
    if (isStreaming) return;
    const prompt = action.prompt(
      selectedElement.componentName,
      selectedElement.elementTag,
      selectedElement.filePath,
    );
    await sendMessage(prompt);
  };

  return (
    <div
      className="flex items-center gap-1 px-3 py-1.5 flex-shrink-0 overflow-x-auto"
      style={{ background: 'var(--t-surface)', borderTop: '1px solid var(--t-border)' }}
    >
      <span className="text-xs flex-shrink-0 mr-1" style={{ color: 'var(--t-muted)' }}>Actions:</span>
      {ACTIONS.map(action => (
        <button
          key={action.label}
          onClick={() => handleAction(action)}
          disabled={isStreaming}
          className="flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors hover:opacity-80 disabled:opacity-40 flex-shrink-0"
          style={{
            background: 'var(--t-surface2)',
            color: action.color || 'var(--t-text2)',
            border: '1px solid var(--t-border)',
          }}
          title={action.label}
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d={action.icon} />
          </svg>
          {action.label}
        </button>
      ))}
    </div>
  );
};

export default StudioQuickActions;
