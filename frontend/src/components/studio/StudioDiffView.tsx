/** StudioDiffView — Simple line-by-line before/after diff viewer */
import React, { useMemo } from 'react';

interface Props {
  oldContent: string;
  newContent: string;
  fileName?: string;
}

interface DiffLine {
  type: 'unchanged' | 'added' | 'removed';
  content: string;
  oldLineNum?: number;
  newLineNum?: number;
}

const StudioDiffView: React.FC<Props> = ({ oldContent, newContent, fileName }) => {
  const diffLines = useMemo(() => {
    const oldLines = oldContent.split('\n');
    const newLines = newContent.split('\n');
    const result: DiffLine[] = [];

    // Simple LCS-based diff
    const maxLen = Math.max(oldLines.length, newLines.length);
    const lcs = computeLCS(oldLines, newLines);

    let oldIdx = 0;
    let newIdx = 0;
    let lcsIdx = 0;

    while (oldIdx < oldLines.length || newIdx < newLines.length) {
      if (lcsIdx < lcs.length && oldIdx < oldLines.length && oldLines[oldIdx] === lcs[lcsIdx] && newIdx < newLines.length && newLines[newIdx] === lcs[lcsIdx]) {
        result.push({ type: 'unchanged', content: oldLines[oldIdx], oldLineNum: oldIdx + 1, newLineNum: newIdx + 1 });
        oldIdx++;
        newIdx++;
        lcsIdx++;
      } else if (oldIdx < oldLines.length && (lcsIdx >= lcs.length || oldLines[oldIdx] !== lcs[lcsIdx])) {
        result.push({ type: 'removed', content: oldLines[oldIdx], oldLineNum: oldIdx + 1 });
        oldIdx++;
      } else if (newIdx < newLines.length && (lcsIdx >= lcs.length || newLines[newIdx] !== lcs[lcsIdx])) {
        result.push({ type: 'added', content: newLines[newIdx], newLineNum: newIdx + 1 });
        newIdx++;
      } else {
        break; // Safety valve
      }
    }

    return result;
  }, [oldContent, newContent]);

  const stats = useMemo(() => {
    const added = diffLines.filter(l => l.type === 'added').length;
    const removed = diffLines.filter(l => l.type === 'removed').length;
    return { added, removed };
  }, [diffLines]);

  return (
    <div className="flex flex-col h-full overflow-hidden" style={{ background: 'var(--t-bg)' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 h-8 flex-shrink-0"
        style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
      >
        <span className="text-xs font-medium truncate" style={{ color: 'var(--t-text2)' }}>
          {fileName || 'Diff View'}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: 'var(--t-success)' }}>+{stats.added}</span>
          <span className="text-xs" style={{ color: 'var(--t-error)' }}>-{stats.removed}</span>
        </div>
      </div>

      {/* Diff lines */}
      <div className="flex-1 overflow-auto" style={{ fontFamily: 'var(--t-font-mono)', fontSize: 12 }}>
        {diffLines.map((line, i) => {
          let bg = 'transparent';
          let color = 'var(--t-text)';
          let prefix = ' ';

          if (line.type === 'added') {
            bg = 'rgba(34, 197, 94, 0.12)';
            color = 'var(--t-success)';
            prefix = '+';
          } else if (line.type === 'removed') {
            bg = 'rgba(239, 68, 68, 0.12)';
            color = 'var(--t-error)';
            prefix = '-';
          }

          return (
            <div
              key={i}
              className="flex"
              style={{ background: bg, minHeight: '1.5em', lineHeight: '1.5em' }}
            >
              {/* Old line number */}
              <span
                className="flex-shrink-0 text-right px-1 select-none"
                style={{ width: 40, color: 'var(--t-muted)', opacity: 0.5 }}
              >
                {line.oldLineNum || ''}
              </span>
              {/* New line number */}
              <span
                className="flex-shrink-0 text-right px-1 select-none"
                style={{ width: 40, color: 'var(--t-muted)', opacity: 0.5, borderRight: '1px solid var(--t-border)' }}
              >
                {line.newLineNum || ''}
              </span>
              {/* Prefix */}
              <span className="flex-shrink-0 w-5 text-center select-none" style={{ color }}>
                {prefix}
              </span>
              {/* Content */}
              <span className="flex-1 whitespace-pre" style={{ color }}>
                {line.content}
              </span>
            </div>
          );
        })}

        {diffLines.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <p className="text-xs" style={{ color: 'var(--t-muted)' }}>No differences</p>
          </div>
        )}
      </div>
    </div>
  );
};

/** Compute Longest Common Subsequence of string arrays */
function computeLCS(a: string[], b: string[]): string[] {
  const m = a.length;
  const n = b.length;

  // For large files, use a simpler approach
  if (m > 1000 || n > 1000) {
    return simpleLCS(a, b);
  }

  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack
  const result: string[] = [];
  let i = m, j = n;
  while (i > 0 && j > 0) {
    if (a[i - 1] === b[j - 1]) {
      result.unshift(a[i - 1]);
      i--;
      j--;
    } else if (dp[i - 1][j] > dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }
  return result;
}

/** Simple LCS for large files — only matches consecutive equal runs */
function simpleLCS(a: string[], b: string[]): string[] {
  const bSet = new Set(b);
  return a.filter(line => bSet.has(line));
}

export default StudioDiffView;
