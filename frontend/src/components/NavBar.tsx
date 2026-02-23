import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import ThemeSwitcher from './ThemeSwitcher';

const links = [
  { to: '/chat', label: 'Chat', icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' },
  { to: '/coding', label: 'Coding', icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4' },
  { to: '/agents', label: 'Agents', icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
  { to: '/playbooks', label: 'Playbooks', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
  { to: '/workflows', label: 'Workflows', icon: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z' },
  { to: '/kg-studio', label: 'KG Studio', icon: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1' },
  { to: '/builder', label: 'Studio', icon: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z' },
];

const NavBar: React.FC = () => {
  const { activeProvider, activeModel, workspaceMode, themeId } = useAppContext();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isScratch = themeId === 'scratch';

  return (
    <nav className="t-nav border-b" style={{ background: 'var(--t-surface)', borderColor: 'var(--t-border)' }}>
      <div className="flex items-center justify-between px-4 h-12">
        <div className="flex items-center gap-2">
          <span className="font-bold text-sm whitespace-nowrap" style={{ color: 'var(--t-primary)' }}>AI Workspace</span>
          <span className="hidden sm:inline text-xs px-2 py-0.5 rounded" style={{ color: 'var(--t-muted)', background: 'var(--t-surface2)' }}>
            {workspaceMode === 'claude-code' ? 'CC' : 'SA'}
          </span>
        </div>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-1">
          {links.map(link => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded text-xs font-medium transition-colors ${isActive && isScratch ? 't-nav-active' : ''}`
              }
              style={({ isActive }) => ({
                background: isActive && !isScratch ? 'var(--t-primary)' : 'transparent',
                color: isActive ? (isScratch ? 'var(--t-text)' : '#fff') : 'var(--t-muted)',
              })}
            >
              {link.label}
            </NavLink>
          ))}
          <ThemeSwitcher />
          <NavLink
            to="/settings"
            className="px-2 py-1.5 rounded transition-colors"
            style={({ isActive }) => ({ color: isActive ? 'var(--t-primary)' : 'var(--t-muted)' })}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </NavLink>
        </div>

        {/* Model badge */}
        <div className="hidden md:flex items-center gap-2 text-xs">
          <span className="px-2 py-0.5 rounded" style={{
            background: activeProvider === 'claude' ? '#9a3412' : 'var(--t-primary)',
            color: '#fff',
          }}>
            {activeProvider === 'claude' ? 'Claude' : 'Gemini'}
          </span>
          <span className="truncate max-w-[120px]" style={{ color: 'var(--t-muted)' }}>{activeModel}</span>
        </div>

        {/* Mobile hamburger */}
        <div className="md:hidden flex items-center gap-1">
          <ThemeSwitcher />
          <button className="p-2" style={{ color: 'var(--t-muted)' }} onClick={() => setMobileOpen(!mobileOpen)}>
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t px-2 py-2 space-y-1" style={{ borderColor: 'var(--t-border)' }}>
          {links.map(link => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={() => setMobileOpen(false)}
              className="block px-3 py-2 rounded text-sm"
              style={({ isActive }) => ({
                background: isActive ? 'var(--t-primary)' : 'transparent',
                color: isActive ? '#fff' : 'var(--t-muted)',
              })}
            >
              {link.label}
            </NavLink>
          ))}
          <NavLink to="/settings" onClick={() => setMobileOpen(false)} className="block px-3 py-2 rounded text-sm" style={{ color: 'var(--t-muted)' }}>
            Settings
          </NavLink>
        </div>
      )}
    </nav>
  );
};

export default NavBar;
