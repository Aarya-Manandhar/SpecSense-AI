import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, RefreshCw, AlertCircle, Play, X } from 'lucide-react';

const SAMPLE_BANKING_SRS = `REQ-01: The system shall encrypt all user passwords using AES-256 encryption.
REQ-02: The application should update user balance records periodically.
REQ-03: The system shall allow authorized users to access the transaction dashboard.
REQ-04: The mobile application user interface must be user-friendly and intuitive.
REQ-05: The system shall respond quickly under normal operating conditions.
REQ-06: If the user inputs an invalid password, the system shall lock the account after 3 attempts.
REQ-07: The database backup may be executed during off-peak hours if feasible.
REQ-08: The customer support portal should be robust and easy to use.`;

export default function DocumentUploader({ onAnalyzeText, onAnalyzeFile, loading, isOffline }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'text'
  const [rawText, setRawText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (activeTab === 'upload' && selectedFile) {
      onAnalyzeFile(selectedFile);
    } else if (activeTab === 'text' && rawText.trim() !== '') {
      onAnalyzeText(rawText);
    }
  };

  const loadSample = () => {
    setActiveTab('text');
    setRawText(SAMPLE_BANKING_SRS);
    onAnalyzeText(SAMPLE_BANKING_SRS);
  };

  const clearSelectedFile = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const isSubmitDisabled =
    loading ||
    isOffline ||
    (activeTab === 'upload' && !selectedFile) ||
    (activeTab === 'text' && !rawText.trim());

  return (
    <div className="surface-card rounded-lg border border-zinc-200 mb-6 overflow-hidden bg-white shadow-sm">
      {/* Header bar with Tab switcher */}
      <div className="px-5 py-3.5 border-b border-zinc-200 bg-zinc-50/70 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900 tracking-tight">Specification Source</h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            Upload an SRS document or paste requirements directly for automated standards compliance audit.
          </p>
        </div>

        {/* Minimal segmented toggle */}
        <div className="inline-flex p-0.5 rounded-md bg-zinc-100 border border-zinc-200 text-xs font-medium">
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`px-3 py-1.5 rounded transition-colors ${
              activeTab === 'upload'
                ? 'bg-white text-zinc-900 border border-zinc-200 shadow-sm'
                : 'text-zinc-600 hover:text-zinc-900'
            }`}
          >
            File Upload
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('text')}
            className={`px-3 py-1.5 rounded transition-colors ${
              activeTab === 'text'
                ? 'bg-white text-zinc-900 border border-zinc-200 shadow-sm'
                : 'text-zinc-600 hover:text-zinc-900'
            }`}
          >
            Direct Input
          </button>
        </div>
      </div>

      {/* Main input content */}
      <form onSubmit={handleSubmit} className="p-5 space-y-4">
        {activeTab === 'upload' ? (
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={handleFileChange}
              className="hidden"
            />

            {selectedFile ? (
              <div className="p-4 rounded-md border border-zinc-200 bg-zinc-50 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="truncate">
                    <p className="text-xs font-medium text-zinc-900 truncate">{selectedFile.name}</p>
                    <p className="text-[11px] text-zinc-500 font-mono mt-0.5">
                      {(selectedFile.size / 1024).toFixed(1)} KB • Ready for analysis
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-2.5 py-1 text-xs text-zinc-700 hover:text-zinc-900 bg-white border border-zinc-300 hover:bg-zinc-50 rounded shadow-sm transition-colors"
                  >
                    Change file
                  </button>
                  <button
                    type="button"
                    onClick={clearSelectedFile}
                    className="p-1 text-zinc-400 hover:text-zinc-700 rounded transition-colors"
                    title="Remove selected file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
                className={`cursor-pointer border border-dashed rounded-md p-8 text-center transition-all flex flex-col items-center justify-center min-h-[140px] ${
                  isDragging
                    ? 'border-blue-500 bg-blue-50/50'
                    : 'border-zinc-300 hover:border-zinc-400 bg-zinc-50/40 hover:bg-zinc-50'
                }`}
              >
                <div className="w-9 h-9 rounded-md bg-white border border-zinc-200 text-zinc-600 flex items-center justify-center mb-3 shadow-sm">
                  <Upload className="w-4 h-4 text-zinc-600" />
                </div>
                <p className="text-xs font-medium text-zinc-900">
                  Click to browse or drop SRS document here
                </p>
                <div className="flex items-center gap-1.5 mt-2 text-[11px] text-zinc-500">
                  <span>Supported formats:</span>
                  <span className="font-mono text-zinc-700 font-medium">PDF, DOCX, TXT, MD</span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div>
            <textarea
              rows={6}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste or write requirement statements (e.g., REQ-01: The system shall encrypt all user passwords using AES-256...)"
              className="w-full bg-white border border-zinc-200 focus:border-blue-500 rounded-md p-3.5 text-xs text-zinc-900 placeholder-zinc-400 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500/20 transition-colors resize-none leading-relaxed shadow-sm"
            />
            <div className="mt-1 flex items-center justify-between text-[11px] text-zinc-500 font-mono">
              <span>One statement per line or with REQ-xx prefixes</span>
              <span>{rawText.trim() ? `${rawText.split('\n').filter(Boolean).length} statements` : '0 statements'}</span>
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-zinc-100">
          <button
            type="button"
            onClick={loadSample}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white hover:bg-zinc-50 text-zinc-700 hover:text-zinc-900 text-xs font-medium border border-zinc-300 shadow-sm transition-colors disabled:opacity-50"
          >
            <Play className="w-3 h-3 text-zinc-500" />
            <span>Load Sample Spec</span>
          </button>

          <button
            type="submit"
            disabled={isSubmitDisabled}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Running Audit...</span>
              </>
            ) : isOffline ? (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-white" />
                <span>Backend Offline</span>
              </>
            ) : (
              <span>Run Specification Audit</span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
