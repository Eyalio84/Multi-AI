import React, { useState, useRef, useEffect } from 'react';
import { useAppContext } from '../context/AppContext';
import { THEME_LIST, ThemeId } from '../themes/index';

const ThemeSwitcher: React.FC = () => {
  const { themeId, switchTheme } = useAppContext();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="p-1.5 rounded transition-colors"
        style={{ color: 'var(--t-muted)' }}
        title="Switch theme"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
        </svg>
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-56 rounded-lg shadow-xl border z-50 overflow-hidden"
          style={{
            background: 'var(--t-surface)',
            borderColor: 'var(--t-border)',
          }}
        >
          <div className="px-3 py-2 border-b" style={{ borderColor: 'var(--t-border)' }}>
            <span className="text-xs font-semibold" style={{ color: 'var(--t-muted)' }}>THEME</span>
          </div>
          {THEME_LIST.map(t => (
            <button
              key={t.id}
              onClick={() => { switchTheme(t.id as ThemeId); setOpen(false); }}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors"
              style={{
                background: themeId === t.id ? 'var(--t-surface2)' : 'transparent',
                color: 'var(--t-text)',
              }}
              onMouseEnter={e => { if (themeId !== t.id) (e.currentTarget.style.background = 'var(--t-surface2)'); }}
              onMouseLeave={e => { if (themeId !== t.id) (e.currentTarget.style.background = 'transparent'); }}
            >
              {/* Color swatches */}
              <div className="flex gap-0.5 shrink-0">
                {t.swatches.map((c, i) => (
                  <div
                    key={i}
                    className="w-3 h-3 rounded-full border"
                    style={{ background: c, borderColor: i === 0 ? t.swatches[3] || '#666' : 'transparent' }}
                  />
                ))}
              </div>
              {/* Label */}
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium truncate">{t.name}</div>
              </div>
              {/* Check */}
              {themeId === t.id && (
                <svg className="w-4 h-4 shrink-0" style={{ color: 'var(--t-primary)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ThemeSwitcher;
