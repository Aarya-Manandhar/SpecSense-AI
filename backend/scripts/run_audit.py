"""
Audit script: runs DocumentParser -> RequirementPreprocessor -> calculate_analysis_payload
on the three TaskTracker test PDFs and prints scores/REQ counts.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import re
from app.services.document_parser import DocumentParser
from app.ml.preprocessor import RequirementPreprocessor
from app.api.endpoints import calculate_analysis_payload

pp = RequirementPreprocessor()
test_data = Path(__file__).resolve().parents[2] / "test_data"
files = [
    ("HIGH",   "TaskTracker_SRS_1_high_quality.pdf"),
    ("MEDIUM", "TaskTracker_SRS_2_medium_quality.pdf"),
    ("LOWEST", "TaskTracker_SRS_3_lowest_quality.pdf"),
]

print("=== Real PDF -> Preprocessor -> calculate_analysis_payload scores ===\n")
scores = {}
req_counts = {}
for label, fname in files:
    pdf_path = test_data / fname
    raw = DocumentParser._parse_pdf(pdf_path.read_bytes())
    sents = pp.extract_sentences(raw)
    result = calculate_analysis_payload(sents)
    n_req = len([s for s in sents if re.search(r"REQ-\d+", s)])
    scores[label] = result.project_score
    req_counts[label] = n_req
    print(f"[{label}] score={result.project_score}  req_lines={n_req}/32  total_stmts={len(sents)}")

print()
h, l = scores["HIGH"], scores["LOWEST"]
print(f"HIGH ({h}) > LOWEST ({l}): {h > l}")
