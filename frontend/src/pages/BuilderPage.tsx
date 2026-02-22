import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import ModelSelector from '../components/ModelSelector';

const BuilderPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    builderState, setBuilderState, startWebAppBuild, resetWebAppBuild,
    generateWebAppPlan, generateWebAppCode, loadGeneratedProjectIntoIDE, exportGeneratedProject,
  } = useAppContext();

  const { isActive, currentStep, idea, plan, theme, generatedFiles, status } = builderState;

  if (!isActive) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold mb-4" style={{ color: 'var(--t-text)' }}>Web App Builder</h2>
          <p className="mb-6" style={{ color: 'var(--t-muted)' }}>Generate complete React + Vite + Tailwind projects from a single idea. Uses AI to plan architecture, then generates all files.</p>
          <button onClick={startWebAppBuild} className="t-btn px-6 py-3 rounded-lg text-lg" style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}>
            Start Building
          </button>
        </div>
      </div>
    );
  }

  const steps = ['Idea', 'Plan', 'Theme', 'Generate', 'Export'];

  return (
    <div className="flex flex-col h-full">
      {/* Step indicator */}
      <div className="p-3 border-b" style={{ borderColor: 'var(--t-border)', background: 'var(--t-surface)' }}>
        <div className="flex items-center justify-between mb-2">
          <ModelSelector />
          <button onClick={resetWebAppBuild} className="t-btn px-3 py-1 text-xs rounded" style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>Reset</button>
        </div>
        <div className="flex items-center gap-2">
          {steps.map((s, i) => (
            <React.Fragment key={s}>
              <div className="flex items-center gap-1" style={{ color: i + 1 <= currentStep ? 'var(--t-primary)' : 'var(--t-muted)' }}>
                <div
                  className="h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold"
                  style={{ background: i + 1 <= currentStep ? 'var(--t-primary)' : 'var(--t-surface2)', color: 'var(--t-text)' }}
                >
                  {i + 1}
                </div>
                <span className="text-xs hidden sm:inline">{s}</span>
              </div>
              {i < steps.length - 1 && <div className="flex-1 h-0.5" style={{ background: i + 1 < currentStep ? 'var(--t-primary)' : 'var(--t-surface2)' }} />}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step content */}
      <div className="flex-1 overflow-y-auto p-4 lg:p-8 max-w-3xl mx-auto w-full">
        {/* Step 1: Idea */}
        {currentStep === 1 && (
          <div>
            <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--t-text)' }}>What do you want to build?</h3>
            <textarea
              value={idea}
              onChange={e => setBuilderState(prev => ({ ...prev, idea: e.target.value }))}
              placeholder="Describe your app idea in detail... e.g., A task management app with drag-and-drop kanban board, dark theme, and local storage persistence."
              className="w-full h-40 p-4 rounded-lg text-sm focus:outline-none focus:ring-2 resize-none"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', '--tw-ring-color': 'var(--t-primary)' } as React.CSSProperties}
            />
            <button
              onClick={generateWebAppPlan}
              disabled={!idea.trim() || status.isLoading}
              className="t-btn mt-4 px-6 py-3 rounded-lg disabled:opacity-50"
              style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}
            >
              {status.isLoading ? status.message : 'Generate Plan'}
            </button>
          </div>
        )}

        {/* Step 2: Plan Review */}
        {currentStep === 2 && plan && (
          <div>
            <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--t-text)' }}>Project Plan</h3>
            <div className="t-card rounded-lg p-4 space-y-3" style={{ background: 'var(--t-surface)' }}>
              <div><span className="text-xs" style={{ color: 'var(--t-muted)' }}>Name:</span> <span className="text-sm" style={{ color: 'var(--t-text)' }}>{plan.projectName}</span></div>
              <div><span className="text-xs" style={{ color: 'var(--t-muted)' }}>Description:</span> <p className="text-sm" style={{ color: 'var(--t-text2)' }}>{plan.description}</p></div>
              {plan.features && (
                <div>
                  <span className="text-xs" style={{ color: 'var(--t-muted)' }}>Features:</span>
                  <ul className="list-disc list-inside text-sm mt-1" style={{ color: 'var(--t-text2)' }}>
                    {plan.features.map((f: string, i: number) => <li key={i}>{f}</li>)}
                  </ul>
                </div>
              )}
              {plan.fileStructure && (
                <div>
                  <span className="text-xs" style={{ color: 'var(--t-muted)' }}>Files:</span>
                  <div className="mt-1 text-xs font-mono" style={{ color: 'var(--t-muted)' }}>{plan.fileStructure.join('\n')}</div>
                </div>
              )}
            </div>
            <button
              onClick={() => setBuilderState(prev => ({ ...prev, currentStep: 3 }))}
              className="t-btn mt-4 px-6 py-3 rounded-lg"
              style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}
            >
              Next: Theme
            </button>
          </div>
        )}

        {/* Step 3: Theme */}
        {currentStep === 3 && (
          <div>
            <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--t-text)' }}>Choose a Theme</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm block mb-1" style={{ color: 'var(--t-muted)' }}>Color Palette</label>
                <select
                  value={theme.palette}
                  onChange={e => setBuilderState(prev => ({ ...prev, theme: { ...prev.theme, palette: e.target.value } }))}
                  className="w-full p-2 rounded text-sm"
                  style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}
                >
                  <option>Modern & Minimal</option>
                  <option>Dark & Bold</option>
                  <option>Warm & Inviting</option>
                  <option>Cool & Professional</option>
                  <option>Vibrant & Playful</option>
                </select>
              </div>
              <div>
                <label className="text-sm block mb-1" style={{ color: 'var(--t-muted)' }}>Typography</label>
                <select
                  value={theme.typography}
                  onChange={e => setBuilderState(prev => ({ ...prev, theme: { ...prev.theme, typography: e.target.value } }))}
                  className="w-full p-2 rounded text-sm"
                  style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}
                >
                  <option>Sans-serif & Friendly</option>
                  <option>Monospace & Technical</option>
                  <option>Serif & Elegant</option>
                  <option>Mixed & Dynamic</option>
                </select>
              </div>
            </div>
            <button
              onClick={generateWebAppCode}
              disabled={status.isLoading}
              className="t-btn mt-4 px-6 py-3 rounded-lg disabled:opacity-50"
              style={{ background: 'var(--t-success)', color: 'var(--t-text)' }}
            >
              {status.isLoading ? status.message : 'Generate Code'}
            </button>
          </div>
        )}

        {/* Step 4: Generating */}
        {currentStep === 4 && (
          <div className="text-center mt-20">
            <div className="animate-spin h-12 w-12 border-4 border-t-transparent rounded-full mx-auto" style={{ borderColor: 'var(--t-primary)', borderTopColor: 'transparent' }} />
            <p className="mt-4" style={{ color: 'var(--t-muted)' }}>{status.message}</p>
          </div>
        )}

        {/* Step 5: Export */}
        {currentStep === 5 && generatedFiles && (
          <div>
            <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--t-text)' }}>Project Generated!</h3>
            <div className="t-card rounded-lg p-4 mb-4" style={{ background: 'var(--t-surface)' }}>
              <p className="text-sm mb-2" style={{ color: 'var(--t-muted)' }}>{Object.keys(generatedFiles).length} files generated:</p>
              <div className="font-mono text-xs space-y-0.5 max-h-40 overflow-y-auto" style={{ color: 'var(--t-text2)' }}>
                {Object.keys(generatedFiles).map(path => <div key={path}>{path}</div>)}
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={async () => { await loadGeneratedProjectIntoIDE(); navigate('/coding'); }}
                className="t-btn px-6 py-3 rounded-lg"
                style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}
              >
                Open in IDE
              </button>
              <button
                onClick={exportGeneratedProject}
                className="t-btn px-6 py-3 rounded-lg"
                style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}
              >
                Download ZIP
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BuilderPage;
