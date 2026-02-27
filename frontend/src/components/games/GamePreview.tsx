import React, { useMemo, useState } from 'react';
import type { GameProject } from '../../types/game';

interface Props {
  game: GameProject;
}

const GamePreview: React.FC<Props> = ({ game }) => {
  const [fullscreen, setFullscreen] = useState(false);
  const files = game.files || {};

  const compiledHtml = useMemo(() => {
    if (!files['index.html']) return null;

    let html = files['index.html'];

    // Replace script src references with inline scripts
    const scriptFiles = Object.keys(files).filter(f => f.endsWith('.js'));
    for (const sf of scriptFiles) {
      const srcPattern = new RegExp(`<script\\s+src=["']${sf.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}["']\\s*>\\s*</script>`, 'g');
      html = html.replace(srcPattern, `<script>\n${files[sf]}\n</script>`);
    }

    // If phaser.min.js reference exists, replace with API URL
    html = html.replace(
      /src=["']\/docs\/phaser\/phaser\.min\.js["']/g,
      'src="/docs/phaser/phaser.min.js"'
    );

    return html;
  }, [files]);

  if (!compiledHtml) {
    return (
      <div className="flex items-center justify-center h-full" style={{ color: 'var(--t-muted)' }}>
        <div className="text-center space-y-2">
          <div className="text-3xl">&#127918;</div>
          <div className="text-sm">No game files yet</div>
          <div className="text-xs">Complete the interview and generate your game</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${fullscreen ? 'fixed inset-0 z-50' : 'h-full'}`} style={{ background: '#000' }}>
      <div className="flex items-center justify-between px-3 py-1.5" style={{ background: 'var(--t-surface)' }}>
        <span className="text-xs font-medium" style={{ color: 'var(--t-text)' }}>
          Preview: {game.name}
        </span>
        <button
          onClick={() => setFullscreen(!fullscreen)}
          className="text-xs px-2 py-0.5 rounded"
          style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
        >
          {fullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
        </button>
      </div>
      <iframe
        srcDoc={compiledHtml}
        className="flex-1 w-full border-0"
        sandbox="allow-scripts allow-same-origin"
        title="Game Preview"
      />
    </div>
  );
};

export default GamePreview;
