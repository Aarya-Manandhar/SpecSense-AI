import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, ChevronDown, ChevronUp, Copy, Check, Sparkles, ArrowRight } from 'lucide-react';

export default function RequirementCard({ index, item, onApplyRewrite }) {
  const [expanded, setExpanded] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);

  const { text, score = 0, defects = [], defect_count = 0, highlights = [] } = item;

  // Separate rule-confirmed defects from ML-only advisories
  const ruleDefects = defects.filter(d => !d.is_advisory);
  const advisoryDefects = defects.filter(d => d.is_advisory);

  // Determine score status styling
  let scoreBadgeColor = 'text-emerald-700 border-emerald-200 bg-emerald-50';
  if (score < 70) {
    scoreBadgeColor = 'text-rose-700 border-rose-200 bg-rose-50';
  } else if (score < 90) {
    scoreBadgeColor = 'text-amber-800 border-amber-200 bg-amber-50';
  }

  const getSeverityBadgeStyle = (sev) => {
    switch (sev) {
      case 'Critical':
        return 'bg-rose-100 text-rose-800 border-rose-300 font-bold';
      case 'High':
        return 'bg-amber-100 text-amber-800 border-amber-300 font-bold';
      case 'Medium':
        return 'bg-sky-100 text-sky-800 border-sky-300 font-semibold';
      case 'Low':
        return 'bg-indigo-100 text-indigo-800 border-indigo-300 font-medium';
      case 'Advisory':
        return 'bg-zinc-100 text-zinc-500 border-zinc-300 font-normal italic';
      default:
        return 'bg-zinc-100 text-zinc-700 border-zinc-200';
    }
  };

  // Refined text highlighting for problematic keywords
  const renderHighlightedText = (originalText, highlightWords) => {
    if (!highlightWords || highlightWords.length === 0) {
      return <span>{originalText}</span>;
    }

    const pattern = new RegExp(`\\b(${highlightWords.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})\\b`, 'gi');
    const parts = originalText.split(pattern);

    return (
      <span>
        {parts.map((part, i) => {
          const isMatch = highlightWords.some(hw => hw.toLowerCase() === part.toLowerCase());
          if (isMatch) {
            return (
              <span
                key={i}
                className="bg-rose-50 text-rose-800 border-b-2 border-rose-400 px-1 py-0.5 rounded-xs font-medium"
                title="Problematic or non-verifiable phrasing detected"
              >
                {part}
              </span>
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

  const reqId = `REQ-${String(index + 1).padStart(2, '0')}`;

  return (
    <div
      className={`rounded-lg border transition-colors bg-white shadow-sm ${
        defect_count > 0 ? 'border-zinc-200' : 'border-zinc-200/80'
      }`}
    >
      {/* Header bar */}
      <div className="px-4 py-3 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-200 bg-zinc-50/70">
        <div className="flex items-center gap-2.5">
          <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-white border border-zinc-200 text-zinc-700 shadow-2xs">
            {reqId}
          </span>

          {defect_count === 0 ? (
            <div className="flex items-center gap-1.5">
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span>Compliant</span>
              </span>
              <span className="font-mono text-[10px] tracking-wider px-2 py-0.5 rounded bg-zinc-100 text-zinc-600 border border-zinc-200">
                [None]
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              {ruleDefects.length > 0 && (
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                  <span>{ruleDefects.length} {ruleDefects.length === 1 ? 'Defect' : 'Defects'}</span>
                </span>
              )}
              {ruleDefects.length === 0 && advisoryDefects.length > 0 && (
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Compliant</span>
                </span>
              )}
              {advisoryDefects.length > 0 && (
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-zinc-50 text-zinc-500 border border-zinc-200 italic">
                  <span>{advisoryDefects.length} {advisoryDefects.length === 1 ? 'Advisory' : 'Advisories'}</span>
                </span>
              )}
              {item.severity && item.severity !== "None" ? (
                <span className={`font-mono text-[10px] tracking-wider px-2 py-0.5 rounded border shadow-2xs ${getSeverityBadgeStyle(item.severity)}`}>
                  [{item.severity}]
                </span>
              ) : (
                <span className="font-mono text-[10px] tracking-wider px-2 py-0.5 rounded bg-zinc-100 text-zinc-600 border border-zinc-200">
                  [None]
                </span>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2.5">
          <span className={`text-xs font-mono font-medium px-2 py-0.5 rounded border ${scoreBadgeColor}`}>
            {score}/100
          </span>

          {defect_count > 0 && (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="inline-flex items-center gap-1 text-xs text-zinc-600 hover:text-zinc-900 px-2.5 py-1 rounded bg-white hover:bg-zinc-100 border border-zinc-200 transition-colors shadow-2xs"
            >
              <span>{expanded ? 'Hide Details' : 'Review Defects'}</span>
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>
      </div>

      {/* Requirement Statement */}
      <div className="p-4 sm:p-5">
        <p className="text-sm text-zinc-900 leading-relaxed font-normal">
          {renderHighlightedText(text, highlights)}
        </p>

        {/* Category tags */}
        {defect_count > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {defects.map((def, i) => (
              <span
                key={i}
                className="px-2 py-0.5 rounded text-[11px] font-medium bg-zinc-100 text-zinc-700 border border-zinc-200"
              >
                {def.issue}
              </span>
            ))}
          </div>
        )}

        {/* Expanded Defect Diagnostics & Recommended Rewrite */}
        {defects.length > 0 && (
          <div className={`mt-4 pt-4 border-t border-zinc-100 space-y-3.5 ${expanded ? 'block' : 'hidden print:block'}`}>
            {defects.map((def, i) => (
              <div key={i} className="bg-zinc-50/70 p-4 rounded-md border border-zinc-200 space-y-3 print:bg-white print:border-zinc-300">
                
                {/* Defect Header */}
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-zinc-900">{def.issue}</span>
                  {def.is_advisory ? (
                    <span className="font-mono text-[10px] tracking-wider px-1.5 py-0.5 rounded border bg-zinc-100 text-zinc-500 border-zinc-300 italic">
                      Advisory (no score impact)
                    </span>
                  ) : (
                    <span className={`font-mono text-[10px] tracking-wider px-1.5 py-0.5 rounded border ${getSeverityBadgeStyle(def.severity || 'Medium')}`}>
                      Severity: [{def.severity || 'Medium'}]
                    </span>
                  )}
                </div>

                {/* Issue and QA Impact Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded bg-white border border-zinc-200 shadow-2xs">
                    <span className="text-[11px] font-semibold text-zinc-500 block mb-1">Defect Analysis</span>
                    <p className="text-zinc-700 leading-relaxed">{def.reason}</p>
                  </div>
                  <div className="p-3 rounded bg-white border border-zinc-200 shadow-2xs">
                    <span className="text-[11px] font-semibold text-zinc-500 block mb-1">Engineering Impact</span>
                    <p className="text-zinc-700 leading-relaxed">{def.business_impact}</p>
                  </div>
                </div>

                {/* Recommended Rewrite */}
                {def.rewrite && (
                  <div className="p-3.5 rounded bg-blue-50/40 border border-blue-200/80 print:bg-zinc-50 print:border-zinc-200">
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="text-xs font-semibold text-blue-950 print:text-zinc-900 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-blue-600 print:hidden" />
                        <span>Recommended IEEE Revision:</span>
                      </span>

                      <div className="flex items-center gap-2 print:hidden">
                        <button
                          type="button"
                          onClick={() => handleCopy(def.rewrite, i)}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] text-zinc-700 hover:text-zinc-900 bg-white hover:bg-zinc-50 border border-zinc-300 shadow-2xs transition-colors"
                        >
                          {copiedIndex === i ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-600" />
                              <span>Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3 text-zinc-500" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>

                        {onApplyRewrite && (
                          <button
                            type="button"
                            onClick={() => onApplyRewrite(index, def.rewrite)}
                            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-2xs"
                          >
                            <span>Apply Fix</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>

                    <p className="text-xs font-mono text-zinc-900 leading-relaxed bg-white p-2.5 rounded border border-blue-100 print:border-zinc-300 shadow-2xs">
                      "{def.rewrite}"
                    </p>
                  </div>
                )}

              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
