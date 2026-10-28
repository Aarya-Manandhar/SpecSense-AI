import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
repo_root = Path(__file__).resolve().parents[2]
for directory in (backend_dir, repo_root):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError:
    from backend.app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_analyze_text():
    sample_text = (
        "The system shall encrypt all user passwords using AES-256 algorithm.\n"
        "The application should update user records periodically.\n"
        "The user interface must be user-friendly."
    )
    response = client.post("/api/v1/analyze-text", json={"text": sample_text})
    assert response.status_code == 200
    data = response.json()
    assert "project_score" in data
    assert data["total_requirements"] == 3
    assert len(data["requirements"]) == 3
    assert "clear_percentage" in data
    assert "ambiguous_percentage" in data
    assert "weak_percentage" in data
    assert "untestable_percentage" in data

def test_analyze_file_txt():
    content = "The system shall respond quickly.\nThe admin may delete accounts."
    files = {"file": ("test_srs.txt", content.encode("utf-8"), "text/plain")}
    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["total_requirements"] == 2
    assert data["defective_requirements_count"] > 0

def test_export_csv():
    payload = {
        "document_id": "test_doc",
        "project_score": 75,
        "overall_status": "Needs PM Review",
        "total_requirements": 1,
        "defective_requirements_count": 1,
        "threshold_category": "Moderate Risk",
        "clear_percentage": 0,
        "ambiguous_percentage": 100,
        "incomplete_percentage": 0,
        "untestable_percentage": 0,
        "weak_percentage": 0,
        "counts_by_category": {"is_ambiguous": 1, "is_incomplete": 0, "is_untestable": 0, "is_weak": 0},
        "requirements": [
            {
                "text": "The system shall respond quickly.",
                "score": 70,
                "status": "Needs Review",
                "defects": [
                    {
                        "issue": "Ambiguous Requirement",
                        "category": "is_ambiguous",
                        "severity": "High",
                        "penalty": -30,
                        "confidence": 0.95,
                        "reason": "Vague term",
                        "business_impact": "Disputes",
                        "suggestion": "Be specific",
                        "rewrite": "The system shall respond within 2 seconds.",
                        "highlighted_term": "quickly"
                    }
                ],
                "defect_count": 1,
                "highlights": ["quickly"]
            }
        ]
    }
    response = client.post("/api/v1/export/csv", json=payload)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Requirement #" in response.text

def test_security_headers():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "x-process-time" in response.headers
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"

def test_empty_text_validation():
    response = client.post("/api/v1/analyze-text", json={"text": "   "})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]

def test_unsupported_file_extension():
    files = {"file": ("malicious.exe", b"MZDummyHeader", "application/octet-stream")}
    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

def test_evaluation_summary_endpoint():
    response = client.get("/api/v1/evaluation/summary")
    assert response.status_code == 200
    data = response.json()
    assert "rows_evaluated" in data
    assert "counts" in data


