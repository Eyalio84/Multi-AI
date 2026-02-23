import React from 'react';
import { useToastState } from '../hooks/useToast';

const ToastContainer: React.FC = () => {
  const { toasts, dismiss } = useToastState();
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      {toasts.map(t => (
        <div key={t.id}
          className="flex items-start gap-2 px-3 py-2 rounded shadow-lg text-xs animate-fade-in"
          style={{
            background: t.type === 'error' ? '#7f1d1d' : 'var(--t-surface2)',
            color: t.type === 'error' ? '#fca5a5' : 'var(--t-text)',
            border: `1px solid ${t.type === 'error' ? '#991b1b' : 'var(--t-border)'}`,
          }}>
          <span className="flex-1 break-words">{t.message}</span>
          <button onClick={() => dismiss(t.id)} className="flex-shrink-0 opacity-60 hover:opacity-100">&times;</button>
        </div>
      ))}
    </div>
  );
};

export default ToastContainer;
