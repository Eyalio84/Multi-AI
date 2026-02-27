import React from 'react';
import type { GameDesignDoc } from '../../types/game';

interface Props {
  gdd: GameDesignDoc | null;
}

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="mb-4">
    <h4 className="text-sm font-semibold mb-2 px-3 py-1 rounded" style={{ background: 'var(--t-surface2)', color: 'var(--t-primary)' }}>
      {title}
    </h4>
    <div className="px-3 text-sm space-y-1" style={{ color: 'var(--t-text)' }}>
      {children}
    </div>
  </div>
);

const Field: React.FC<{ label: string; value: any }> = ({ label, value }) => (
  <div className="flex flex-wrap gap-x-2 gap-y-0.5">
    <span className="flex-shrink-0" style={{ color: 'var(--t-muted)' }}>{label}:</span>
    <span className="break-words">{Array.isArray(value) ? value.join(', ') : String(value)}</span>
  </div>
);

const GameDesignView: React.FC<Props> = ({ gdd }) => {
  if (!gdd) {
    return (
      <div className="flex items-center justify-center h-full" style={{ color: 'var(--t-muted)' }}>
        <div className="text-sm">No GDD yet — complete the interview first</div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-3">
      <h3 className="text-base font-bold mb-3" style={{ color: 'var(--t-text)' }}>
        {gdd.meta.name} — Game Design Document
      </h3>

      <Section title="Meta">
        <Field label="Genre" value={gdd.meta.genre} />
        <Field label="Unique Feature" value={gdd.meta.unique_feature} />
        <Field label="Starting Scenario" value={gdd.meta.starting_scenario} />
      </Section>

      <Section title="Player">
        <Field label="Description" value={gdd.player.description} />
        <Field label="Movement" value={gdd.player.movement_style} />
        <Field label="Abilities" value={gdd.player.abilities} />
        <Field label="HP System" value={gdd.player.hp_system} />
        <Field label="Progression" value={gdd.player.progression} />
        <Field label="Base Stats" value={`HP:${gdd.player.base_stats.hp} STR:${gdd.player.base_stats.strength} DEF:${gdd.player.base_stats.defense}`} />
      </Section>

      <Section title="World">
        <Field label="Size" value={gdd.world.map_size} />
        <Field label="Theme" value={gdd.world.tile_theme} />
        <Field label="Interactive Objects" value={gdd.world.interactive_objects} />
      </Section>

      <Section title={`NPCs (${gdd.npcs.length})`}>
        {gdd.npcs.map((npc, i) => (
          <div key={i} className="p-2 rounded mb-1" style={{ background: 'var(--t-surface)' }}>
            <span className="font-medium">{npc.name}</span>
            <span className="text-xs ml-2" style={{ color: 'var(--t-muted)' }}>
              {npc.role} ({npc.intelligence})
            </span>
          </div>
        ))}
      </Section>

      <Section title={`Enemies (${gdd.enemies.length})`}>
        {gdd.enemies.map((enemy, i) => (
          <div key={i} className="p-2 rounded mb-1" style={{ background: 'var(--t-surface)' }}>
            <span className="font-medium">{enemy.name}</span>
            <span className="text-xs ml-2" style={{ color: 'var(--t-muted)' }}>
              HP:{enemy.hp} DMG:{enemy.damage} SPD:{enemy.speed} XP:{enemy.xp}
            </span>
          </div>
        ))}
      </Section>

      <Section title="Systems">
        <Field label="Combat" value={gdd.systems.combat} />
        <Field label="Inventory" value={gdd.systems.inventory} />
        <Field label="Audio" value={gdd.systems.audio} />
      </Section>

      {gdd.local_llm.enabled && (
        <Section title="Local LLM">
          <Field label="Model" value={gdd.local_llm.model} />
          <Field label="NPC Intelligence" value={gdd.local_llm.npc_intelligence} />
        </Section>
      )}
    </div>
  );
};

export default GameDesignView;
