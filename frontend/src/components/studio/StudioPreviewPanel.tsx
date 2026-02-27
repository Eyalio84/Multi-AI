/** StudioPreviewPanel — SandpackProvider wrapper, dark theme, console, error overlay */
import React, { useMemo, useState } from 'react';
import {
  SandpackProvider,
  SandpackLayout,
  SandpackPreview,
  SandpackConsole,
} from '@codesandbox/sandpack-react';
import { useStudio } from '../../context/StudioContext';

/**
 * Convert HTML string style attributes to JSX object style in generated code.
 * Handles: style="color: red; font-size: 14px" → style={{ color: 'red', fontSize: '14px' }}
 */
function sanitizeStringStyles(code: string): string {
  // Match style="..." or style='...' in JSX (but not already style={{ }})
  return code.replace(
    /style=(["'])([^"']+?)\1/g,
    (_match, _quote, cssString: string) => {
      const props = cssString
        .split(';')
        .map((s: string) => s.trim())
        .filter(Boolean)
        .map((decl: string) => {
          const colonIdx = decl.indexOf(':');
          if (colonIdx === -1) return null;
          const prop = decl.slice(0, colonIdx).trim();
          const val = decl.slice(colonIdx + 1).trim();
          // Convert kebab-case to camelCase
          const camelProp = prop.replace(/-([a-z])/g, (_: string, c: string) => c.toUpperCase());
          // Keep numeric values as numbers, everything else as string
          const isNumeric = /^-?\d+(\.\d+)?(px|em|rem|vh|vw|%)?$/.test(val);
          const numericOnly = /^-?\d+(\.\d+)?$/.test(val);
          if (numericOnly) return `${camelProp}: ${val}`;
          return `${camelProp}: '${val.replace(/'/g, "\\'")}'`;
        })
        .filter(Boolean)
        .join(', ');
      return `style={{ ${props} }}`;
    }
  );
}

/**
 * Packages that break in Sandpack's browser bundler (Node.js subpath imports,
 * native modules, etc.). Instead of npm-installing them, we inject lightweight
 * shim modules so the generated code runs without changes.
 */
const SANDPACK_SHIMS: Record<string, string> = {
  'react-markdown': `import React from 'react';
function SimpleMarkdown({ children }) {
  if (!children) return null;
  const html = String(children)
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
    .replace(/\\*(.+?)\\*/g, '<em>$1</em>')
    .replace(/\`\`\`[\\s\\S]*?\`\`\`/g, (m) => '<pre style="background:#1e293b;color:#e2e8f0;padding:12px;border-radius:6px;overflow-x:auto;font-size:13px"><code>' + m.slice(m.indexOf('\\n')+1, m.lastIndexOf('\\n')) + '</code></pre>')
    .replace(/\`([^\`]+)\`/g, '<code style="background:#1e293b;color:#38bdf8;padding:2px 5px;border-radius:3px;font-size:0.9em">$1</code>')
    .replace(/^[\\-\\*] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\\/li>)/s, '<ul>$1</ul>')
    .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" style="color:#38bdf8">$1</a>')
    .replace(/\\n\\n/g, '<br/><br/>')
    .replace(/\\n/g, '<br/>');
  return React.createElement('div', { dangerouslySetInnerHTML: { __html: html } });
}
export default SimpleMarkdown;`,

  'remark-gfm': `export default function remarkGfm() { return (tree) => tree; }`,
  'remark-math': `export default function remarkMath() { return (tree) => tree; }`,
  'rehype-highlight': `export default function rehypeHighlight() { return (tree) => tree; }`,
  'rehype-katex': `export default function rehypeKatex() { return (tree) => tree; }`,
  'rehype-raw': `export default function rehypeRaw() { return (tree) => tree; }`,
  'react-syntax-highlighter': `import React from 'react';
export function Prism({ children, language, style, ...props }) {
  return React.createElement('pre', { style: { background: '#1e293b', color: '#e2e8f0', padding: '16px', borderRadius: '8px', overflow: 'auto', fontSize: '13px', ...(style || {}) } },
    React.createElement('code', null, children)
  );
}
export function Light({ children, ...props }) { return Prism({ children, ...props }); }
export default Prism;`,
  'react-syntax-highlighter/dist/esm/styles/prism': `export const oneDark = {}; export const vscDarkPlus = {}; export const materialDark = {}; export default oneDark;`,
  'react-syntax-highlighter/dist/cjs/styles/prism': `export const oneDark = {}; export const vscDarkPlus = {}; export const materialDark = {}; export default oneDark;`,
  'react-syntax-highlighter/dist/esm/styles/hljs': `export const docco = {}; export const dark = {}; export default docco;`,

  'react-icons/fi': `import React from 'react';
const icon = (d) => (props) => React.createElement('svg', { viewBox: '0 0 24 24', width: '1em', height: '1em', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', ...props }, React.createElement('path', { d }));
export const FiSearch = icon('M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z');
export const FiPlus = icon('M12 5v14M5 12h14');
export const FiTrash = icon('M3 6h18M8 6V4h8v2m1 0v14H7V6');
export const FiEdit = icon('M11 4H4v16h16v-7M18.5 2.5l3 3L12 15H9v-3z');
export const FiSave = icon('M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z');
export const FiX = icon('M18 6L6 18M6 6l12 12');
export const FiCheck = icon('M20 6L9 17l-5-5');
export const FiMenu = icon('M3 12h18M3 6h18M3 18h18');
export const FiHome = icon('M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z');
export const FiSettings = icon('M12 15a3 3 0 100-6 3 3 0 000 6z');
export const FiUser = icon('M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 3a4 4 0 100 8 4 4 0 000-8z');
export const FiLogOut = icon('M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9');
export const FiStar = icon('M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z');
export const FiHeart = icon('M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 000-7.78z');
export const FiMoon = icon('M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z');
export const FiSun = icon('M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42');
export const FiChevronDown = icon('M6 9l6 6 6-6');
export const FiChevronRight = icon('M9 18l6-6-6-6');
export const FiFolder = icon('M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z');
export const FiFile = icon('M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z');
export const FiCopy = icon('M20 9h-9a2 2 0 00-2 2v9a2 2 0 002 2h9a2 2 0 002-2v-9a2 2 0 00-2-2zM5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1');
export const FiDownload = icon('M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3');
export const FiUpload = icon('M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12');
export const FiRefreshCw = icon('M23 4v6h-6M1 20v-6h6');
export const FiArrowLeft = icon('M19 12H5M12 19l-7-7 7-7');
export const FiArrowRight = icon('M5 12h14M12 5l7 7-7 7');
export const FiBell = icon('M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0');
export const FiFilter = icon('M22 3H2l8 9.46V19l4 2v-8.54L22 3z');
export const FiTag = icon('M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z');
export const FiClock = icon('M12 22a10 10 0 100-20 10 10 0 000 20zM12 6v6l4 2');
export const FiEye = icon('M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z');
export const FiLink = icon('M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71');
export const FiExternalLink = icon('M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3');`,

  'react-icons/fa': `import React from 'react';
const icon = (d) => (props) => React.createElement('svg', { viewBox: '0 0 24 24', width: '1em', height: '1em', fill: 'currentColor', ...props }, React.createElement('path', { d }));
export const FaBars = icon('M3 12h18M3 6h18M3 18h18');
export const FaTimes = icon('M18 6L6 18M6 6l12 12');
export const FaCheck = icon('M20 6L9 17l-5-5');
export const FaPlus = icon('M12 5v14M5 12h14');
export const FaSearch = icon('M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z');
export const FaTrash = icon('M3 6h18M8 6V4h8v2m1 0v14H7V6');
export const FaEdit = icon('M11 4H4v16h16v-7M18.5 2.5l3 3L12 15H9v-3z');
export const FaStar = icon('M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z');
export const FaHeart = icon('M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 000-7.78z');
export const FaUser = icon('M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 3a4 4 0 100 8 4 4 0 000-8z');
export const FaHome = icon('M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z');`,

  'react-icons/md': `import React from 'react';
const icon = (d) => (props) => React.createElement('svg', { viewBox: '0 0 24 24', width: '1em', height: '1em', fill: 'currentColor', ...props }, React.createElement('path', { d }));
export const MdDelete = icon('M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z');
export const MdEdit = icon('M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 000-1.41l-2.34-2.34a1 1 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z');
export const MdAdd = icon('M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z');
export const MdClose = icon('M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z');
export const MdSearch = icon('M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z');
export const MdSettings = icon('M19.14 12.94a7.07 7.07 0 000-1.88l2.03-1.58a.49.49 0 00.12-.61l-1.92-3.32a.49.49 0 00-.59-.22l-2.39.96a7.04 7.04 0 00-1.62-.94l-.36-2.54a.48.48 0 00-.48-.41h-3.84a.48.48 0 00-.48.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96a.49.49 0 00-.59.22L2.74 8.87a.48.48 0 00.12.61l2.03 1.58a7.07 7.07 0 000 1.88l-2.03 1.58a.49.49 0 00-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.37 1.03.7 1.62.94l.36 2.54c.05.24.26.41.48.41h3.84c.24 0 .44-.17.48-.41l.36-2.54c.59-.24 1.13-.57 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32a.49.49 0 00-.12-.61l-2.03-1.58zM12 15.6A3.6 3.6 0 1115.6 12 3.6 3.6 0 0112 15.6z');`,

  'lucide-react': `import React from 'react';
const icon = (d) => React.forwardRef(({ size = 24, color = 'currentColor', strokeWidth = 2, ...props }, ref) =>
  React.createElement('svg', { ref, xmlns: 'http://www.w3.org/2000/svg', width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: color, strokeWidth, strokeLinecap: 'round', strokeLinejoin: 'round', ...props },
    React.createElement('path', { d })));
export const Search = icon('M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z');
export const Plus = icon('M12 5v14M5 12h14');
export const Trash2 = icon('M3 6h18M8 6V4h8v2m1 0v14H7V6');
export const Edit = icon('M11 4H4v16h16v-7M18.5 2.5l3 3L12 15H9v-3z');
export const Save = icon('M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z');
export const X = icon('M18 6L6 18M6 6l12 12');
export const Check = icon('M20 6L9 17l-5-5');
export const Menu = icon('M3 12h18M3 6h18M3 18h18');
export const Home = icon('M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z');
export const Settings = icon('M12 15a3 3 0 100-6 3 3 0 000 6z');
export const User = icon('M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 3a4 4 0 100 8 4 4 0 000-8z');
export const LogOut = icon('M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9');
export const Star = icon('M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z');
export const Heart = icon('M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 000-7.78z');
export const Moon = icon('M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z');
export const Sun = icon('M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42');
export const ChevronDown = icon('M6 9l6 6 6-6');
export const ChevronRight = icon('M9 18l6-6-6-6');
export const ChevronLeft = icon('M15 18l-6-6 6-6');
export const ChevronUp = icon('M18 15l-6-6-6 6');
export const ArrowLeft = icon('M19 12H5M12 19l-7-7 7-7');
export const ArrowRight = icon('M5 12h14M12 5l7 7-7 7');
export const Copy = icon('M20 9h-9a2 2 0 00-2 2v9a2 2 0 002 2h9a2 2 0 002-2v-9a2 2 0 00-2-2zM5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1');
export const Download = icon('M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3');
export const Upload = icon('M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12');
export const RefreshCw = icon('M23 4v6h-6M1 20v-6h6');
export const Bell = icon('M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0');
export const Filter = icon('M22 3H2l8 9.46V19l4 2v-8.54L22 3z');
export const Tag = icon('M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z');
export const Clock = icon('M12 22a10 10 0 100-20 10 10 0 000 20zM12 6v6l4 2');
export const Eye = icon('M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z');
export const EyeOff = icon('M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M1 1l22 22');
export const Link = icon('M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71');
export const ExternalLink = icon('M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3');
export const Folder = icon('M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z');
export const File = icon('M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z');
export const AlertCircle = icon('M12 22a10 10 0 100-20 10 10 0 000 20zM12 8v4M12 16h.01');
export const Info = icon('M12 22a10 10 0 100-20 10 10 0 000 20zM12 16v-4M12 8h.01');
export const Loader = icon('M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83');
export const MoreHorizontal = icon('M12 13a1 1 0 100-2 1 1 0 000 2zM19 13a1 1 0 100-2 1 1 0 000 2zM5 13a1 1 0 100-2 1 1 0 000 2z');
export const MoreVertical = icon('M12 13a1 1 0 100-2 1 1 0 000 2zM12 6a1 1 0 100-2 1 1 0 000 2zM12 20a1 1 0 100-2 1 1 0 000 2z');
export const Maximize2 = icon('M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7');
export const Minimize2 = icon('M4 14h6v6M20 10h-6V4M14 10l7-7M3 21l7-7');
export const Send = icon('M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z');
export const Trash = icon('M3 6h18M8 6V4h8v2m1 0v14H7V6');
export const Mail = icon('M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6');
export const MessageSquare = icon('M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z');
export const Image = icon('M21 19V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2zM8.5 10a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM21 15l-5-5L5 21');
export const Calendar = icon('M19 4H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2zM16 2v4M8 2v4M3 10h18');
export const Bookmark = icon('M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z');
export const Share2 = icon('M18 8a3 3 0 100-6 3 3 0 000 6zM6 15a3 3 0 100-6 3 3 0 000 6zM18 22a3 3 0 100-6 3 3 0 000 6zM8.59 13.51l6.83 3.98M15.41 6.51l-6.82 3.98');
export const Zap = icon('M13 2L3 14h9l-1 10 10-12h-9l1-10z');
export const Globe = icon('M12 22a10 10 0 100-20 10 10 0 000 20zM2 12h20');`,
};

/** Check if a module path matches a shimmed package */
function getShimKey(importPath: string): string | null {
  if (SANDPACK_SHIMS[importPath]) return importPath;
  // Check parent package (e.g. 'react-icons/fi' → check 'react-icons/fi')
  // For sub-paths like 'react-syntax-highlighter/dist/esm/styles/prism'
  for (const key of Object.keys(SANDPACK_SHIMS)) {
    if (importPath === key || importPath.startsWith(key + '/')) {
      return SANDPACK_SHIMS[importPath] ? importPath : key;
    }
  }
  return null;
}

const StudioPreviewPanel: React.FC = () => {
  const { files, mode } = useStudio();
  const [showConsole, setShowConsole] = useState(false);

  // Collect all imports to determine which shims are needed
  const detectedImports = useMemo(() => {
    const imports = new Set<string>();
    const importRe = /(?:import\s+[\s\S]*?from\s+|import\s+)['"]([^./'"@][^'"]*|@[^/'"]+\/[^'"]+)['"]/g;
    for (const [path, file] of Object.entries(files)) {
      if (!/\.(jsx?|tsx?)$/.test(path)) continue;
      let match: RegExpExecArray | null;
      while ((match = importRe.exec(file.content)) !== null) {
        imports.add(match[1]);
      }
    }
    return imports;
  }, [files]);

  // Convert studio files to Sandpack file format
  const sandpackFiles = useMemo(() => {
    const result: Record<string, { code: string; active?: boolean }> = {};

    const fileEntries = Object.entries(files);
    if (fileEntries.length === 0) {
      result['/App.js'] = {
        code: `export default function App() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontFamily: 'system-ui', color: '#888', background: '#111827' }}>
      <div style={{ textAlign: 'center' }}>
        <h2 style={{ color: '#0ea5e9', marginBottom: 8 }}>Studio Preview</h2>
        <p>Describe your app in the chat to get started</p>
      </div>
    </div>
  );
}`,
        active: true,
      };
      return result;
    }

    for (const [path, file] of fileEntries) {
      const sandpackPath = path.startsWith('/') ? path : `/${path}`;
      const isJsx = /\.(jsx?|tsx?)$/.test(sandpackPath);
      const code = isJsx ? sanitizeStringStyles(file.content) : file.content;
      result[sandpackPath] = { code };
    }

    // Ensure we have an entry point
    if (!result['/App.js'] && !result['/App.tsx'] && !result['/App.jsx']) {
      if (result['/src/App.tsx'] || result['/src/App.js']) {
        // ok — Sandpack will find it
      } else {
        result['/App.js'] = {
          code: `export default function App() {
  return <div>Preview loading...</div>;
}`,
        };
      }
    }

    // Inject shim files for packages that break in Sandpack
    for (const imp of detectedImports) {
      const shimKey = getShimKey(imp);
      if (shimKey && SANDPACK_SHIMS[shimKey]) {
        // Sandpack resolves bare imports from /node_modules/<pkg>/index.js
        const shimPath = `/node_modules/${shimKey}/index.js`;
        if (!result[shimPath]) {
          result[shimPath] = { code: SANDPACK_SHIMS[shimKey] };
        }
      }
    }

    return result;
  }, [files, detectedImports]);

  // Compute dependencies: package.json + auto-detect (excluding shimmed packages)
  const customDeps = useMemo(() => {
    const deps: Record<string, string> = {};

    // 1. Check for package.json in files
    const pkgFile = files['package.json'] || files['/package.json'];
    if (pkgFile) {
      try {
        const pkg = JSON.parse(pkgFile.content);
        if (pkg.dependencies) Object.assign(deps, pkg.dependencies);
      } catch {}
    }

    // 2. Auto-detect imports, skip builtins and shimmed packages
    const builtins = new Set([
      'react', 'react-dom', 'react-dom/client', 'react/jsx-runtime',
    ]);

    for (const imp of detectedImports) {
      const pkgName = imp.startsWith('@')
        ? imp.split('/').slice(0, 2).join('/')
        : imp.split('/')[0];
      // Skip if builtin, already added, or we have a shim for it
      if (builtins.has(pkgName) || deps[pkgName]) continue;
      if (getShimKey(imp)) continue;
      deps[pkgName] = 'latest';
    }

    // Remove any shimmed packages that came from package.json too
    for (const imp of detectedImports) {
      const shimKey = getShimKey(imp);
      if (shimKey) {
        const pkgName = shimKey.startsWith('@')
          ? shimKey.split('/').slice(0, 2).join('/')
          : shimKey.split('/')[0];
        delete deps[pkgName];
      }
    }

    return deps;
  }, [files, detectedImports]);

  const hasFiles = Object.keys(files).length > 0;

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 h-8 flex-shrink-0"
        style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
      >
        <span className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>
          Preview
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowConsole(!showConsole)}
            className="text-xs px-2 py-0.5 rounded transition-colors"
            style={{
              background: showConsole ? 'var(--t-primary)' : 'var(--t-surface2)',
              color: showConsole ? '#fff' : 'var(--t-muted)',
            }}
          >
            Console
          </button>
        </div>
      </div>

      {/* Sandpack — use absolute positioning to force full height */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <div className="studio-sandpack-wrapper" style={{ position: 'absolute', inset: 0 }}>
          <SandpackProvider
            template="react"
            files={sandpackFiles}
            customSetup={{
              dependencies: {
                ...customDeps,
              },
            }}
            theme={{
              colors: {
                surface1: '#111827',
                surface2: '#1f2937',
                surface3: '#374151',
                clickable: '#6b7280',
                base: '#f1f5f9',
                disabled: '#374151',
                hover: '#0ea5e9',
                accent: '#0ea5e9',
                error: '#ef4444',
                errorSurface: '#7f1d1d',
              },
              syntax: {
                plain: '#f1f5f9',
                comment: { color: '#6b7280', fontStyle: 'italic' },
                keyword: '#c084fc',
                tag: '#22c55e',
                punctuation: '#6b7280',
                definition: '#38bdf8',
                property: '#fbbf24',
                static: '#f472b6',
                string: '#a5f3fc',
              },
              font: {
                body: "system-ui, -apple-system, sans-serif",
                mono: "'Menlo', 'Monaco', 'Courier New', monospace",
                size: '13px',
                lineHeight: '1.5',
              },
            }}
            options={{
              recompileMode: 'delayed',
              recompileDelay: 500,
            }}
          >
            <SandpackLayout>
              <SandpackPreview
                showNavigator={false}
                showRefreshButton={hasFiles}
                showOpenInCodeSandbox={false}
              />
              {showConsole && (
                <SandpackConsole />
              )}
            </SandpackLayout>
          </SandpackProvider>
        </div>
        {/* Force the entire Sandpack tree to fill available height */}
        <style>{`
          .studio-sandpack-wrapper,
          .studio-sandpack-wrapper > .sp-wrapper,
          .studio-sandpack-wrapper > div {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
          }
          .studio-sandpack-wrapper .sp-layout {
            flex: 1 !important;
            height: 100% !important;
            max-height: none !important;
            border: none !important;
            border-radius: 0 !important;
            display: flex !important;
            flex-direction: column !important;
          }
          .studio-sandpack-wrapper .sp-stack {
            flex: 1 !important;
            height: 100% !important;
            max-height: none !important;
          }
          .studio-sandpack-wrapper .sp-preview-container {
            flex: 1 !important;
            height: 100% !important;
            max-height: none !important;
          }
          .studio-sandpack-wrapper .sp-preview-iframe {
            height: 100% !important;
            min-height: 0 !important;
          }
          .studio-sandpack-wrapper .sp-preview-actions {
            z-index: 10;
          }
        `}</style>
      </div>
    </div>
  );
};

export default StudioPreviewPanel;
