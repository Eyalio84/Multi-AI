/** StudioPipelineConfig — Pipeline strategy selector + aesthetic visual controls */
import React from 'react';
import { useStudio } from '../../context/StudioContext';
import type { StudioPipelineStrategy, StudioVisualConfig, StudioPipelineStage } from '../../types/studio';

const STRATEGIES: { id: StudioPipelineStrategy; label: string; desc: string }[] = [
  { id: 'single', label: 'Single', desc: 'One model generates' },
  { id: 'advisor_builder', label: 'Advisor + Builder', desc: 'Model A enriches spec, Model B builds' },
  { id: 'builder_critic', label: 'Builder + Critic', desc: 'Build, critique, then refine' },
  { id: 'ping_pong', label: 'Ping Pong', desc: '2 models alternate 3 refine passes' },
  { id: 'chain', label: 'Chain', desc: 'Sequential stages, each adding specialty' },
];

const TYPOGRAPHY_OPTIONS: StudioVisualConfig['typography'][] = ['system', 'editorial', 'playful', 'minimal', 'bold'];
const THEME_OPTIONS: StudioVisualConfig['theme'][] = ['auto', 'light', 'dark', 'colorful'];
const MOTION_OPTIONS: StudioVisualConfig['motion'][] = ['none', 'subtle', 'rich'];
const BG_OPTIONS: StudioVisualConfig['background'][] = ['flat', 'gradient', 'pattern', 'glass'];
const STATE_OPTIONS: StudioVisualConfig['stateManagement'][] = ['context', 'zustand', 'redux'];
const STYLE_OPTIONS: StudioVisualConfig['stylingParadigm'][] = ['inline', 'tailwind', 'css-modules', 'styled'];

const STAGE_PRESETS: Record<StudioPipelineStrategy, StudioPipelineStage[]> = {
  single: [],
  advisor_builder: [
    { role: 'advisor', provider: 'claude', model: 'claude-opus-4-6' },
    { role: 'builder', provider: 'gemini', model: 'gemini-3-pro-preview' },
  ],
  builder_critic: [
    { role: 'builder', provider: 'gemini', model: 'gemini-3-pro-preview' },
    { role: 'critic', provider: 'claude', model: 'claude-sonnet-4-6' },
  ],
  ping_pong: [
    { role: 'builder', provider: 'gemini', model: 'gemini-3-pro-preview' },
    { role: 'builder', provider: 'claude', model: 'claude-sonnet-4-6' },
  ],
  chain: [
    { role: 'advisor', provider: 'claude', model: 'claude-sonnet-4-6' },
    { role: 'builder', provider: 'gemini', model: 'gemini-3-pro-preview' },
    { role: 'critic', provider: 'openai', model: 'gpt-5-mini' },
  ],
};

