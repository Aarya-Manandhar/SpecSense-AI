import React, { useState } from 'react';
import { Download, Printer, FileSpreadsheet, Check } from 'lucide-react';

export default function ReportExporter({ analysisData }) {
  const [downloading, setDownloading] = useState(false);

  if (!analysisData) return null;

  const handleExportCSV = async () => {
    setDownloading(true);
    try {
      const res = await fetch('/api/v1/export/csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(analysisData)
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `specsense_report_${analysisData.document_id || 'export'}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (err) {
      console.error('CSV Export Error:', err);
    } finally {
      setDownloading(false);
    }
  };

  const handlePrintPDF = () => {
    window.print();
  };

  return (
    <div className="w-full glass-card p-6 rounded-3xl border border-slate-800 shadow-xl mb-8 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Download className="w-4 h-4 text-indigo-400" />
          Export Intelligence Analysis Report
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">
          Download full requirement audit data in CSV spreadsheet format or export printable PDF report.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleExportCSV}
          disabled={downloading}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition-all shadow"
        >
          <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
          <span>{downloading ? 'Downloading...' : 'Export CSV'}</span>
        </button>

        <button
          type="button"
          onClick={handlePrintPDF}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 transition-all"
        >
          <Printer className="w-4 h-4" />
          <span>Export PDF Report</span>
        </button>
      </div>
    </div>
  );
}
