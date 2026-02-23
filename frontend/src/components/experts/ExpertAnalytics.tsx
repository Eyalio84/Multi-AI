import React, { useState, useEffect } from 'react';
import { Expert, ExpertConversation } from '../../types';
import * as api from '../../services/apiService';

interface ExpertAnalyticsProps {
  expert: Expert;
}

const ExpertAnalytics: React.FC<ExpertAnalyticsProps> = ({ expert }) => {
  const [conversations, setConversations] = useState<ExpertConversation[]>([]);

  useEffect(() => {
    api.listExpertConversations(expert.id).then(setConversations).catch(() => {});
  }, [expert.id]);

  const totalMessages = conversations.reduce((sum, c) => sum + c.message_count, 0);
  const avgMessages = conversations.length > 0 ? (totalMessages / conversations.length).toFixed(1) : '0';

  const Stat = ({ label, value, color }: { label: string; value: string | number; color?: string }) => (
    <div className="p-3 rounded-lg" style={{ background: 'var(--t-surface)' }}>
      <div className="text-lg font-bold" style={{ color: color || expert.color }}>{value}</div>
      <div className="text-xs" style={{ color: 'var(--t-muted)' }}>{label}</div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto p-4 space-y-6">
      <h3 className="text-sm font-semibold" style={{ color: 'var(--t-text)' }}>Analytics</h3>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Conversations" value={conversations.length} />
        <Stat label="Total Messages" value={totalMessages} />
        <Stat label="Avg per Conv" value={avgMessages} />
        <Stat label="Retrieval Methods" value={expert.retrieval_methods?.length || 0} />
      </div>

      {/* Retrieval weight distribution */}
      <section>
        <h4 className="text-xs font-semibold mb-2" style={{ color: 'var(--t-text)' }}>Weight Distribution</h4>
        <div className="flex rounded-lg overflow-hidden h-6">
          {[
            { label: 'Emb', value: expert.retrieval_alpha, color: '#8b5cf6' },
            { label: 'Text', value: expert.retrieval_beta, color: '#10b981' },
            { label: 'Graph', value: expert.retrieval_gamma, color: '#f59e0b' },
            { label: 'Intent', value: expert.retrieval_delta, color: '#ef4444' },
          ].map(w => (
            <div key={w.label} className="flex items-center justify-center text-[10px] text-white font-medium"
              style={{ width: `${w.value * 100}%`, background: w.color, minWidth: w.value > 0 ? '30px' : '0' }}>
              {w.value > 0.05 ? `${w.label} ${(w.value * 100).toFixed(0)}%` : ''}
            </div>
          ))}
        </div>
      </section>

      {/* Recent conversations */}
      <section>
        <h4 className="text-xs font-semibold mb-2" style={{ color: 'var(--t-text)' }}>Recent Conversations</h4>
        {conversations.length === 0 ? (
          <div className="text-xs" style={{ color: 'var(--t-muted)' }}>No conversations yet.</div>
        ) : (
          <div className="space-y-1">
            {conversations.slice(0, 10).map(c => (
              <div key={c.id} className="flex items-center justify-between p-2 rounded text-xs" style={{ background: 'var(--t-surface)' }}>
                <span className="truncate" style={{ color: 'var(--t-text)' }}>{c.title || `Conv ${c.id.slice(0, 6)}`}</span>
                <div className="flex gap-2 flex-shrink-0" style={{ color: 'var(--t-muted)' }}>
                  <span>{c.message_count} msgs</span>
                  <span>{new Date(c.last_message_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default ExpertAnalytics;
