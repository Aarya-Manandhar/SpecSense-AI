import React, { useState, useRef } from 'react';
import { Upload, FileText, Sparkles, CheckCircle2, RefreshCw } from 'lucide-react';

const SAMPLE_BANKING_SRS = `REQ-01: The system shall encrypt all user passwords using AES-256 encryption.
REQ-02: The application should update user balance records periodically.
REQ-03: The system shall allow authorized users to access the transaction dashboard.
REQ-04: The mobile application user interface must be user-friendly and intuitive.
REQ-05: The system shall respond quickly under normal operating conditions.
REQ-06: If the user inputs an invalid password, the system shall lock the account after 3 attempts.
REQ-07: The database backup may be executed during off-peak hours if feasible.
REQ-08: The customer support portal should be robust and easy to use.`;

export default function DocumentUploader({ onAnalyzeText, onAnalyzeFile, loading }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'text'
  const [rawText, setRawText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
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

  return (
    <div className="w-full glass-card p-6 md:p-8 rounded-3xl border border-slate-800 shadow-2xl mb-8">
      {/* Mode Switcher Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 mb-6 border-b border-slate-800/80">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            SRS Input & Requirements Parser
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Upload SRS specification (PDF, DOCX, TXT) or paste raw requirement statements.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'upload'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Upload File (PDF/DOCX)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('text')}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'text'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Paste Text
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {activeTab === 'upload' ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            className="group cursor-pointer border-2 border-dashed border-slate-700/80 hover:border-indigo-500/80 bg-slate-950/40 hover:bg-indigo-950/10 p-8 rounded-2xl text-center transition-all flex flex-col items-center justify-center min-h-[200px]"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="p-4 bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 rounded-2xl group-hover:scale-110 transition-transform mb-3">
              <Upload className="w-8 h-8" />
            </div>
            {selectedFile ? (
              <div className="flex items-center gap-2 text-emerald-400 font-medium text-sm">
                <CheckCircle2 className="w-4 h-4" />
                <span>Selected: {selectedFile.name}</span>
                <span className="text-xs text-slate-500">
                  ({(selectedFile.size / 1024).toFixed(1)} KB)
                </span>
              </div>
            ) : (
              <>
                <p className="text-sm font-semibold text-slate-200">
                  Drop your SRS Document here, or <span className="text-indigo-400">Browse</span>
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Supports PDF (.pdf), Microsoft Word (.docx), Plain Text (.txt)
                </p>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            <textarea
              rows={6}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste software requirement statements here (e.g. 'The system shall respond quickly...')"
              className="w-full bg-slate-950/80 border border-slate-800 focus:border-indigo-500 rounded-2xl p-4 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono transition-all resize-none"
            />
          </div>
        )}

        {/* Action Controls & Sample Preset Button */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
          <button
            type="button"
            onClick={loadSample}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-300 text-xs font-semibold border border-slate-700/60 transition-all"
          >
            <Sparkles className="w-4 h-4 text-indigo-400" />
            Load Sample Banking SRS
          </button>

          <button
            type="submit"
            disabled={loading || (activeTab === 'upload' && !selectedFile) || (activeTab === 'text' && !rawText.trim())}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-sm font-bold shadow-lg shadow-indigo-600/30 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Analyzing Requirements...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Analyze Requirements
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
