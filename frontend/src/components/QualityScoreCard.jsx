import React from 'react';
import { Award, ShieldAlert, CheckCircle, AlertTriangle, HelpCircle } from 'lucide-react';

export default function QualityScoreCard({ data }) {
  if (!data) return null;

  const {
    project_score,
    overall_status,
    total_requirements,
    defective_requirements_count,
    threshold_category,
    clear_percentage,
    ambiguous_percentage,
    incomplete_percentage,
    untestable_percentage,
    weak_percentage,
    counts_by_category = {}
  } = data;

  // Determine color theme based on score
  let scoreColor = 'from-emerald-500 to-teal-400 text-emerald-400';
  let badgeBg = 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300';
  if (project_score < 70) {
    scoreColor = 'from-rose-500 to-amber-500 text-rose-400';
    badgeBg = 'bg-rose-500/10 border-rose-500/30 text-rose-300';
  } else if (project_score < 90) {
    scoreColor = 'from-amber-400 to-yellow-300 text-amber-400';
    badgeBg = 'bg-amber-500/10 border-amber-500/30 text-amber-300';
  }

  const clearCount = total_requirements - defective_requirements_count;

  return (
    <div className="w-full glass-card p-6 md:p-8 rounded-3xl border border-slate-800 shadow-2xl mb-8">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        
        {/* Requirement Quality Score Gauge / Circle */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center p-6 bg-slate-950/60 rounded-2xl border border-slate-800/80 text-center">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-1.5">
            <Award className="w-4 h-4 text-indigo-400" />
            Requirement Quality Score™
          </p>

          <div className="relative w-40 h-40 flex items-center justify-center">
            {/* SVG Progress Ring */}
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-slate-800"
                strokeWidth="3.5"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className={`transition-all duration-1000 ease-out`}
                strokeDasharray={`${project_score}, 100`}
                strokeWidth="3.5"
                strokeLinecap="round"
                stroke="url(#scoreGradient)"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor={project_score >= 90 ? '#10b981' : project_score >= 70 ? '#f59e0b' : '#f43f5e'} />
                  <stop offset="100%" stopColor={project_score >= 90 ? '#14b8a6' : project_score >= 70 ? '#eab308' : '#fb923c'} />
                </linearGradient>
              </defs>
            </svg>

            <div className="absolute flex flex-col items-center justify-center">
              <span className={`text-4xl font-black tracking-tight bg-gradient-to-br ${scoreColor} bg-clip-text text-transparent`}>
                {project_score}
              </span>
              <span className="text-xs text-slate-500 font-semibold mt-0.5">/ 100</span>
            </div>
          </div>

          {/* Overall Risk Status Badge */}
          <div className={`mt-5 px-4 py-1.5 rounded-full border text-xs font-bold flex items-center gap-1.5 ${badgeBg}`}>
            {project_score >= 90 ? (
              <CheckCircle className="w-3.5 h-3.5" />
            ) : (
              <ShieldAlert className="w-3.5 h-3.5" />
            )}
            <span>{overall_status}</span>
          </div>
        </div>

        {/* Breakdown Statistics & Defect Category Bars */}
        <div className="lg:col-span-7 space-y-5">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800">
              <p className="text-xs text-slate-400 font-medium">Total Requirements</p>
              <p className="text-xl font-bold text-white mt-1">{total_requirements}</p>
            </div>
            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800">
              <p className="text-xs text-emerald-400 font-medium">Clear / Ready</p>
              <p className="text-xl font-bold text-emerald-400 mt-1">{clearCount}</p>
            </div>
            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800 col-span-2 sm:col-span-1">
              <p className="text-xs text-rose-400 font-medium">Flagged Defects</p>
              <p className="text-xl font-bold text-rose-400 mt-1">{defective_requirements_count}</p>
            </div>
          </div>

          {/* Defect Category Distribution Progress Bars */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-semibold mb-1">
              <span>Quality Defect Breakdown</span>
              <span>Distribution</span>
            </div>

            {/* Clear Requirements Bar */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Clear Requirements
                </span>
                <span className="text-slate-400 font-mono">{clear_percentage}%</span>
              </div>
              <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 transition-all duration-700" style={{ width: `${clear_percentage}%` }}></div>
              </div>
            </div>

            {/* Ambiguous Bar */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> 🔴 Ambiguous (Vague / Unmeasurable)
                </span>
                <span className="text-slate-400 font-mono">{ambiguous_percentage}% ({counts_by_category.is_ambiguous || 0})</span>
              </div>
              <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                <div className="h-full bg-rose-500 transition-all duration-700" style={{ width: `${ambiguous_percentage}%` }}></div>
              </div>
            </div>

            {/* Incomplete Bar */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> 🟠 Incomplete (Missing Exceptions)
                </span>
                <span className="text-slate-400 font-mono">{incomplete_percentage}% ({counts_by_category.is_incomplete || 0})</span>
              </div>
              <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                <div className="h-full bg-amber-500 transition-all duration-700" style={{ width: `${incomplete_percentage}%` }}></div>
              </div>
            </div>

            {/* Non-testable Bar */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-500"></span> 🔵 Non-Testable (Subjective Terms)
                </span>
                <span className="text-slate-400 font-mono">{untestable_percentage}% ({counts_by_category.is_untestable || 0})</span>
              </div>
              <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                <div className="h-full bg-sky-500 transition-all duration-700" style={{ width: `${untestable_percentage}%` }}></div>
              </div>
            </div>

            {/* Weak Wording Bar */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span> 🟣 Weak Phrasing (Non-Mandatory Verbs)
                </span>
                <span className="text-slate-400 font-mono">{weak_percentage}% ({counts_by_category.is_weak || 0})</span>
              </div>
              <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                <div className="h-full bg-purple-500 transition-all duration-700" style={{ width: `${weak_percentage}%` }}></div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}
