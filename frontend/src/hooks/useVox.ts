/**
 * useVox — Thin React wrapper around voxCore singleton.
 *
 * Subscribes to voxCore events and triggers React re-renders.
 * Injects React Router navigation callback into voxCore (INSIGHT-004).
 * All actual logic lives in services/voxCore.ts.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import type { VoxState, VoxConfig, VoxMode } from '../types/vox';
import type { Tour } from '../components/VoxTourOverlay';
import * as voxCore from '../services/voxCore';

export type VoxEventCallback = (data: any) => void;

export function useVox() {
  const [state, setState] = useState<VoxState>(voxCore.getState);
  const [activeTour, setActiveTour] = useState<Tour | null>(voxCore.getActiveTour);

  const navigate = useNavigate();
  const location = useLocation();

  // Inject navigation callback into voxCore (INSIGHT-004)
  useEffect(() => {
    voxCore.setNavigator(navigate);
    voxCore.setLocationGetter(() => location.pathname);
  }, [navigate, location.pathname]);

  // Subscribe to voxCore state changes → trigger React re-renders (INSIGHT-006)
  useEffect(() => {
    const unsubState = voxCore.on('state_change', (newState: VoxState) => {
      setState({ ...newState });
    });
    const unsubTourStart = voxCore.on('tour_start', (tour: Tour) => {
      setActiveTour(tour);
    });
    const unsubTourEnd = voxCore.on('tour_end', () => {
      setActiveTour(null);
    });
    return () => { unsubState(); unsubTourStart(); unsubTourEnd(); };
  }, []);

  // Report page visits to backend awareness
  const prevPageRef = useRef(location.pathname);
  useEffect(() => {
    if (location.pathname !== prevPageRef.current) {
      prevPageRef.current = location.pathname;
      voxCore.reportPageVisit(location.pathname);
    }
  }, [location.pathname]);

  // Proxy public API (stable callbacks)
  const connect = useCallback((mode: VoxMode, config?: Partial<VoxConfig>) => {
    voxCore.connect(mode, config);
  }, []);

  const disconnect = useCallback(() => {
    voxCore.disconnect();
  }, []);

  const toggleMic = useCallback(() => {
    voxCore.toggleMic();
  }, []);

  const sendText = useCallback((text: string) => {
    voxCore.sendText(text);
  }, []);

  const setVoice = useCallback((v: string) => {
    voxCore.setVoice(v);
  }, []);

  const clearTour = useCallback(() => {
    voxCore.clearTour();
  }, []);

  const on = useCallback((event: string, fn: VoxEventCallback) => {
    return voxCore.on(event, fn);
  }, []);

  const off = useCallback((event: string, fn: VoxEventCallback) => {
    voxCore.off(event, fn);
  }, []);

  return {
    state,
    connect,
    disconnect,
    toggleMic,
    sendText,
    setVoice,
    on,
    off,
    activeTour,
    clearTour,
  };
}
