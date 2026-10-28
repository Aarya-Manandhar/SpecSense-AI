// Production-configurable API Base URL
// In development, empty string leverages Vite's proxy (/api -> http://127.0.0.1:8000)
// In production, can be set to https://api.specsense.yourdomain.com via VITE_API_URL
export const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

export const API_ENDPOINTS = {
  HEALTH: `${API_BASE}/api/v1/health`,
  ANALYZE_TEXT: `${API_BASE}/api/v1/analyze-text`,
  ANALYZE_FILE: `${API_BASE}/api/v1/analyze`,
  EXPORT_CSV: `${API_BASE}/api/v1/export/csv`,
  EVALUATION_SUMMARY: `${API_BASE}/api/v1/evaluation/summary`,
  EVALUATION_ROWS: `${API_BASE}/api/v1/evaluation/rows`,
};
