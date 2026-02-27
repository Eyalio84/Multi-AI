import React, { useState, useEffect, useCallback } from 'react';
import * as api from '../../services/apiService';
import type { InterviewQuestion, GameProject } from '../../types/game';

const STORY_LABELS: Record<string, { label: string; color: string }> = {
  player: { label: 'Player Story', color: '#3b82f6' },
  world: { label: 'World Story', color: '#10b981' },
  technical: { label: 'Technical Story', color: '#8b5cf6' },
};

interface Props {
  game: GameProject;
  onComplete: () => void;
}

const GameInterview: React.FC<Props> = ({ game, onComplete }) => {
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [textValue, setTextValue] = useState('');
  const [multiValue, setMultiValue] = useState<string[]>([]);
  const [synthesizing, setSynthesizing] = useState(false);

  useEffect(() => {
    api.getInterviewQuestions().then(qs => {
      setQuestions(qs);
      const existing = game.interview_data || {};
      setAnswers(existing);
      const firstUnanswered = qs.findIndex((q: InterviewQuestion) => !(q.id in existing));
      if (firstUnanswered >= 0) setCurrentIdx(firstUnanswered);
      else setCurrentIdx(qs.length - 1);
    });
  }, [game.id]);

  const q = questions[currentIdx];
  const progress = Object.keys(answers).length;
  const total = questions.length;
  const allDone = progress >= total;
  const currentStory = q ? STORY_LABELS[q.story] : null;

  useEffect(() => {
    if (!q) return;
    if (q.type === 'text') setTextValue((answers[q.id] as string) || (q.default as string) || '');
    if (q.type === 'multiselect') setMultiValue((answers[q.id] as string[]) || (q.default as string[]) || []);
  }, [currentIdx, q]);

  const submitAnswer = useCallback(async (answer: any) => {
    if (!q) return;
    const updated = { ...answers, [q.id]: answer };
    setAnswers(updated);
    await api.submitInterviewAnswer(game.id, q.id, answer);
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(currentIdx + 1);
    }
  }, [q, answers, currentIdx, questions.length, game.id]);

  const handleSynthesize = async () => {
    setSynthesizing(true);
    try {
      await api.synthesizeGDD(game.id);
      onComplete();
    } finally {
      setSynthesizing(false);
    }
  };

  if (!q) {
    return <div className="p-6 text-center" style={{ color: 'var(--t-muted)' }}>Loading questions...</div>;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Progress bar */}
      <div className="px-3 pt-2">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] font-medium" style={{ color: currentStory?.color }}>
            {currentStory?.label}
          </span>
          <span className="text-[11px]" style={{ color: 'var(--t-muted)' }}>
            {progress}/{total}
          </span>
        </div>
        <div className="w-full h-1 rounded-full" style={{ background: 'var(--t-surface2)' }}>
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${(progress / total) * 100}%`, background: 'var(--t-primary)' }}
          />
        </div>
        {/* Step dots */}
        <div className="flex gap-0.5 mt-1.5 flex-wrap">
          {questions.map((qq, i) => (
            <button
              key={qq.id}
              onClick={() => setCurrentIdx(i)}
              className="w-1.5 h-1.5 rounded-full transition-all"
              style={{
                background: i === currentIdx
                  ? 'var(--t-primary)'
                  : answers[qq.id] !== undefined
                    ? STORY_LABELS[qq.story].color
                    : 'var(--t-surface2)',
                transform: i === currentIdx ? 'scale(1.8)' : 'scale(1)',
              }}
            />
          ))}
        </div>
      </div>

      {/* Question */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        <h3 className="text-base font-medium mb-3" style={{ color: 'var(--t-text)' }}>
          {q.question}
        </h3>

        {/* Select options — compact grid on mobile */}
        {q.type === 'select' && q.options && (
          <div className="grid grid-cols-1 gap-1.5">
            {q.options.map(opt => (
              <button
                key={opt.value}
                onClick={() => submitAnswer(opt.value)}
                className="text-left px-3 py-2 rounded-lg border transition-all"
                style={{
                  borderColor: answers[q.id] === opt.value ? 'var(--t-primary)' : 'var(--t-border)',
                  background: answers[q.id] === opt.value ? 'var(--t-primary)' : 'var(--t-surface)',
                  color: answers[q.id] === opt.value ? '#fff' : 'var(--t-text)',
                }}
              >
                <div className="text-sm">{opt.label}</div>
              </button>
            ))}
          </div>
        )}

        {/* Multiselect */}
        {q.type === 'multiselect' && q.options && (
          <div className="space-y-1.5">
            {q.options.map(opt => {
              const selected = multiValue.includes(opt.value);
              return (
                <button
                  key={opt.value}
                  onClick={() => {
                    const next = selected
                      ? multiValue.filter(v => v !== opt.value)
                      : [...multiValue, opt.value];
                    setMultiValue(next);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg border transition-all"
                  style={{
                    borderColor: selected ? 'var(--t-primary)' : 'var(--t-border)',
                    background: selected ? 'var(--t-primary)' : 'var(--t-surface)',
                    color: selected ? '#fff' : 'var(--t-text)',
                  }}
                >
                  <div className="text-sm">{selected ? '[x] ' : '[  ] '}{opt.label}</div>
                </button>
              );
            })}
            <button
              onClick={() => submitAnswer(multiValue)}
              className="w-full px-3 py-2 rounded text-sm font-medium mt-1"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
            >
              Confirm Selection
            </button>
          </div>
        )}

        {/* Text input */}
        {q.type === 'text' && (
          <div className="space-y-2">
            <textarea
              value={textValue}
              onChange={e => setTextValue(e.target.value)}
              rows={3}
              className="w-full p-3 rounded-lg border text-sm"
              style={{
                background: 'var(--t-surface)',
                borderColor: 'var(--t-border)',
                color: 'var(--t-text)',
              }}
              placeholder={q.default as string || 'Type your answer...'}
            />
            <button
              onClick={() => submitAnswer(textValue || q.default)}
              className="px-4 py-2 rounded text-sm font-medium"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
            >
              Submit
            </button>
          </div>
        )}
      </div>

      {/* Navigation — stacks synthesize button better on small screens */}
      <div className="px-3 py-2 border-t" style={{ borderColor: 'var(--t-border)' }}>
        {allDone && (
          <button
            onClick={handleSynthesize}
            disabled={synthesizing}
            className="w-full px-3 py-2 rounded text-sm font-medium mb-2"
            style={{ background: '#10b981', color: '#fff' }}
          >
            {synthesizing ? 'Synthesizing GDD...' : 'Build Game Design Doc'}
          </button>
        )}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrentIdx(Math.max(0, currentIdx - 1))}
            disabled={currentIdx === 0}
            className="px-3 py-1.5 rounded text-xs"
            style={{
              background: currentIdx === 0 ? 'var(--t-surface2)' : 'var(--t-surface)',
              color: currentIdx === 0 ? 'var(--t-muted)' : 'var(--t-text)',
              borderWidth: 1,
              borderColor: 'var(--t-border)',
            }}
          >
            Back
          </button>
          <span className="text-[11px]" style={{ color: 'var(--t-muted)' }}>
            {currentIdx + 1} / {total}
          </span>
          <button
            onClick={() => setCurrentIdx(Math.min(questions.length - 1, currentIdx + 1))}
            disabled={currentIdx >= questions.length - 1}
            className="px-3 py-1.5 rounded text-xs"
            style={{
              background: currentIdx >= questions.length - 1 ? 'var(--t-surface2)' : 'var(--t-surface)',
              color: currentIdx >= questions.length - 1 ? 'var(--t-muted)' : 'var(--t-text)',
              borderWidth: 1,
              borderColor: 'var(--t-border)',
            }}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default GameInterview;
