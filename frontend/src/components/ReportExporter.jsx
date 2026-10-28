import React, { useState } from 'react';
import { Download, Printer, FileSpreadsheet, Check } from 'lucide-react';
import { API_ENDPOINTS } from '../config';

export default function ReportExporter({ analysisData }) {
  const [downloading, setDownloading] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  if (!analysisData) return null;

  const handleExportCSV = async () => {
    setDownloading(true);
    try {
      const res = await fetch(API_ENDPOINTS.EXPORT_CSV, {
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
      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 2500);
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
    <div className="surface-card rounded-lg border border-zinc-200 px-5 py-3.5 mb-6 flex flex-wrap items-center justify-between gap-4 bg-white shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-md bg-zinc-100 border border-zinc-200 text-zinc-600 flex items-center justify-center shrink-0">
          <Download className="w-4 h-4 text-zinc-600" />
        </div>
        <div>
          <h3 className="text-xs font-semibold text-zinc-900">
            Export Audit Report
          </h3>
          <p className="text-[11px] text-zinc-500">
            Generate CSV spreadsheet for traceability matrices or print a standardized compliance summary.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={handleExportCSV}
          disabled={downloading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white hover:bg-zinc-50 text-zinc-700 text-xs font-medium border border-zinc-300 shadow-sm transition-colors disabled:opacity-50"
        >
          {downloadSuccess ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              <span>Downloaded</span>
            </>
          ) : (
            <>
              <FileSpreadsheet className="w-3.5 h-3.5 text-zinc-500" />
              <span>{downloading ? 'Exporting...' : 'Export CSV'}</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={handlePrintPDF}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-medium shadow-sm transition-colors"
        >
          <Printer className="w-3.5 h-3.5 text-zinc-300" />
          <span>Print / PDF</span>
        </button>
      </div>
    </div>
  );
}
