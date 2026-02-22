import React, { useState, useEffect } from 'react';
import * as apiService from '../services/apiService';

interface WorkflowStep {
  id: string;
  name: string;
  prompt_template?: string;
  model_hint?: string;
  depends_on?: string[];
  provider?: string;
  model?: string;
  reason?: string;
}

interface Template {
  id: string;
  name: string;
  description: string;
  step_count: number;
  steps: { id: string; name: string }[];
}

const WorkflowsPage: React.FC = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [goal, setGoal] = useState('');
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [executing, setExecuting] = useState(false);
  const [executionLog, setExecutionLog] = useState<{ stepId: string; text: string; status: string }[]>([]);
  const [activeStepId, setActiveStepId] = useState<string | null>(null);

  useEffect(() => {
    apiService.listWorkflowTemplates().then(data => setTemplates(data.templates || [])).catch(() => {});
  }, []);

  const handleUseTemplate = async (templateId: string) => {
    if (!goal.trim()) return;
    const data = await apiService.planWorkflow(goal, templateId);
    setSteps(data.steps || []);
  };

  const handlePlanCustom = async () => {
    if (!goal.trim()) return;
    const data = await apiService.planWorkflow(goal);
    setSteps(data.steps || []);
  };

  const handleExecute = async () => {
    if (steps.length === 0) return;
    setExecuting(true);
    setExecutionLog([]);

    try {
      const stream = await apiService.streamWorkflowExecution(steps, goal);
      const reader = stream.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '));

        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'step_start') {
              setActiveStepId(data.step_id);
              setExecutionLog(prev => [...prev, { stepId: data.step_id, text: '', status: 'running' }]);
            } else if (data.type === 'step_token') {
              setExecutionLog(prev => prev.map(l =>
                l.stepId === data.step_id ? { ...l, text: l.text + data.content } : l
              ));
            } else if (data.type === 'step_complete') {
              setExecutionLog(prev => prev.map(l =>
                l.stepId === data.step_id ? { ...l, status: 'complete' } : l
              ));
            } else if (data.type === 'step_error') {
              setExecutionLog(prev => prev.map(l =>
                l.stepId === data.step_id ? { ...l, status: 'error', text: l.text + `\nError: ${data.error}` } : l
              ));
            } else if (data.type === 'workflow_complete') {
              setActiveStepId(null);
            }
          } catch {}
        }
      }
    } catch (e: any) {
      setExecutionLog(prev => [...prev, { stepId: 'error', text: e.message, status: 'error' }]);
    }
    setExecuting(false);
  };

  const getStatusColor = (status: string) => {
    if (status === 'complete') return 'var(--t-success)';
    if (status === 'error') return 'var(--t-error)';
    return 'var(--t-primary)';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <div className="p-3 border-b" style={{ borderColor: 'var(--t-border)', background: 'var(--t-surface)' }}>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            value={goal}
            onChange={e => setGoal(e.target.value)}
            placeholder="Describe your workflow goal..."
            className="flex-1 px-3 py-2 rounded text-sm focus:outline-none focus:ring-1"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', '--tw-ring-color': 'var(--t-primary)' } as React.CSSProperties}
          />
          <button onClick={handlePlanCustom} className="t-btn px-4 py-2 text-sm rounded" style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}>
            AI Plan
          </button>
        </div>
      </div>

      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Templates + Steps */}
        <div className="w-full lg:w-80 border-b lg:border-b-0 lg:border-r flex flex-col overflow-y-auto" style={{ borderColor: 'var(--t-border)' }}>
          <div className="p-2 text-xs font-semibold border-b" style={{ color: 'var(--t-muted)', borderColor: 'var(--t-border)' }}>TEMPLATES</div>
          {templates.map(t => (
            <button
              key={t.id}
              onClick={() => handleUseTemplate(t.id)}
              className="t-btn text-left px-3 py-2 border-b"
              style={{ borderColor: 'var(--t-surface)' }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--t-surface2)'}
              onMouseLeave={e => e.currentTarget.style.background = ''}
            >
              <div className="text-sm" style={{ color: 'var(--t-text2)' }}>{t.name}</div>
              <div className="text-xs" style={{ color: 'var(--t-muted)' }}>{t.description}</div>
              <div className="text-[10px] mt-0.5" style={{ color: 'var(--t-primary)' }}>{t.step_count} steps</div>
            </button>
          ))}

          {steps.length > 0 && (
            <>
              <div className="p-2 text-xs font-semibold border-b mt-2" style={{ color: 'var(--t-muted)', borderColor: 'var(--t-border)' }}>PLANNED STEPS</div>
              {steps.map((step, i) => (
                <div
                  key={step.id}
                  className={`px-3 py-2 border-b`}
                  style={{
                    borderColor: 'var(--t-surface)',
                    ...(activeStepId === step.id ? { background: 'rgba(14, 165, 233, 0.1)' } : {}),
                  }}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[10px]" style={{ color: 'var(--t-muted)' }}>{i + 1}</span>
                    <span className="text-sm" style={{ color: 'var(--t-text2)' }}>{step.name}</span>
                    {activeStepId === step.id && <span className="animate-pulse text-[10px]" style={{ color: 'var(--t-primary)' }}>running</span>}
                  </div>
                  {step.provider && (
                    <span className={`text-[9px] px-1 py-0.5 rounded ${step.provider === 'claude' ? 'bg-orange-800' : 'bg-blue-800'}`}>
                      {step.model}
                    </span>
                  )}
                </div>
              ))}
              <button
                onClick={handleExecute}
                disabled={executing}
                className="t-btn m-2 px-4 py-2 text-sm rounded disabled:opacity-50"
                style={{ background: 'var(--t-success)', color: 'var(--t-text)' }}
              >
                {executing ? 'Executing...' : 'Execute Workflow'}
              </button>
            </>
          )}
        </div>

        {/* Execution log */}
        <div className="flex-1 overflow-y-auto p-4">
          {executionLog.length === 0 && (
            <div className="text-center mt-20" style={{ color: 'var(--t-muted)' }}>
              <p className="text-lg">Workflow Engine</p>
              <p className="text-sm mt-1">Select a template or use AI Plan, then execute</p>
            </div>
          )}
          {executionLog.map((log, i) => (
            <div key={i} className="mb-4">
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`h-2 w-2 rounded-full ${log.status === 'running' ? 'animate-pulse' : ''}`}
                  style={{ background: getStatusColor(log.status) }}
                />
                <span className="text-sm font-medium" style={{ color: 'var(--t-text2)' }}>
                  {steps.find(s => s.id === log.stepId)?.name || log.stepId}
                </span>
                <span className="text-[10px]" style={{ color: getStatusColor(log.status) }}>
                  {log.status}
                </span>
              </div>
              <div className="t-card ml-4 p-3 rounded text-sm whitespace-pre-wrap max-h-60 overflow-y-auto" style={{ background: 'var(--t-surface)', color: 'var(--t-text2)' }}>
                {log.text || 'Processing...'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WorkflowsPage;