function PillSelect<T extends string>({
  label, options, value, onChange,
}: { label: string; options: T[]; value: T; onChange: (v: T) => void }) {
  return (
    <div className="mb-3">
      <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--t-muted)' }}>{label}</label>
      <div className="flex flex-wrap gap-1">
        {options.map(opt => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            className="px-2 py-0.5 rounded text-xs transition-colors"
            style={{
              background: value === opt ? 'var(--t-primary)' : 'var(--t-surface2)',
              color: value === opt ? '#fff' : 'var(--t-text)',
              opacity: value === opt ? 1 : 0.7,
            }}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}

const StudioPipelineConfig: React.FC = () => {
  const { pipelineConfig, setPipelineConfig, orchestrationStages, isStreaming } = useStudio();
  const { strategy, visualConfig } = pipelineConfig;

  const updateVisual = <K extends keyof StudioVisualConfig>(key: K, val: StudioVisualConfig[K]) => {
    setPipelineConfig(prev => ({
      ...prev,
      visualConfig: { ...prev.visualConfig, [key]: val },
    }));
  };

  const setStrategy = (s: StudioPipelineStrategy) => {
    setPipelineConfig(prev => ({
      ...prev,
      strategy: s,
      stages: STAGE_PRESETS[s] || [],
    }));
  };

  return (
    <div className="overflow-y-auto p-3" style={{ background: 'var(--t-surface)', color: 'var(--t-text)' }}>
      {/* Strategy Selector */}
      <div className="mb-4">
        <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--t-muted)' }}>
          Pipeline Strategy
        </h4>
        <div className="space-y-1">
          {STRATEGIES.map(s => (
            <button
              key={s.id}
              onClick={() => setStrategy(s.id)}
              className="w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors"
              style={{
                background: strategy === s.id ? 'var(--t-primary)' : 'transparent',
                color: strategy === s.id ? '#fff' : 'var(--t-text)',
                opacity: strategy === s.id ? 1 : 0.8,
              }}
            >
              <div className="font-medium">{s.label}</div>
              <div className="opacity-60 text-[10px]">{s.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Stage Preview for multi-model strategies */}
      {pipelineConfig.stages.length > 0 && (
        <div className="mb-4 p-2 rounded" style={{ background: 'var(--t-surface2)' }}>
          <h4 className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--t-muted)' }}>
            Pipeline Stages
          </h4>
          {pipelineConfig.stages.map((stage, i) => (
            <div key={i} className="flex items-center gap-1.5 text-xs mb-1">
              <span className="w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold"
                style={{ background: 'var(--t-primary)', color: '#fff' }}>
                {i + 1}
              </span>
              <span className="capitalize font-medium">{stage.role}</span>
              <span style={{ color: 'var(--t-muted)' }}>-</span>
              <span style={{ color: 'var(--t-muted)' }}>{stage.model}</span>
            </div>
          ))}
        </div>
      )}

      {/* Orchestration Progress */}
      {orchestrationStages.length > 0 && isStreaming && (
        <div className="mb-4 p-2 rounded" style={{ background: 'var(--t-surface2)' }}>
          <h4 className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--t-muted)' }}>
            Pipeline Progress
          </h4>
          {orchestrationStages.filter(e => e.type === 'orchestration_stage').map((e, i) => (
            <div key={i} className="flex items-center gap-1.5 text-xs mb-1">
              <span className={`w-2 h-2 rounded-full ${e.status === 'completed' ? 'bg-green-400' : e.status === 'started' ? 'animate-pulse bg-yellow-400' : 'bg-gray-400'}`} />
              <span className="capitalize">{e.role}</span>
              <span style={{ color: 'var(--t-muted)' }}>{e.provider}/{e.model?.split('-').slice(0, 2).join('-')}</span>
            </div>
          ))}
        </div>
      )}

      {/* Visual Config - Aesthetics */}
      <div className="border-t pt-3 mt-2" style={{ borderColor: 'var(--t-border)' }}>
        <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--t-muted)' }}>
          Visual Aesthetics
        </h4>

        <PillSelect label="Typography" options={TYPOGRAPHY_OPTIONS} value={visualConfig.typography} onChange={v => updateVisual('typography', v)} />
        <PillSelect label="Theme" options={THEME_OPTIONS} value={visualConfig.theme} onChange={v => updateVisual('theme', v)} />
        <PillSelect label="Motion" options={MOTION_OPTIONS} value={visualConfig.motion} onChange={v => updateVisual('motion', v)} />
        <PillSelect label="Background" options={BG_OPTIONS} value={visualConfig.background} onChange={v => updateVisual('background', v)} />

        <div className="border-t pt-2 mt-2" style={{ borderColor: 'var(--t-border)' }}>
          <h4 className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--t-muted)' }}>
            Architecture
          </h4>
          <PillSelect label="State Management" options={STATE_OPTIONS} value={visualConfig.stateManagement} onChange={v => updateVisual('stateManagement', v)} />
          <PillSelect label="Styling" options={STYLE_OPTIONS} value={visualConfig.stylingParadigm} onChange={v => updateVisual('stylingParadigm', v)} />
        </div>

        {/* Toggle switches */}
        <div className="mt-3 space-y-2">
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-xs" style={{ color: 'var(--t-text)' }}>Anti-Slop Mode</span>
            <button
              onClick={() => updateVisual('antiSlop', !visualConfig.antiSlop)}
              className="w-8 h-4 rounded-full transition-colors relative"
              style={{ background: visualConfig.antiSlop ? 'var(--t-primary)' : 'var(--t-surface2)' }}
            >
              <span
                className="absolute top-0.5 w-3 h-3 rounded-full bg-white transition-transform"
                style={{ left: visualConfig.antiSlop ? '16px' : '2px' }}
              />
            </button>
          </label>
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-xs" style={{ color: 'var(--t-text)' }}>Self-Reflection</span>
            <button
              onClick={() => updateVisual('selfReflection', !visualConfig.selfReflection)}
              className="w-8 h-4 rounded-full transition-colors relative"
              style={{ background: visualConfig.selfReflection ? 'var(--t-primary)' : 'var(--t-surface2)' }}
            >
              <span
                className="absolute top-0.5 w-3 h-3 rounded-full bg-white transition-transform"
                style={{ left: visualConfig.selfReflection ? '16px' : '2px' }}
              />
            </button>
          </label>
        </div>
      </div>
    </div>
  );
};

export default StudioPipelineConfig;
