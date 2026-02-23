import { useState, useCallback, useRef } from 'react';

export interface Toast {
  id: number;
  message: string;
  type: 'error' | 'info';
}

let globalToasts: Toast[] = [];
let globalSetToasts: ((t: Toast[]) => void) | null = null;
let nextId = 1;

/** Show a toast from anywhere (no hook needed) */
export function showToast(message: string, type: 'error' | 'info' = 'error') {
  const toast: Toast = { id: nextId++, message, type };
  globalToasts = [...globalToasts, toast];
  globalSetToasts?.(globalToasts);
  setTimeout(() => {
    globalToasts = globalToasts.filter(t => t.id !== toast.id);
    globalSetToasts?.(globalToasts);
  }, 4000);
}

/** Hook for the toast renderer component */
export function useToastState() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  globalSetToasts = setToasts;
  globalToasts = toasts;

  const dismiss = useCallback((id: number) => {
    globalToasts = globalToasts.filter(t => t.id !== id);
    setToasts(globalToasts);
  }, []);

  return { toasts, dismiss };
}
