import React, { useEffect, useState } from 'react'

export default function EvaluationPanel() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [rows, setRows] = useState([])
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [flagFilter, setFlagFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')

  useEffect(() => {
    loadSummary()
  }, [])

  useEffect(() => {
    loadRows()
  }, [page, flagFilter, sourceFilter])

  async function loadSummary() {
    setLoading(true)
    try {
      const res = await fetch('/api/v1/evaluation/summary')
      const data = await res.json()
      setSummary(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function loadRows() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.set('page', page)
      params.set('page_size', pageSize)
      if (flagFilter) params.set('flag', flagFilter)
      if (sourceFilter) params.set('source', sourceFilter)
      const res = await fetch('/api/v1/evaluation/rows?' + params.toString())
      const data = await res.json()
      setRows(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  function nextPage() {
    if (page * pageSize < total) setPage(p => p + 1)
  }
  function prevPage() {
    if (page > 1) setPage(p => p - 1)
  }

  return (
    <section className="mt-10 w-full max-w-5xl bg-slate-900/60 rounded-2xl p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold">Real Evaluation</h3>
          <p className="text-sm text-slate-400">Counts and Eirene precision / recall (interactive)</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={flagFilter} onChange={e=>{setFlagFilter(e.target.value); setPage(1)}} className="bg-slate-800 text-slate-200 px-3 py-1 rounded">
            <option value="">All flags</option>
            <option value="is_ambiguous">is_ambiguous</option>
            <option value="is_incomplete">is_incomplete</option>
            <option value="is_untestable">is_untestable</option>
            <option value="is_weak">is_weak</option>
          </select>
          <select value={sourceFilter} onChange={e=>{setSourceFilter(e.target.value); setPage(1)}} className="bg-slate-800 text-slate-200 px-3 py-1 rounded">
            <option value="">All sources</option>
            <option value="promise">promise</option>
            <option value="eirene">eirene</option>
          </select>
          <button onClick={()=>{setPage(1); loadSummary(); loadRows();}} className="px-3 py-1 rounded bg-indigo-600 text-white">Refresh</button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-3 bg-slate-800 rounded">
          <div className="text-sm text-slate-400">Rows evaluated</div>
          <div className="text-2xl font-bold">{summary ? summary.rows_evaluated : '—'}</div>
        </div>
        <div className="p-3 bg-slate-800 rounded">
          <div className="text-sm text-slate-400">Predicted counts (total)</div>
          <div className="mt-1 text-sm text-slate-100">
            {summary ? Object.entries(summary.counts).map(([k,v]) => (<div key={k}><strong>{k}</strong>: {v}</div>)) : '—'}
          </div>
        </div>
        <div className="p-3 bg-slate-800 rounded">
          <div className="text-sm text-slate-400">Eirene metrics</div>
          <div className="mt-2 text-sm text-slate-100">
            {summary && summary.metrics_by_source && summary.metrics_by_source.eirene ? (
              Object.entries(summary.metrics_by_source.eirene).map(([cat, m]) => (
                <div key={cat} className="mb-1">
                  <strong>{cat}</strong>: {m.annotated_count} annotated • P: {m.precision===null? '—': m.precision.toFixed(3)} • R: {m.recall===null? '—': m.recall.toFixed(3)}
                </div>
              ))
            ) : 'No annotated metrics'}
          </div>
        </div>
      </div>

      <div className="mt-6">
        <div className="overflow-x-auto">
          <table className="w-full table-auto text-left text-sm">
            <thead className="text-slate-400 text-xs">
              <tr>
                <th className="px-3 py-2">#</th>
                <th className="px-3 py-2">Text</th>
                <th className="px-3 py-2">Source</th>
                <th className="px-3 py-2">Score</th>
                <th className="px-3 py-2">Defects</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r,i) => (
                <tr key={i} className="border-t border-slate-800">
                  <td className="px-3 py-2 align-top">{(page-1)*pageSize + i + 1}</td>
                  <td className="px-3 py-2 align-top max-w-xl">{r.text}</td>
                  <td className="px-3 py-2 align-top">{r.source_key || r.source}</td>
                  <td className="px-3 py-2 align-top">{r.score}</td>
                  <td className="px-3 py-2 align-top">{(r.defects||[]).join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div className="text-sm text-slate-400">Showing page {page} — {total} total</div>
          <div className="flex items-center gap-2">
            <button onClick={prevPage} disabled={page<=1} className="px-3 py-1 rounded bg-slate-800 text-slate-200 disabled:opacity-40">Prev</button>
            <button onClick={nextPage} disabled={page*pageSize >= total} className="px-3 py-1 rounded bg-slate-800 text-slate-200 disabled:opacity-40">Next</button>
          </div>
        </div>
      </div>
    </section>
  )
}
