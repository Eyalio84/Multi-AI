import { useState, useEffect, useCallback } from 'react';
import { ThemeId, getTheme } from '../themes/index';

const THEME_STORAGE_KEY = 'workspace_theme';

function loadSavedTheme(): ThemeId {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    if (saved && ['default', 'crt', 'scratch', 'solarized', 'sunset'].includes(saved)) {
      return saved as ThemeId;
    }
  } catch {}
  return 'default';
}

function applyTheme(id: ThemeId) {
  const theme = getTheme(id);
  const root = document.documentElement;

  // Set all CSS custom properties
  for (const [prop, value] of Object.entries(theme.vars)) {
    root.style.setProperty(prop, value);
  }

  // Set data-theme for special effect selectors (CRT scanlines, scratch borders)
  root.setAttribute('data-theme', theme.dataTheme);

  // Persist
  try { localStorage.setItem(THEME_STORAGE_KEY, id); } catch {}
}

export function useTheme() {
  const [themeId, setThemeId] = useState<ThemeId>(loadSavedTheme);

  // Apply on mount and when themeId changes
  useEffect(() => {
    applyTheme(themeId);
  }, [themeId]);

  const switchTheme = useCallback((id: ThemeId) => {
    setThemeId(id);
  }, []);

  return { themeId, switchTheme, theme: getTheme(themeId) };
}
