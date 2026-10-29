import React, { useState } from 'react';
import { ShieldCheck, AlertTriangle, AlertCircle, CheckCircle2, HelpCircle, ChevronDown, ChevronUp, BookOpen } from 'lucide-react';

export default function QualityScoreCard({ data }) {
  if (!data) return null;

  const [showHowScoringWorks, setShowHowScoringWorks] = useState(false);

  const {
    project_score,
    health_index,
    overall_status,
    total_requirements,
    defective_requirements_count,
    clear_percentage = 0,
    ambiguous_percentage = 0,
    incomplete_percentage = 0,
    untestable_percentage = 0,
    weak_percentage = 0,
    counts_by_category = {},
    counts_by_severity = {},
    exclusion_count = 0,
    exclusion_summary = {}
  } = data;

  // Determine score status styling
  let statusBadge = {
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500',
    icon: CheckCircle2,
    scoreColor: 'text-emerald-600',
    trackColor: 'bg-emerald-500',
  };

  if (project_score < 70) {
    statusBadge = {
      bg: 'bg-rose-50 text-rose-700 border-rose-200',
      dot: 'bg-rose-500',
      icon: AlertCircle,
      scoreColor: 'text-rose-600',
      trackColor: 'bg-rose-500',
    };
  } else if (project_score < 90) {
    statusBadge = {
      bg: 'bg-amber-50 text-amber-800 border-amber-200',
      dot: 'bg-amber-500',
      icon: AlertTriangle,
      scoreColor: 'text-amber-600',
      trackColor: 'bg-amber-500',
    };
  }

  const clearCount = Math.max(0, total_requirements - defective_requirements_count);

  const defectCategories = [
    {
      key: 'clear',
      label: 'Compliant Requirements',
      description: 'Zero defects detected; meets IEEE 830 and ISO/IEC/IEEE 29148 standards',
      percentage: clear_percentage,
      count: clearCount,
      color: 'bg-emerald-500',
      textColor: 'text-emerald-600',
    },
    {
      key: 'is_ambiguous',
      label: 'Ambiguity',
      description: 'Undefined quantifiers, vague timing ("fast", "periodically", "most"), or open-ended scope ("common", "etc.", "and/or")',
      percentage: ambiguous_percentage,
      count: counts_by_category.is_ambiguous || 0,
      color: 'bg-rose-500',
      textColor: 'text-rose-600',
    },
    {
      key: 'is_incomplete',
      label: 'Incompleteness',
      description: 'Bare capabilities ("allow", "enable", "support") lacking operational parameters, input constraints, or boundary conditions',
      percentage: incomplete_percentage,
      count: counts_by_category.is_incomplete || 0,
      color: 'bg-amber-500',
      textColor: 'text-amber-600',
    },
    {
      key: 'is_untestable',
      label: 'Non-Testable',
      description: 'Subjective quality claims ("user-friendly", "securely", "gracefully", "safe") without binary pass/fail verification fixtures',
      percentage: untestable_percentage,
      count: counts_by_category.is_untestable || 0,
      color: 'bg-sky-500',
      textColor: 'text-sky-600',
    },
    {
      key: 'is_weak',
      label: 'Weak Modality',
      description: 'Non-mandatory modal verbs ("should", "may", "could", "can") or escape clauses instead of mandatory imperative "shall"',
      percentage: weak_percentage,
      count: counts_by_category.is_weak || 0,
      color: 'bg-indigo-500',
      textColor: 'text-indigo-600',
    },
  ];

  return (
    <div className="surface-card rounded-lg border border-zinc-200 mb-6 overflow-hidden bg-white shadow-sm">
      {/* Header bar */}
      <div className="px-5 py-3.5 border-b border-zinc-200 bg-zinc-50/70 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900 tracking-tight">Specification Health Assessment</h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            Quality score evaluated according to IEEE 830 and ISO/IEC/IEEE 29148 requirement engineering standards.
          </p>
        </div>
        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${statusBadge.bg}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${statusBadge.dot}`} />
          <span>{overall_status}</span>
        </div>
      </div>

      <div className="p-5">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

          {/* Left Column: Health Score Card & KPI Stats */}
          <div className="lg:col-span-5 space-y-4">
            <div className="bg-zinc-50 p-5 rounded-md border border-zinc-200 flex items-center justify-between">
              <div>
                <span className="text-xs uppercase tracking-wider text-zinc-500 font-medium">Health Index</span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className={`text-4xl font-semibold tracking-tight font-mono ${statusBadge.scoreColor}`}>
                    {project_score}
                  </span>
                  <span className="text-xs text-zinc-500 font-mono">/ 100</span>
                </div>
                <p className="text-xs text-zinc-600 mt-2">
                  {project_score >= 90
                    ? 'Specification passes production quality gates.'
                    : project_score >= 70
                      ? 'Contains moderate ambiguities requiring revision before implementation.'
                      : 'High defect density. Critical revisions recommended.'}
                </p>
              </div>

              {/* Minimal Score Ring */}
              <div className="relative w-16 h-16 shrink-0">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    className="text-zinc-200"
                    strokeWidth="3.5"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className="transition-all duration-700 ease-out"
                    strokeDasharray={`${project_score}, 100`}
                    strokeWidth="3.5"
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    style={{
                      stroke: project_score >= 90 ? '#10b981' : project_score >= 70 ? '#f59e0b' : '#f43f5e'
                    }}
                  />
                </svg>
              </div>
            </div>

            {/* 3 Metric Summary Boxes */}
            <div className="grid grid-cols-3 gap-2.5">
              <div className="bg-white p-3 rounded-md border border-zinc-200 shadow-xs">
                <p className="text-[11px] text-zinc-500">Requirements</p>
                <p className="text-lg font-semibold text-zinc-900 font-mono mt-0.5">{total_requirements}</p>
              </div>
              <div className="bg-white p-3 rounded-md border border-zinc-200 shadow-xs">
                <p className="text-[11px] text-zinc-500">Compliant</p>
                <p className="text-lg font-semibold text-emerald-600 font-mono mt-0.5">{clearCount}</p>
              </div>
              <div className="bg-white p-3 rounded-md border border-zinc-200 shadow-xs">
                <p className="text-[11px] text-zinc-500">Flagged</p>
                <p className="text-lg font-semibold text-rose-600 font-mono mt-0.5">{defective_requirements_count}</p>
              </div>
            </div>

            {/* Stage 5: Exclusion count & Scope Transparency */}
            {exclusion_count > 0 && (
              <div className="p-2.5 rounded bg-zinc-100/80 border border-zinc-200 text-[11px] text-zinc-600 flex items-center justify-between">
                <span>Non-Requirement Lines Excluded:</span>
                <span className="font-mono font-semibold text-zinc-800">{exclusion_count} items</span>
              </div>
            )}
          </div>

          {/* Right Column: Defect Distribution Breakdown */}
          <div className="lg:col-span-7 bg-zinc-50/70 p-4 rounded-md border border-zinc-200 space-y-3.5">
            <div className="flex flex-wrap items-center justify-between text-xs font-medium text-zinc-600 pb-2 border-b border-zinc-200 gap-2">
              <span>Defect Distribution & Severities</span>
              {counts_by_severity && Object.keys(counts_by_severity).length > 0 && (
                <div className="flex items-center gap-1.5 font-mono text-[10px]">
                  {counts_by_severity.Critical > 0 && (
                    <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200 font-semibold">
                      {counts_by_severity.Critical} Critical
                    </span>
                  )}
                  {counts_by_severity.High > 0 && (
                    <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200 font-semibold">
                      {counts_by_severity.High} High
                    </span>
                  )}
                  {counts_by_severity.Medium > 0 && (
                    <span className="px-1.5 py-0.5 rounded bg-sky-100 text-sky-800 border border-sky-200 font-semibold">
                      {counts_by_severity.Medium} Med
                    </span>
                  )}
                  {counts_by_severity.Low > 0 && (
                    <span className="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-800 border border-indigo-200 font-semibold">
                      {counts_by_severity.Low} Low
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className="space-y-3">
              {defectCategories.map((cat) => (
                <div key={cat.key} className="group">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full ${cat.color}`} />
                      <span className="font-medium text-zinc-800">{cat.label}</span>
                      <span className="hidden sm:inline text-[11px] text-zinc-500">— {cat.description}</span>
                    </div>
                    <div className="flex items-center gap-2 font-mono text-[11px]">
                      <span className="text-zinc-700 font-semibold">{cat.count}</span>
                      <span className="text-zinc-500">({cat.percentage}%)</span>
                    </div>
                  </div>

                  {/* Slim sleek progress meter */}
                  <div className="w-full h-1.5 bg-zinc-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${cat.color} transition-all duration-500`}
                      style={{ width: `${Math.min(100, Math.max(0, cat.percentage))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* How Scoring Works Collapsible Panel */}
        <div className="mt-5 pt-4 border-t border-zinc-200">
          <button
            type="button"
            onClick={() => setShowHowScoringWorks(!showHowScoringWorks)}
            className="w-full flex items-center justify-between text-left text-xs font-medium text-zinc-700 hover:text-zinc-900 py-1 transition-colors print:hidden"
          >
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-zinc-500" />
              <span className="font-semibold text-zinc-900">How Scoring Works (ISO/IEC/IEEE 29148 & IEEE 830)</span>
              <span className="text-[11px] text-zinc-500 hidden sm:inline">— Formula, penalty weights & quality gates</span>
            </div>
            <div className="flex items-center gap-1 text-zinc-500 text-[11px]">
              <span>{showHowScoringWorks ? 'Hide Methodology' : 'View Methodology'}</span>
              {showHowScoringWorks ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </div>
          </button>

          {/* Expanded or Print-view Content */}
          <div className={`mt-3 space-y-4 text-xs text-zinc-700 ${showHowScoringWorks ? 'block' : 'hidden print:block'}`}>
            <div className="bg-zinc-50 p-4 rounded-md border border-zinc-200 space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Column 1: Formula & Requirements Scope */}
                <div className="space-y-2">
                  <span className="font-semibold text-zinc-900 block text-[11px] uppercase tracking-wider">
                    Requirements-Only Health Index Formula
                  </span>
                  <p className="text-zinc-600 leading-relaxed text-[11px]">
                    Non-requirement boilerplate (section titles, scope paragraphs, acronym tables, revision histories) are isolated by the NLP preprocessor and excluded from penalty calculations to prevent score dilution.
                  </p>
                  <div className="p-2.5 rounded bg-white border border-zinc-200 font-mono text-[11px] text-zinc-800 space-y-1 shadow-2xs">
                    <div>Statement Score = max(0, 100 - &Sigma; Penalties)</div>
                    <div>Health Index = round( &Sigma; Statement Scores / Total Requirements )</div>
                  </div>
                </div>

                {/* Column 2: Quality Gate Thresholds */}
                <div className="space-y-2">
                  <span className="font-semibold text-zinc-900 block text-[11px] uppercase tracking-wider">
                    Quality Gate Tiers
                  </span>
                  <div className="space-y-1.5 text-[11px]">
                    <div className="flex items-center justify-between p-1.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800">
                      <span className="font-semibold">&ge; 90: Ready for Development</span>
                      <span className="font-mono">Low Risk</span>
                    </div>
                    <div className="flex items-center justify-between p-1.5 rounded bg-amber-50 border border-amber-200 text-amber-800">
                      <span className="font-semibold">70 &ndash; 89: Needs PM Review</span>
                      <span className="font-mono">Moderate Risk</span>
                    </div>
                    <div className="flex items-center justify-between p-1.5 rounded bg-rose-50 border border-rose-200 text-rose-800">
                      <span className="font-semibold">&lt; 70: Action Required</span>
                      <span className="font-mono">High Risk</span>
                    </div>
                  </div>
                </div>

              </div>

              {/* Penalty Deductions Matrix */}
              <div className="pt-3 border-t border-zinc-200">
                <span className="font-semibold text-zinc-900 block text-[11px] uppercase tracking-wider mb-2">
                  Standard Penalty Deductions & Severity Matrix
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-[11px]">
                  
                  <div className="p-2.5 rounded bg-white border border-rose-200 shadow-2xs">
                    <div className="flex items-center justify-between font-semibold text-rose-700 mb-1">
                      <span>Incompleteness</span>
                      <span className="font-mono px-1 py-0.2 rounded bg-rose-100 text-rose-800 border border-rose-300">-40 pts</span>
                    </div>
                    <span className="font-mono text-[10px] text-zinc-500 font-semibold block mb-1">[Critical Severity]</span>
                    <p className="text-zinc-600 leading-snug">
                      Bare capabilities lacking operational parameters or conditions without error/fallback handlers.
                    </p>
                  </div>

                  <div className="p-2.5 rounded bg-white border border-amber-200 shadow-2xs">
                    <div className="flex items-center justify-between font-semibold text-amber-800 mb-1">
                      <span>Ambiguity</span>
                      <span className="font-mono px-1 py-0.2 rounded bg-amber-100 text-amber-900 border border-amber-300">-30 pts</span>
                    </div>
                    <span className="font-mono text-[10px] text-zinc-500 font-semibold block mb-1">[High Severity]</span>
                    <p className="text-zinc-600 leading-snug">
                      Undefined quantifiers or subjective timing metrics ('quickly', 'periodically', 'most', 'common').
                    </p>
                  </div>

                  <div className="p-2.5 rounded bg-white border border-sky-200 shadow-2xs">
                    <div className="flex items-center justify-between font-semibold text-sky-800 mb-1">
                      <span>Non-Testable</span>
                      <span className="font-mono px-1 py-0.2 rounded bg-sky-100 text-sky-900 border border-sky-300">-20 pts</span>
                    </div>
                    <span className="font-mono text-[10px] text-zinc-500 font-semibold block mb-1">[Medium Severity]</span>
                    <p className="text-zinc-600 leading-snug">
                      Subjective qualitative terms lacking binary pass/fail verification ('user-friendly', 'securely', 'gracefully').
                    </p>
                  </div>

                  <div className="p-2.5 rounded bg-white border border-indigo-200 shadow-2xs">
                    <div className="flex items-center justify-between font-semibold text-indigo-800 mb-1">
                      <span>Weak Modality</span>
                      <span className="font-mono px-1 py-0.2 rounded bg-indigo-100 text-indigo-900 border border-indigo-300">-10 pts</span>
                    </div>
                    <span className="font-mono text-[10px] text-zinc-500 font-semibold block mb-1">[Low Severity]</span>
                    <p className="text-zinc-600 leading-snug">
                      Non-imperative verbs ('should', 'may', 'could', 'can') instead of mandatory 'shall'.
                    </p>
                  </div>

                </div>
              </div>

            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
