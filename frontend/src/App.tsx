import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider, useAppContext } from './context/AppContext';
import { VoxProvider } from './context/VoxContext';
import NavBar from './components/NavBar';
import ChatPage from './pages/ChatPage';
import CodingPage from './pages/CodingPage';
import AgentsPage from './pages/AgentsPage';
import PlaybooksPage from './pages/PlaybooksPage';
import WorkflowsPage from './pages/WorkflowsPage';
import KGStudioPage from './pages/KGStudioPage';
import StudioPage from './pages/StudioPage';
import IntegrationsPage from './pages/IntegrationsPage';
import SettingsPage from './pages/SettingsPage';
import ExpertsPage from './pages/ExpertsPage';
import ToolsPage from './pages/ToolsPage';
import VoxPage from './pages/VoxPage';
import VoxOverlay from './components/VoxOverlay';
import ToastContainer from './components/ToastContainer';

const AppContent: React.FC = () => {
  const { globalError, setGlobalError } = useAppContext();

  return (
    <VoxProvider>
      <div className="flex flex-col h-screen font-sans overflow-hidden" style={{ background: 'var(--t-bg)', color: 'var(--t-text)', fontFamily: 'var(--t-font)' }}>
        <NavBar />
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/coding" element={<CodingPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/playbooks" element={<PlaybooksPage />} />
            <Route path="/workflows" element={<WorkflowsPage />} />
            <Route path="/kg-studio" element={<KGStudioPage />} />
            <Route path="/builder" element={<StudioPage />} />
            <Route path="/experts" element={<ExpertsPage />} />
            <Route path="/tools" element={<ToolsPage />} />
            <Route path="/vox" element={<VoxPage />} />
            <Route path="/integrations" element={<IntegrationsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>

        {globalError && (
          <div className="fixed bottom-4 right-4 p-4 rounded-lg shadow-lg max-w-sm z-50" style={{ background: 'var(--t-error)', color: '#fff' }}>
            <div className="flex justify-between items-center">
              <p className="font-semibold text-sm">Error</p>
              <button onClick={() => setGlobalError(null)} className="text-xl leading-none">&times;</button>
            </div>
            <p className="text-sm mt-1">{globalError}</p>
          </div>
        )}

        <VoxOverlay />
        <ToastContainer />
      </div>
    </VoxProvider>
  );
};

const App: React.FC = () => (
  <AppProvider>
    <AppContent />
  </AppProvider>
);

export default App;
