import React from 'react';
import { ShieldCheck, AlertTriangle, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function QualityScoreCard({ data }) {
  if (!data) return null;

  const {
    project_score,
    overall_status,
    total_requirements,
    defective_requirements_count,
    clear_percentage = 0,
    ambiguous_percentage = 0,
    incomplete_percentage = 0,
    untestable_percentage = 0,
    weak_percentage = 0,
    counts_by_category = {}
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
      description: 'Zero defects detected',
      percentage: clear_percentage,
      count: clearCount,
      color: 'bg-emerald-500',
      textColor: 'text-emerald-600',
    },
    {
      key: 'is_ambiguous',
      label: 'Ambiguity',
      description: 'Vague, subjective, or open-ended phrasing',
      percentage: ambiguous_percentage,
      count: counts_by_category.is_ambiguous || 0,
      color: 'bg-rose-500',
      textColor: 'text-rose-600',
    },
    {
      key: 'is_incomplete',
      label: 'Incompleteness',
      description: 'Missing error conditions or conditional branches',
      percentage: incomplete_percentage,
      count: counts_by_category.is_incomplete || 0,
      color: 'bg-amber-500',
      textColor: 'text-amber-600',
    },
    {
      key: 'is_untestable',
      label: 'Non-Testable',
      description: 'Subjective assertions lacking measurable verification metrics',
      percentage: untestable_percentage,
      count: counts_by_category.is_untestable || 0,
      color: 'bg-sky-500',
      textColor: 'text-sky-600',
    },
    {
      key: 'is_weak',
      label: 'Weak Modality',
      description: 'Uses optional terms ("should", "may") instead of mandatory "shall"',
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
                <p className="text-[11px] text-zinc-500">Total Statements</p>
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
          </div>

          {/* Right Column: Defect Distribution Breakdown */}
          <div className="lg:col-span-7 bg-zinc-50/70 p-4 rounded-md border border-zinc-200 space-y-3.5">
            <div className="flex items-center justify-between text-xs font-medium text-zinc-600 pb-2 border-b border-zinc-200">
              <span>Defect Distribution</span>
              <span className="font-mono text-[11px]">Incidence Rate</span>
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
      </div>
    </div>
  );
}
