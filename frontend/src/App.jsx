import React, { useState, useEffect } from 'react';
import { ShieldCheck, Activity, Search, Filter, Layers, BarChart3, Sparkles, FileText, CheckCircle2 } from 'lucide-react';
import DocumentUploader from './components/DocumentUploader';
import QualityScoreCard from './components/QualityScoreCard';
import RequirementCard from './components/RequirementCard';
import ReportExporter from './components/ReportExporter';
import EvaluationPanel from './components/EvaluationPanel';

export default function App() {
  const [backendStatus, setBackendStatus] = useState({ loading: true, status: 'unknown' });
  const [activeTab, setActiveTab] = useState('analyzer'); // 'analyzer' | 'benchmark'
  const [loading, setLoading] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  
  // Filter & Search states
  const [searchQuery, setSearchQuery] = useState('');
  const [defectFilter, setDefectFilter] = useState('ALL'); // 'ALL' | 'DEFECTIVE' | 'CLEAR' | 'is_ambiguous' | 'is_incomplete' | 'is_untestable' | 'is_weak'

  useEffect(() => {
    fetch('/api/v1/health')
      .then((res) => res.json())
      .then((data) => {
        setBackendStatus({ loading: false, status: data.status, service: data.service });
      })
      .catch((err) => {
        console.error('Health check failed:', err);
        setBackendStatus({ loading: false, status: 'disconnected' });
      });
  }, []);

  const handleAnalyzeText = async (text) => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/analyze-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      setAnalysisData(data);
    } catch (err) {
      console.error('Analyze text failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeFile = async (file) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/v1/analyze', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setAnalysisData(data);
    } catch (err) {
      console.error('Analyze file failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyRewrite = (reqIndex, newText) => {
    if (!analysisData) return;
    const updatedRequirements = [...analysisData.requirements];
    
    // Replace text of requirement and reset its defects to clear
    updatedRequirements[reqIndex] = {
      ...updatedRequirements[reqIndex],
      text: newText,
      score: 100,
      status: 'Ready for Dev',
      defects: [],
      defect_count: 0,
      highlights: []
    };

    // Recalculate score & counts
    const totalScore = updatedRequirements.reduce((acc, curr) => acc + curr.score, 0);
    const newProjectScore = round(totalScore / updatedRequirements.length);
    const defectiveCount = updatedRequirements.filter(r => r.defect_count > 0).length;

    setAnalysisData({
      ...analysisData,
      project_score: newProjectScore,
      defective_requirements_count: defectiveCount,
      requirements: updatedRequirements
    });
  };

  function round(val) {
    return Math.round(val);
  }

  // Filter requirements based on search and category filters
  const filteredRequirements = (analysisData?.requirements || []).filter((req) => {
    const matchesSearch = req.text.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (defectFilter === 'ALL') return matchesSearch;
    if (defectFilter === 'DEFECTIVE') return matchesSearch && req.defect_count > 0;
    if (defectFilter === 'CLEAR') return matchesSearch && req.defect_count === 0;
    
    // Category specific filters
    const hasCategory = req.defects.some(d => d.category === defectFilter);
    return matchesSearch && hasCategory;
  });

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-['Inter',sans-serif]">
      
      {/* Top Navigation Header */}
      <header className="glass-panel sticky top-0 z-50 px-6 py-4 flex flex-wrap items-center justify-between border-b border-slate-800 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-600/20 rounded-2xl border border-indigo-500/30 text-indigo-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-black text-xl tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent flex items-center gap-2">
              SpecSense <span className="text-indigo-400">AI</span>
            </h1>
            <p className="text-xs text-slate-400 font-medium">Pre-Development Requirements Intelligence Platform</p>
          </div>
        </div>

        {/* Center Tab Switcher */}
        <div className="flex items-center gap-1.5 bg-slate-950/80 p-1 rounded-2xl border border-slate-800">
          <button
            onClick={() => setActiveTab('analyzer')}
            className={`px-4 py-2 text-xs font-bold rounded-xl transition-all flex items-center gap-2 ${
              activeTab === 'analyzer'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Requirements Analyzer</span>
          </button>
          <button
            onClick={() => setActiveTab('benchmark')}
            className={`px-4 py-2 text-xs font-bold rounded-xl transition-all flex items-center gap-2 ${
              activeTab === 'benchmark'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>PROMISE & EIRENE Benchmark</span>
          </button>
        </div>

        {/* Backend System Status Badge */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-950/80 border border-slate-800 text-xs">
          <Activity className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
          <span className="text-slate-400">Engine API:</span>
          {backendStatus.loading ? (
            <span className="text-amber-400 font-medium">Connecting...</span>
          ) : backendStatus.status === 'healthy' ? (
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Ready
            </span>
          ) : (
            <span className="text-rose-400 font-medium">Offline</span>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        
        {activeTab === 'analyzer' ? (
          <div>
            {/* Hero Subheader */}
            <div className="text-center max-w-3xl mx-auto mb-10">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-4">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>Pre-Development Quality Assurance for Software SRS</span>
              </div>
              <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight leading-tight">
                Analyze Requirements Before Writing Single Line of Code
              </h2>
              <p className="mt-3 text-sm md:text-base text-slate-400 font-normal leading-relaxed">
                Detect ambiguity 🔴, incompleteness 🟠, non-testability 🔵, and weak wording 🟣 to eliminate costly miscommunications and rework.
              </p>
            </div>

            {/* Document Uploader Component */}
            <DocumentUploader
              onAnalyzeText={handleAnalyzeText}
              onAnalyzeFile={handleAnalyzeFile}
              loading={loading}
            />

            {/* Quality Intelligence Dashboard Results */}
            {analysisData && (
              <div className="space-y-8">
                
                {/* Score Gauge & Breakdown Metrics */}
                <QualityScoreCard data={analysisData} />

                {/* Report Exporter Bar */}
                <ReportExporter analysisData={analysisData} />

                {/* Requirements Inspector Section Header */}
                <div className="glass-card p-6 md:p-8 rounded-3xl border border-slate-800 shadow-xl space-y-6">
                  
                  <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
                    <div>
                      <h3 className="text-xl font-extrabold text-white flex items-center gap-2">
                        <Layers className="w-5 h-5 text-indigo-400" />
                        Requirements Audit Inspector
                      </h3>
                      <p className="text-xs text-slate-400 mt-1">
                        Showing {filteredRequirements.length} of {analysisData.total_requirements} requirement items. Click "Why? & Fix" to view detailed root cause and rewrites.
                      </p>
                    </div>

                    {/* Search & Defect Filter Controls */}
                    <div className="flex flex-wrap items-center gap-3">
                      {/* Search Bar */}
                      <div className="relative">
                        <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Search requirements..."
                          className="bg-slate-950/80 border border-slate-800 focus:border-indigo-500 pl-9 pr-4 py-2 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-48 sm:w-64 transition-all"
                        />
                      </div>

                      {/* Filter Dropdown */}
                      <div className="flex items-center gap-1.5 bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
                        <Filter className="w-3.5 h-3.5 text-indigo-400" />
                        <select
                          value={defectFilter}
                          onChange={(e) => setDefectFilter(e.target.value)}
                          className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer"
                        >
                          <option value="ALL" className="bg-slate-900">All Requirements</option>
                          <option value="DEFECTIVE" className="bg-slate-900">Flagged Defects Only</option>
                          <option value="CLEAR" className="bg-slate-900">Clear Requirements Only</option>
                          <option value="is_ambiguous" className="bg-slate-900">🔴 Ambiguous</option>
                          <option value="is_incomplete" className="bg-slate-900">🟠 Incomplete</option>
                          <option value="is_untestable" className="bg-slate-900">🔵 Non-Testable</option>
                          <option value="is_weak" className="bg-slate-900">🟣 Weak Wording</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Requirements List */}
                  <div className="space-y-4">
                    {filteredRequirements.length === 0 ? (
                      <div className="p-8 text-center bg-slate-950/40 rounded-2xl border border-slate-800/60">
                        <p className="text-sm font-semibold text-slate-400">No requirements match the current filter or search criteria.</p>
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
          <div className="flex flex-col items-center">
            <EvaluationPanel />
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-slate-800/80 text-center text-xs text-slate-500 font-medium">
        SpecSense AI — Pre-Development Quality Assurance Engine for Software Requirements
      </footer>
    </div>
  );
}
