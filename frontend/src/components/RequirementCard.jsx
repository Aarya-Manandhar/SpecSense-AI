import React, { useState } from 'react';
import { AlertCircle, CheckCircle, ChevronDown, ChevronUp, Copy, Check, Sparkles, HelpCircle } from 'lucide-react';

export default function RequirementCard({ index, item, onApplyRewrite }) {
  const [expanded, setExpanded] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);

  const { text, score, status, defects = [], defect_count = 0, highlights = [] } = item;

  // Status color styling
  let scoreBadge = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  if (score < 70) {
    scoreBadge = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  } else if (score < 90) {
    scoreBadge = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  }

  // Highlight problematic words inside requirement text
  const renderHighlightedText = (originalText, highlightWords) => {
    if (!highlightWords || highlightWords.length === 0) {
      return <span>{originalText}</span>;
    }

    // Escape regex special chars
    const pattern = new RegExp(`\\b(${highlightWords.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})\\b`, 'gi');
    const parts = originalText.split(pattern);

    return (
      <span>
        {parts.map((part, i) => {
          const isMatch = highlightWords.some(hw => hw.toLowerCase() === part.toLowerCase());
          if (isMatch) {
            return (
              <mark
                key={i}
                className="bg-amber-500/20 text-amber-300 font-semibold px-1 py-0.5 rounded border border-amber-500/40"
              >
                {part}
              </mark>
            );
          }
          return part;
        })}
      </span>
    );
  };

  const handleCopy = (rewriteText, defectIdx) => {
    navigator.clipboard.writeText(rewriteText);
    setCopiedIndex(defectIdx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className={`w-full rounded-2xl border transition-all ${
      defect_count > 0 
        ? 'bg-slate-950/70 border-slate-800 hover:border-slate-700' 
        : 'bg-slate-950/40 border-slate-800/60'
    } p-5 md:p-6 mb-4 shadow-lg`}>
      
      {/* Header Row: Requirement Index, Score Badge, Status & Toggle */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/60">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-xs font-mono text-indigo-400 font-semibold">
            REQ #{String(index + 1).padStart(2, '0')}
          </span>
          {defect_count === 0 ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/20">
              <CheckCircle className="w-3 h-3" /> Clear
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 text-xs font-semibold border border-rose-500/20">
              <AlertCircle className="w-3 h-3" /> {defect_count} Defect{defect_count > 1 ? 's' : ''}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <div className={`px-3 py-1 rounded-lg border text-xs font-bold font-mono ${scoreBadge}`}>
            Score: {score}/100
          </div>

          {defect_count > 0 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 text-xs font-semibold border border-indigo-500/30 transition-all"
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>{expanded ? 'Hide Analysis' : 'Why? & Fix'}</span>
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>
      </div>

      {/* Requirement Statement Body with Highlights */}
      <div className="mt-4">
        <p className="text-slate-100 text-base leading-relaxed font-medium">
          "{renderHighlightedText(text, highlights)}"
        </p>
      </div>

      {/* Defect Category Badges */}
      {defect_count > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {defects.map((def, i) => {
            let catBadge = 'bg-slate-800 text-slate-300 border-slate-700';
            if (def.category === 'is_ambiguous') catBadge = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
            if (def.category === 'is_incomplete') catBadge = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
            if (def.category === 'is_untestable') catBadge = 'bg-sky-500/15 text-sky-300 border-sky-500/30';
            if (def.category === 'is_weak') catBadge = 'bg-purple-500/15 text-purple-300 border-purple-500/30';

            return (
              <span key={i} className={`px-2.5 py-1 rounded-lg border text-xs font-semibold ${catBadge}`}>
                {def.issue}
              </span>
            );
          })}
        </div>
      )}

      {/* Expandable Explainability & Rewrite Drawer */}
      {expanded && defects.length > 0 && (
        <div className="mt-5 pt-4 border-t border-slate-800 space-y-4">
          {defects.map((def, i) => (
            <div key={i} className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-white">{def.issue}</span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] uppercase font-bold text-slate-400">
                    Severity: {def.severity}
                  </span>
                </div>
              </div>

              {/* Explainability Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                  <span className="font-semibold text-rose-400 block mb-1">Issue & Reason:</span>
                  <p className="text-slate-300">{def.reason}</p>
                </div>
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                  <span className="font-semibold text-amber-400 block mb-1">Business & QA Impact:</span>
                  <p className="text-slate-300">{def.business_impact}</p>
                </div>
              </div>

              {/* Suggested Improvement / Rewrite Box */}
              <div className="p-3.5 bg-indigo-950/20 rounded-xl border border-indigo-500/30">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                    Suggested Improvement:
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleCopy(def.rewrite, i)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-medium transition-all"
                    >
                      {copiedIndex === i ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>

                    {onApplyRewrite && (
                      <button
                        type="button"
                        onClick={() => onApplyRewrite(index, def.rewrite)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-semibold shadow transition-all"
                      >
                        Apply Fix
                      </button>
                    )}
                  </div>
                </div>

                <p className="text-sm font-mono text-emerald-300 mt-1">
                  "{def.rewrite}"
                </p>
              </div>

            </div>
          ))}
        </div>
      )}

    </div>
  );
}
