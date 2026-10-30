import React, { useEffect, useState } from 'react';
import { RefreshCw, Filter, Database, CheckCircle2, ChevronLeft, ChevronRight, BarChart2 } from 'lucide-react';
import { API_ENDPOINTS } from '../config';

export default function EvaluationPanel() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [flagFilter, setFlagFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');

  useEffect(() => {
    loadSummary();
  }, []);

  useEffect(() => {
    loadRows();
  }, [page, flagFilter, sourceFilter]);

  async function loadSummary() {
    try {
      const res = await fetch(API_ENDPOINTS.EVALUATION_SUMMARY);
      if (res.ok) {
        const data = await res.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Failed to load evaluation summary:', err);
    }
  }

  async function loadRows() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('page', page);
      params.set('page_size', pageSize);
      if (flagFilter) params.set('flag', flagFilter);
      if (sourceFilter) params.set('source', sourceFilter);
      const res = await fetch(`${API_ENDPOINTS.EVALUATION_ROWS}?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setRows(data.items || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error('Failed to load evaluation rows:', err);
    } finally {
      setLoading(false);
    }
  }

  function nextPage() {
    if (page * pageSize < total) setPage(p => p + 1);
  }
  function prevPage() {
    if (page > 1) setPage(p => p - 1);
  }

  const eireneMetrics = summary?.metrics_by_source?.eirene || {};

  return (
    <div className="w-full max-w-6xl space-y-6">
      
      {/* Top Benchmark KPI & Performance Overview */}
      <div className="surface-card rounded-lg border border-zinc-200 overflow-hidden bg-white shadow-sm">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-zinc-200 bg-zinc-50/70 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center">
              <Database className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-zinc-900">Dataset Validation & Benchmarks</h2>
              <p className="text-xs text-zinc-500">
                Cross-validated evaluation against PROMISE NFR and EIRENE labeled requirement corpora.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => { setPage(1); loadSummary(); loadRows(); }}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white hover:bg-zinc-50 text-zinc-700 text-xs font-medium border border-zinc-300 shadow-2xs transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-zinc-400' : 'text-zinc-500'}`} />
            <span>Reload Metrics</span>
          </button>
        </div>

        {/* 3 Metric Cards */}
        <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Total Corpus Statements */}
          <div className="bg-zinc-50 p-4 rounded-md border border-zinc-200">
            <p className="text-xs font-medium text-zinc-500">Corpus Statements Evaluated</p>
            <p className="text-3xl font-semibold text-zinc-900 font-mono mt-1">
              {summary ? summary.rows_evaluated?.toLocaleString() : '—'}
            </p>
            <p className="text-[11px] text-zinc-500 mt-2">
              Combined sample size across PROMISE and EIRENE benchmark sources.
            </p>
          </div>

          {/* Predicted Counts by Class */}
          <div className="bg-zinc-50 p-4 rounded-md border border-zinc-200">
            <p className="text-xs font-medium text-zinc-500 mb-2">Predicted Defect Distribution</p>
            {summary && summary.counts ? (
              <div className="space-y-1.5 font-mono text-xs">
                {Object.entries(summary.counts).map(([flag, cnt]) => (
                  <div key={flag} className="flex items-center justify-between py-0.5 border-b border-zinc-200/60 last:border-0">
                    <span className="text-zinc-600 font-sans">{flag.replace('is_', '')}</span>
                    <span className="text-zinc-900 font-semibold">{cnt}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-zinc-500">Loading metrics...</div>
            )}
          </div>

          {/* Eirene Ground Truth Precision & Recall */}
          <div className="bg-zinc-50 p-4 rounded-md border border-zinc-200">
            <p className="text-xs font-medium text-zinc-500 mb-2">EIRENE Ground-Truth Validation</p>
            {Object.keys(eireneMetrics).length > 0 ? (
              <div className="space-y-1.5 text-xs">
                {Object.entries(eireneMetrics).map(([cat, m]) => (
                  <div key={cat} className="flex items-center justify-between py-0.5 border-b border-zinc-200/60 last:border-0">
                    <span className="text-zinc-700 font-medium">{cat}</span>
                    <div className="flex items-center gap-2 font-mono text-[11px] text-zinc-600">
                      <span>P: <strong className="text-zinc-900">{m.precision === null ? '—' : m.precision.toFixed(2)}</strong></span>
                      <span>R: <strong className="text-zinc-900">{m.recall === null ? '—' : m.recall.toFixed(2)}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-zinc-500">No annotated ground-truth metrics available.</p>
            )}
          </div>
        </div>

        <div className="px-5 pb-5">
          <aside className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-950">
            <h3 className="font-semibold">Evaluation limitations</h3>
            <p className="mt-1">
              Classifiers were trained on synthetic requirements. In the current EIRENE annotated sample,
              ambiguity reached 0.25 precision / 0.39 recall (199 annotations), weak modality reached 0.07
              precision (30 annotations), and incompleteness had no true positives (59 annotations).
              Untestability has no annotated EIRENE examples. Treat these results as an early validation signal;
              performance may transfer poorly to other real SRS documents.
            </p>
          </aside>
        </div>
      </div>

      {/* Benchmark Exploration Table */}
      <div className="surface-card rounded-lg border border-zinc-200 overflow-hidden bg-white shadow-sm">
        {/* Table Filters Toolbar */}
        <div className="px-5 py-3 border-b border-zinc-200 bg-zinc-50/70 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-semibold text-zinc-900">Evaluated Statements Explorer</h3>
            <span className="text-[11px] font-mono text-zinc-500">({total.toLocaleString()} total entries)</span>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-md border border-zinc-200 text-xs shadow-2xs">
              <Filter className="w-3 h-3 text-zinc-400" />
              <select
                value={flagFilter}
                onChange={(e) => { setFlagFilter(e.target.value); setPage(1); }}
                className="bg-transparent text-zinc-800 font-medium focus:outline-none cursor-pointer"
              >
                <option value="">All Defect Flags</option>
                <option value="is_ambiguous">Ambiguity</option>
                <option value="is_incomplete">Incompleteness</option>
                <option value="is_untestable">Untestable</option>
                <option value="is_weak">Weak Modality</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-md border border-zinc-200 text-xs shadow-2xs">
              <select
                value={sourceFilter}
                onChange={(e) => { setSourceFilter(e.target.value); setPage(1); }}
                className="bg-transparent text-zinc-800 font-medium focus:outline-none cursor-pointer"
              >
                <option value="">All Benchmark Datasets</option>
                <option value="promise">PROMISE Dataset</option>
                <option value="eirene">EIRENE Dataset</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-50 text-zinc-500 font-mono uppercase text-[10px] tracking-wider border-b border-zinc-200">
              <tr>
                <th className="px-4 py-2.5 w-14">#</th>
                <th className="px-4 py-2.5">Requirement Statement</th>
                <th className="px-4 py-2.5 w-28">Source</th>
                <th className="px-4 py-2.5 w-20">Score</th>
                <th className="px-4 py-2.5 w-44">Flags</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                    <RefreshCw className="w-4 h-4 animate-spin mx-auto mb-2 text-zinc-400" />
                    <span>Loading benchmark records...</span>
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                    No benchmark records found matching the active filter criteria.
                  </td>
                </tr>
              ) : (
                rows.map((r, i) => {
                  const globalIdx = (page - 1) * pageSize + i + 1;
                  return (
                    <tr key={i} className="hover:bg-zinc-50/80 transition-colors">
                      <td className="px-4 py-3 align-top font-mono text-zinc-500 text-[11px]">
                        {String(globalIdx).padStart(3, '0')}
                      </td>
                      <td className="px-4 py-3 align-top text-zinc-800 leading-relaxed font-normal">
                        {r.text}
                      </td>
                      <td className="px-4 py-3 align-top">
                        <span className="font-mono text-[10px] uppercase px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-700 border border-zinc-200">
                          {r.source_key || r.source}
                        </span>
                      </td>
                      <td className="px-4 py-3 align-top font-mono text-zinc-800 font-medium">
                        {r.score ?? '—'}
                      </td>
                      <td className="px-4 py-3 align-top">
                        <div className="flex flex-wrap gap-1">
                          {(r.defects || []).length > 0 ? (
                            r.defects.map((def, dIdx) => (
                              <span
                                key={dIdx}
                                className="px-1.5 py-0.5 rounded text-[10px] bg-rose-50 text-rose-700 border border-rose-200 font-mono"
                              >
                                {def.replace('is_', '')}
                              </span>
                            ))
                          ) : (
                            <span className="text-zinc-400 text-[11px]">—</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-5 py-3 border-t border-zinc-200 bg-zinc-50/70 flex items-center justify-between text-xs text-zinc-500">
          <span>
            Showing <strong className="text-zinc-800">{Math.min(total, (page - 1) * pageSize + 1)}</strong> to{' '}
            <strong className="text-zinc-800">{Math.min(total, page * pageSize)}</strong> of{' '}
            <strong className="text-zinc-800">{total.toLocaleString()}</strong> entries
          </span>

          <div className="flex items-center gap-1.5">
            <button
              onClick={prevPage}
              disabled={page <= 1}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-white hover:bg-zinc-50 text-zinc-700 hover:text-zinc-900 border border-zinc-300 shadow-2xs disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>
            <span className="px-2 font-mono text-[11px] text-zinc-600">
              Page {page} of {Math.max(1, Math.ceil(total / pageSize))}
            </span>
            <button
              onClick={nextPage}
              disabled={page * pageSize >= total}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-white hover:bg-zinc-50 text-zinc-700 hover:text-zinc-900 border border-zinc-300 shadow-2xs disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
