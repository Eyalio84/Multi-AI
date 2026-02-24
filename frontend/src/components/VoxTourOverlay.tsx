/**
 * VoxTourOverlay — Guided tour spotlight/highlight component.
 * Shows a spotlight on target CSS selectors, with tooltips and
 * auto-advance when VOX finishes speaking each step.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';

export interface TourStep {
  target: string;
  speech: string;
  position: 'top' | 'bottom' | 'left' | 'right';
  highlight: boolean;
}

export interface Tour {
  name: string;
  description: string;
  steps: TourStep[];
}

interface VoxTourOverlayProps {
  tour: Tour | null;
  onComplete: () => void;
  onStepChange?: (step: number, speech: string) => void;
}

const VoxTourOverlay: React.FC<VoxTourOverlayProps> = ({ tour, onComplete, onStepChange }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Find target element for current step
  useEffect(() => {
    if (!tour) return;
    const step = tour.steps[currentStep];
    if (!step) return;

    // Try each selector (comma-separated fallbacks)
    const selectors = step.target.split(',').map(s => s.trim());
    let el: Element | null = null;
    for (const sel of selectors) {
      try {
        el = document.querySelector(sel);
        if (el) break;
      } catch (_) { /* invalid selector */ }
    }

    if (el) {
      const rect = el.getBoundingClientRect();
      setTargetRect(rect);
    } else {
      // No element found — use center of screen
      setTargetRect(new DOMRect(
        window.innerWidth / 2 - 100,
        window.innerHeight / 2 - 50,
        200,
        100,
      ));
    }

    // Notify parent of step change for VOX to speak
    onStepChange?.(currentStep, step.speech);
  }, [tour, currentStep, onStepChange]);

  const handleNext = useCallback(() => {
    if (!tour) return;
    if (currentStep < tour.steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      setCurrentStep(0);
      onComplete();
    }
  }, [tour, currentStep, onComplete]);

  const handlePrev = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  }, [currentStep]);

  const handleSkip = useCallback(() => {
    setCurrentStep(0);
    onComplete();
  }, [onComplete]);

  if (!tour || !targetRect) return null;

  const step = tour.steps[currentStep];
  if (!step) return null;

  // Calculate tooltip position
  const padding = 12;
  const tooltipStyle: React.CSSProperties = {
    position: 'fixed',
    zIndex: 10002,
    maxWidth: 320,
    padding: '12px 16px',
    borderRadius: 12,
    background: 'var(--t-surface, #1e293b)',
    border: '1px solid var(--t-primary, #0ea5e9)',
    color: 'var(--t-text, #e2e8f0)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  };

  switch (step.position) {
    case 'top':
      tooltipStyle.left = targetRect.left + targetRect.width / 2 - 160;
      tooltipStyle.bottom = window.innerHeight - targetRect.top + padding;
      break;
    case 'bottom':
      tooltipStyle.left = targetRect.left + targetRect.width / 2 - 160;
      tooltipStyle.top = targetRect.bottom + padding;
      break;
    case 'left':
      tooltipStyle.right = window.innerWidth - targetRect.left + padding;
      tooltipStyle.top = targetRect.top + targetRect.height / 2 - 60;
      break;
    case 'right':
      tooltipStyle.left = targetRect.right + padding;
      tooltipStyle.top = targetRect.top + targetRect.height / 2 - 60;
      break;
  }

  // Clamp to viewport
  if (typeof tooltipStyle.left === 'number') {
    tooltipStyle.left = Math.max(8, Math.min(tooltipStyle.left, window.innerWidth - 340));
  }
  if (typeof tooltipStyle.top === 'number') {
    tooltipStyle.top = Math.max(8, Math.min(tooltipStyle.top, window.innerHeight - 200));
  }

  return (
    <>
      {/* Backdrop overlay */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 10000,
          background: 'rgba(0,0,0,0.5)',
          pointerEvents: 'auto',
        }}
        onClick={handleSkip}
      />

      {/* Spotlight cutout */}
      {step.highlight && (
        <div
          style={{
            position: 'fixed',
            zIndex: 10001,
            left: targetRect.left - 6,
            top: targetRect.top - 6,
            width: targetRect.width + 12,
            height: targetRect.height + 12,
            borderRadius: 8,
            border: '2px solid var(--t-primary, #0ea5e9)',
            boxShadow: '0 0 0 9999px rgba(0,0,0,0.5), 0 0 20px rgba(14,165,233,0.4)',
            background: 'transparent',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Tooltip */}
      <div ref={tooltipRef} style={tooltipStyle} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--t-primary, #0ea5e9)' }}>
            {tour.name} ({currentStep + 1}/{tour.steps.length})
          </span>
          <button
            onClick={handleSkip}
            style={{
              background: 'none', border: 'none', color: 'var(--t-muted, #94a3b8)',
              cursor: 'pointer', fontSize: 16, lineHeight: 1, padding: '0 2px',
            }}
          >
            &times;
          </button>
        </div>

        {/* Speech text */}
        <p style={{ fontSize: 13, lineHeight: 1.5, margin: '0 0 12px' }}>
          {step.speech}
        </p>

        {/* Navigation */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            onClick={handlePrev}
            disabled={currentStep === 0}
            style={{
              fontSize: 12, fontWeight: 600, padding: '4px 12px', borderRadius: 6,
              border: '1px solid var(--t-border, #334155)',
              background: 'transparent',
              color: currentStep === 0 ? 'var(--t-muted, #64748b)' : 'var(--t-text, #e2e8f0)',
              cursor: currentStep === 0 ? 'default' : 'pointer',
              opacity: currentStep === 0 ? 0.4 : 1,
            }}
          >
            Prev
          </button>

          {/* Step dots */}
          <div style={{ display: 'flex', gap: 4 }}>
            {tour.steps.map((_, i) => (
              <span
                key={i}
                style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: i === currentStep ? 'var(--t-primary, #0ea5e9)' : 'var(--t-muted, #64748b)',
                }}
              />
            ))}
          </div>

          <button
            onClick={handleNext}
            style={{
              fontSize: 12, fontWeight: 600, padding: '4px 12px', borderRadius: 6,
              border: 'none',
              background: 'var(--t-primary, #0ea5e9)',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            {currentStep === tour.steps.length - 1 ? 'Finish' : 'Next'}
          </button>
        </div>
      </div>
    </>
  );
};

export default VoxTourOverlay;
