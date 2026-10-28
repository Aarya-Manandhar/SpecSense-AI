import React, { useState, useEffect } from 'react';
import { ShieldCheck, Activity, Search, Filter, Layers, BarChart3, AlertCircle, RefreshCw, X } from 'lucide-react';
import DocumentUploader from './components/DocumentUploader';
import QualityScoreCard from './components/QualityScoreCard';
import RequirementCard from './components/RequirementCard';
import ReportExporter from './components/ReportExporter';
import EvaluationPanel from './components/EvaluationPanel';
import { API_ENDPOINTS } from './config';

export default function App() {
  const [backendStatus, setBackendStatus] = useState({ loading: true, status: 'unknown' });
  const [activeTab, setActiveTab] = useState('analyzer'); // 'analyzer' | 'benchmark'
  const [loading, setLoading] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Filter & Search states
  const [searchQuery, setSearchQuery] = useState('');
  const [defectFilter, setDefectFilter] = useState('ALL'); // 'ALL' | 'DEFECTIVE' | 'CLEAR' | category flags

  const checkHealth = () => {
    fetch(API_ENDPOINTS.HEALTH)
      .then((res) => {
        if (!res.ok) throw new Error('Backend HTTP error');
        return res.json();
      })
      .then((data) => {
        setBackendStatus({ loading: false, status: data.status || 'healthy', service: data.service });
        setErrorMessage((prev) => (prev?.includes('Engine API is offline') ? null : prev));
      })
      .catch(() => {
        setBackendStatus({ loading: false, status: 'offline' });
      });
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAnalyzeText = async (text) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch(API_ENDPOINTS.ANALYZE_TEXT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned status ${res.status}`);
      }
      const data = await res.json();
      setAnalysisData(data);
    } catch (err) {
      console.error('Analyze text failed:', err);
      setErrorMessage(
        backendStatus.status === 'offline'
          ? 'Engine API is offline. Please start the backend server to analyze requirements.'
          : `Analysis failed: ${err.message}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeFile = async (file) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(API_ENDPOINTS.ANALYZE_FILE, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned status ${res.status}`);
      }
      const data = await res.json();
      setAnalysisData(data);
    } catch (err) {
      console.error('Analyze file failed:', err);
      setErrorMessage(
        backendStatus.status === 'offline'
          ? 'Engine API is offline. Please start the backend server to process uploaded documents.'
          : `Analysis failed: ${err.message}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleApplyRewrite = (reqIndex, newText) => {
    if (!analysisData) return;
    const updatedRequirements = [...analysisData.requirements];
    updatedRequirements[reqIndex] = {
      ...updatedRequirements[reqIndex],
      text: newText,
      score: 100,
      status: 'Ready for Dev',
      defects: [],
      defect_count: 0,
      highlights: []
    };

    const totalScore = updatedRequirements.reduce((acc, curr) => acc + curr.score, 0);
    const newProjectScore = Math.round(totalScore / updatedRequirements.length);
    const defectiveCount = updatedRequirements.filter(r => r.defect_count > 0).length;

    setAnalysisData({
      ...analysisData,
      project_score: newProjectScore,
      defective_requirements_count: defectiveCount,
      requirements: updatedRequirements
    });
  };

  // Filter requirements based on search and category filters
  const filteredRequirements = (analysisData?.requirements || []).filter((req) => {
    const matchesSearch = req.text.toLowerCase().includes(searchQuery.toLowerCase());

    if (defectFilter === 'ALL') return matchesSearch;
    if (defectFilter === 'DEFECTIVE') return matchesSearch && req.defect_count > 0;
    if (defectFilter === 'CLEAR') return matchesSearch && req.defect_count === 0;

    const hasCategory = req.defects.some(d => d.category === defectFilter);
    return matchesSearch && hasCategory;
  });

  return (
    <div className="min-h-screen bg-[#f8fafc] text-zinc-900 flex flex-col font-sans antialiased selection:bg-blue-600/10 selection:text-blue-700">

      {/* Top Application Header */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-zinc-200 px-6 py-3">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4">
          
          {/* Logo & Product Identity */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center font-bold text-sm tracking-tight">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-zinc-900 tracking-tight">SpecSense</span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-100 text-zinc-600 border border-zinc-200">
                  v1.0
                </span>
              </div>
              <p className="text-[11px] text-zinc-500 hidden sm:block">SRS Quality Assurance & Standards Verification</p>
            </div>
          </div>

          {/* Segmented Navigation Tabs */}
          <div className="inline-flex p-0.5 rounded-md bg-zinc-100 border border-zinc-200 text-xs font-medium">
            <button
              onClick={() => setActiveTab('analyzer')}
              className={`px-3 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
                activeTab === 'analyzer'
                  ? 'bg-white text-zinc-900 border border-zinc-200 shadow-sm'
                  : 'text-zinc-600 hover:text-zinc-900'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Specification Audit</span>
            </button>

            <button
              onClick={() => setActiveTab('benchmark')}
              className={`px-3 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
                activeTab === 'benchmark'
                  ? 'bg-white text-zinc-900 border border-zinc-200 shadow-sm'
                  : 'text-zinc-600 hover:text-zinc-900'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Dataset Benchmarks</span>
            </button>
          </div>

          {/* Service Status Badge */}
          <div className="flex items-center gap-2 text-xs">
            {backendStatus.loading ? (
              <span className="text-zinc-500 font-mono text-[11px] flex items-center gap-1.5">
                <RefreshCw className="w-3 h-3 animate-spin text-zinc-400" /> Connecting
              </span>
            ) : backendStatus.status === 'healthy' ? (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 font-mono text-[11px]">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span>Engine Online</span>
              </div>
            ) : (
              <button
                onClick={checkHealth}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-rose-50 border border-rose-200 text-rose-700 font-mono text-[11px] hover:border-rose-300 transition-colors"
                title="Click to retry connection"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                <span>Offline (Retry)</span>
              </button>
            )}
          </div>

        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">

        {/* Offline Warning Banner */}
        {backendStatus.status === 'offline' && (
          <div className="mb-6 p-4 rounded-md bg-rose-50 border border-rose-200 flex items-start justify-between gap-3 text-xs">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-rose-900">Backend Engine Offline</p>
                <p className="text-zinc-600 mt-0.5 leading-relaxed">
                  Start the FastAPI backend with <code className="bg-white px-1.5 py-0.5 rounded text-blue-700 font-mono border border-zinc-200">uvicorn app.main:app --port 8000</code> to enable live IEEE specification inspection.
                </p>
              </div>
            </div>
            <button
              onClick={checkHealth}
              className="px-2.5 py-1 rounded text-xs text-rose-700 hover:text-rose-900 bg-white hover:bg-rose-100 border border-rose-300 shrink-0 transition-colors font-medium"
            >
              Retry
            </button>
          </div>
        )}

        {/* Dismissible Error Alert */}
        {errorMessage && (
          <div className="mb-6 p-3.5 rounded-md bg-amber-50 border border-amber-200 flex items-center justify-between gap-3 text-xs text-amber-900">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-zinc-500 hover:text-zinc-800 p-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {activeTab === 'analyzer' ? (
          <div>
            {/* Page Header */}
            <div className="mb-6 pb-5 border-b border-zinc-200 flex flex-wrap items-end justify-between gap-4">
              <div>
                <h1 className="text-xl font-semibold text-zinc-900 tracking-tight">
                  Specification Quality Audit
                </h1>
                <p className="mt-1 text-xs text-zinc-500">
                  Automated static verification against IEEE 830 and ISO/IEC/IEEE 29148 standards.
                </p>
              </div>

              {/* Quiet rule tags */}
              <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono text-zinc-600">
                <span className="px-2 py-0.5 rounded bg-white border border-zinc-200 shadow-sm">Ambiguity</span>
                <span className="px-2 py-0.5 rounded bg-white border border-zinc-200 shadow-sm">Incompleteness</span>
                <span className="px-2 py-0.5 rounded bg-white border border-zinc-200 shadow-sm">Non-Testable</span>
                <span className="px-2 py-0.5 rounded bg-white border border-zinc-200 shadow-sm">Weak Modals</span>
              </div>
            </div>

            {/* Document Uploader */}
            <DocumentUploader
              onAnalyzeText={handleAnalyzeText}
              onAnalyzeFile={handleAnalyzeFile}
              loading={loading}
              isOffline={backendStatus.status === 'offline'}
            />

            {/* Analysis Results View */}
            {analysisData && (
              <div className="space-y-6">
                
                {/* Score & Health Dashboard */}
                <QualityScoreCard data={analysisData} />

                {/* Export Report Actions Bar */}
                <ReportExporter analysisData={analysisData} />

                {/* Requirements Inspection Log */}
                <div className="surface-card rounded-lg border border-zinc-200 overflow-hidden bg-white shadow-sm">
                  
                  {/* Log Header & Filter Controls */}
                  <div className="px-5 py-3.5 border-b border-zinc-200 bg-zinc-50/70 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-xs font-semibold text-zinc-900">
                        Requirement Inspection Log
                      </h2>
                      <p className="text-[11px] text-zinc-500 mt-0.5">
                        Showing {filteredRequirements.length} of {analysisData.total_requirements} statements. Select any item to review defects and IEEE rewrites.
                      </p>
                    </div>

                    {/* Filter and Search Bar */}
                    <div className="flex items-center gap-2">
                      {/* Search Input */}
                      <div className="relative">
                        <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Search statements..."
                          className="bg-white border border-zinc-200 focus:border-blue-500 pl-8 pr-7 py-1 rounded-md text-xs text-zinc-800 placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-blue-500/20 w-44 sm:w-56 transition-colors shadow-sm"
                        />
                        {searchQuery && (
                          <button
                            onClick={() => setSearchQuery('')}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        )}
                      </div>

                      {/* Defect Filter Dropdown */}
                      <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-md border border-zinc-200 text-xs shadow-sm">
                        <Filter className="w-3 h-3 text-zinc-400" />
                        <select
                          value={defectFilter}
                          onChange={(e) => setDefectFilter(e.target.value)}
                          className="bg-transparent text-zinc-800 font-medium focus:outline-none cursor-pointer"
                        >
                          <option value="ALL">All Statements</option>
                          <option value="DEFECTIVE">Defective Only</option>
                          <option value="CLEAR">Compliant Only</option>
                          <option value="is_ambiguous">Ambiguity</option>
                          <option value="is_incomplete">Incompleteness</option>
                          <option value="is_untestable">Non-Testable</option>
                          <option value="is_weak">Weak Modality</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Requirements List */}
                  <div className="p-5 space-y-3">
                    {filteredRequirements.length === 0 ? (
                      <div className="py-12 text-center text-zinc-400 text-xs">
                        No requirement statements match the current filter or search query.
                      </div>
                    ) : (
                      filteredRequirements.map((req, idx) => (
                        <RequirementCard
                          key={idx}
                          index={idx}
                          item={req}
                          onApplyRewrite={handleApplyRewrite}
                        />
                      ))
                    )}
                  </div>

                </div>

              </div>
            )}
          </div>
        ) : (
          <div>
            <div className="mb-6 p-4 rounded-md bg-white border border-zinc-200 shadow-sm flex items-start gap-3 text-xs text-zinc-800">
              <div className="w-5 h-5 rounded bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center shrink-0 mt-0.5">
                <BarChart3 className="w-3 h-3" />
              </div>
              <div className="leading-relaxed">
                <span className="font-semibold text-zinc-900 block mb-0.5">Ground-Truth Benchmark Mode</span>
                <p className="text-zinc-500">
                  This panel evaluates model precision and recall against academic datasets (PROMISE NFR & EIRENE). For standard SRS audits, switch back to the <strong className="text-zinc-800">Specification Audit</strong> tab.
                </p>
              </div>
            </div>

            <EvaluationPanel />
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-200 py-4 px-6 text-center text-[11px] text-zinc-500 font-mono bg-white">
        SpecSense AI • Requirements Quality & Static Analysis Engine
      </footer>

    </div>
  );
}
