import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useVox } from '../hooks/useVox';
import type { VoxState, VoxConfig, VoxMode } from '../types/vox';
import type { Tour } from '../components/VoxTourOverlay';

interface VoxContextType {
  state: VoxState;
  connect: (mode: VoxMode, config?: Partial<VoxConfig>) => void;
  disconnect: () => void;
  toggleMic: () => void;
  sendText: (text: string) => void;
  setVoice: (v: string) => void;
  isAvailable: boolean;
  on: (event: string, fn: (data: any) => void) => void;
  off: (event: string, fn: (data: any) => void) => void;
  activeTour: Tour | null;
  clearTour: () => void;
}

const VoxContext = createContext<VoxContextType | undefined>(undefined);

export const VoxProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const vox = useVox();
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    fetch('/api/vox/status')
      .then(r => r.json())
      .then(data => setIsAvailable(data.gemini_available || data.claude_available))
      .catch(() => setIsAvailable(false));
  }, []);

  return (
    <VoxContext.Provider value={{ ...vox, isAvailable }}>
      {children}
    </VoxContext.Provider>
  );
};

export const useVoxContext = () => {
  const context = useContext(VoxContext);
  if (!context) throw new Error('useVoxContext must be used within VoxProvider');
  return context;
};
