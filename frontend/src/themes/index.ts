/** Theme system — 5 preset themes with CSS custom property maps. */

export type ThemeId = 'default' | 'crt' | 'scratch' | 'solarized' | 'sunset';

export interface ThemeDefinition {
  id: ThemeId;
  name: string;
  description: string;
  vars: Record<string, string>;
  /** data-theme attribute value for special CSS effects (scanlines, etc.) */
  dataTheme: string;
  /** Preview swatch colors shown in the switcher */
  swatches: string[];
}

const themes: Record<ThemeId, ThemeDefinition> = {
  /* ── 1. Default — Slate dark ─────────────────────────── */
  default: {
    id: 'default',
    name: 'Default',
    description: 'Clean dark slate with sky-blue accents',
    dataTheme: 'default',
    swatches: ['#111827', '#1f2937', '#0ea5e9', '#38bdf8', '#f1f5f9'],
    vars: {
      '--t-bg':       '#111827',
      '--t-surface':  '#1f2937',
      '--t-surface2': '#374151',
      '--t-border':   '#374151',
      '--t-primary':  '#0ea5e9',
      '--t-primary-h':'#38bdf8',
      '--t-accent1':  '#a78bfa',
      '--t-accent2':  '#f472b6',
      '--t-text':     '#f1f5f9',
      '--t-text2':    '#cbd5e1',
      '--t-muted':    '#6b7280',
      '--t-success':  '#22c55e',
      '--t-warning':  '#f59e0b',
      '--t-error':    '#ef4444',
      '--t-font':     "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      '--t-font-mono':"'Menlo', 'Monaco', 'Courier New', monospace",
      '--t-radius':   '0.5rem',
    },
  },

  /* ── 2. Deluxe-CRT — Amber phosphor, subtle scanlines ── */
  crt: {
    id: 'crt',
    name: 'Deluxe-CRT',
    description: 'Retro terminal with amber glow and subtle scanlines',
    dataTheme: 'crt',
    swatches: ['#0a0a08', '#1a1810', '#ffb000', '#ff8c00', '#ffe4b0'],
    vars: {
      '--t-bg':       '#0a0a08',
      '--t-surface':  '#1a1810',
      '--t-surface2': '#2a2818',
      '--t-border':   '#3a3520',
      '--t-primary':  '#ffb000',
      '--t-primary-h':'#ffc840',
      '--t-accent1':  '#ff8c00',
      '--t-accent2':  '#66bb6a',
      '--t-text':     '#ffe4b0',
      '--t-text2':    '#ccb880',
      '--t-muted':    '#7a7050',
      '--t-success':  '#66bb6a',
      '--t-warning':  '#ffb000',
      '--t-error':    '#ff5533',
      '--t-font':     "'Courier New', 'Lucida Console', monospace",
      '--t-font-mono':"'Courier New', 'Lucida Console', monospace",
      '--t-radius':   '0.25rem',
    },
  },

  /* ── 3. Scratch — B&W pen doodle / hand-drawn ─────────── */
  scratch: {
    id: 'scratch',
    name: 'Scratch',
    description: 'Black & white pen doodle, hand-drawn sketchbook feel',
    dataTheme: 'scratch',
    swatches: ['#fafaf8', '#f0efe8', '#1a1a1a', '#555555', '#e8e8e0'],
    vars: {
      '--t-bg':       '#fafaf8',
      '--t-surface':  '#f0efe8',
      '--t-surface2': '#e8e8e0',
      '--t-border':   '#1a1a1a',
      '--t-primary':  '#1a1a1a',
      '--t-primary-h':'#333333',
      '--t-accent1':  '#555555',
      '--t-accent2':  '#888888',
      '--t-text':     '#1a1a1a',
      '--t-text2':    '#333333',
      '--t-muted':    '#888888',
      '--t-success':  '#2d5a2d',
      '--t-warning':  '#8a6d00',
      '--t-error':    '#8a2d2d',
      '--t-font':     "'Patrick Hand', 'Comic Neue', 'Segoe Print', cursive, sans-serif",
      '--t-font-mono':"'Courier New', monospace",
      '--t-radius':   '0px',
    },
  },

  /* ── 4. Solarized Zen — Warm, eye-friendly ────────────── */
  solarized: {
    id: 'solarized',
    name: 'Solarized Zen',
    description: 'Warm earth tones with teal & amber — easy on the eyes',
    dataTheme: 'solarized',
    swatches: ['#002b36', '#073642', '#2aa198', '#b58900', '#eee8d5'],
    vars: {
      '--t-bg':       '#002b36',
      '--t-surface':  '#073642',
      '--t-surface2': '#0a4050',
      '--t-border':   '#586e75',
      '--t-primary':  '#2aa198',
      '--t-primary-h':'#35c4ba',
      '--t-accent1':  '#b58900',
      '--t-accent2':  '#cb4b16',
      '--t-text':     '#eee8d5',
      '--t-text2':    '#93a1a1',
      '--t-muted':    '#657b83',
      '--t-success':  '#859900',
      '--t-warning':  '#b58900',
      '--t-error':    '#dc322f',
      '--t-font':     "system-ui, -apple-system, sans-serif",
      '--t-font-mono':"'Menlo', 'Monaco', 'Courier New', monospace",
      '--t-radius':   '0.375rem',
    },
  },

  /* ── 5. Sunset Warm — Coral, amber, rose gold ──────────── */
  sunset: {
    id: 'sunset',
    name: 'Sunset Warm',
    description: 'Coral, amber & rose gold on dark warm charcoal',
    dataTheme: 'sunset',
    swatches: ['#1a1218', '#2a1f25', '#ff6b6b', '#ffa94d', '#ffeef0'],
    vars: {
      '--t-bg':       '#1a1218',
      '--t-surface':  '#2a1f25',
      '--t-surface2': '#3a2f35',
      '--t-border':   '#4a3540',
      '--t-primary':  '#ff6b6b',
      '--t-primary-h':'#ff8a8a',
      '--t-accent1':  '#ffa94d',
      '--t-accent2':  '#e8a0bf',
      '--t-text':     '#ffeef0',
      '--t-text2':    '#d4b0b8',
      '--t-muted':    '#8a7080',
      '--t-success':  '#7bc67b',
      '--t-warning':  '#ffa94d',
      '--t-error':    '#ff4757',
      '--t-font':     "system-ui, -apple-system, sans-serif",
      '--t-font-mono':"'Menlo', 'Monaco', 'Courier New', monospace",
      '--t-radius':   '0.5rem',
    },
  },
};

export const THEME_LIST: ThemeDefinition[] = Object.values(themes);
export const getTheme = (id: ThemeId): ThemeDefinition => themes[id] || themes.default;
export default themes;
