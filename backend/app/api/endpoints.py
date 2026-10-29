import sys
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Response
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
import csv
import io
import re
import pandas as pd

# Ensure backend root and workspace root are on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
repo_root = backend_dir.parent
for directory in (backend_dir, repo_root):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

try:
    from app.ml.preprocessor import RequirementPreprocessor
    from app.ml.classifier import RequirementClassifier
    from app.services.document_parser import DocumentParser
except ImportError:
    from backend.app.ml.preprocessor import RequirementPreprocessor
    from backend.app.ml.classifier import RequirementClassifier
    from backend.app.services.document_parser import DocumentParser

router = APIRouter(prefix="/api/v1", tags=["Requirement Analysis"])

# Global singleton instances for speed
preprocessor = RequirementPreprocessor()
classifier = RequirementClassifier()
classifier.load_models()

# Pydantic models used by the API endpoints
class TextAnalysisRequest(BaseModel):
    text: str


class DefectDetail(BaseModel):
    issue: str
    category: str
    severity: str
    penalty: int
    confidence: float
    reason: str
    business_impact: str
    suggestion: str
    rewrite: str
    highlighted_term: Optional[str] = ""
    is_advisory: bool = False


class RequirementAnalysisResult(BaseModel):
    text: str
    score: int
    status: str
    severity: Optional[str] = "None"
    defects: List[DefectDetail]
    defect_count: int
    highlights: Optional[List[str]] = []


class AnalysisResponse(BaseModel):
    document_id: str
    project_score: int
    health_index: Optional[int] = None
    overall_status: str
    total_requirements: int
    defective_requirements_count: int
    threshold_category: str
    clear_percentage: int
    ambiguous_percentage: int
    incomplete_percentage: int
    untestable_percentage: int
    weak_percentage: int
    counts_by_category: Dict[str, int]
    counts_by_severity: Optional[Dict[str, int]] = None
    exclusion_count: Optional[int] = 0
    exclusion_summary: Optional[Dict[str, int]] = None
    requirements: List[RequirementAnalysisResult]


def calculate_analysis_payload(
    sentences: List[str],
    exclusions: Optional[List[Dict[str, str]]] = None
) -> AnalysisResponse:
    if not sentences:
        raise HTTPException(status_code=400, detail="No readable requirements found in document text.")

    if exclusions is None:
        exclusions = getattr(preprocessor, "exclusion_log", [])

    results = []
    total_score = 0
    defective_count = 0
    cat_counts = {
        "is_ambiguous": 0,
        "is_incomplete": 0,
        "is_untestable": 0,
        "is_weak": 0
    }
    severity_counts = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0
    }
    clear_count = 0

    for sent in sentences:
        analysis = classifier.predict_sentence(sent)
        total_score += analysis["score"]
        if analysis["defect_count"] > 0:
            defective_count += 1
            for d in analysis["defects"]:
                cat = d["category"]
                if cat in cat_counts:
                    cat_counts[cat] += 1
                sev = d.get("severity")
                if sev in severity_counts:
                    severity_counts[sev] += 1
        else:
            clear_count += 1
        results.append(analysis)

    total_reqs = len(sentences)
    project_score = round(total_score / total_reqs)
    health_index = project_score

    if project_score >= 90:
        overall_status = "Ready for Development"
        threshold_category = "Low Risk"
    elif project_score >= 70:
        overall_status = "Needs PM Review"
        threshold_category = "Moderate Risk"
    else:
        overall_status = "High Risk - Defect Density Critical"
        threshold_category = "High Risk"

    clear_pct = round((clear_count / total_reqs) * 100)
    ambiguous_pct = round((cat_counts["is_ambiguous"] / total_reqs) * 100)
    incomplete_pct = round((cat_counts["is_incomplete"] / total_reqs) * 100)
    untestable_pct = round((cat_counts["is_untestable"] / total_reqs) * 100)
    weak_pct = round((cat_counts["is_weak"] / total_reqs) * 100)

    # Summarize exclusions
    exclusion_count = len(exclusions) if exclusions else 0
    exclusion_summary: Dict[str, int] = {}
    if exclusions:
        for entry in exclusions:
            reason = entry.get("reason", "other")
            exclusion_summary[reason] = exclusion_summary.get(reason, 0) + 1

    return AnalysisResponse(
        document_id=f"doc_{uuid.uuid4().hex[:8]}",
        project_score=project_score,
        health_index=health_index,
        overall_status=overall_status,
        total_requirements=total_reqs,
        defective_requirements_count=defective_count,
        threshold_category=threshold_category,
        clear_percentage=clear_pct,
        ambiguous_percentage=ambiguous_pct,
        incomplete_percentage=incomplete_pct,
        untestable_percentage=untestable_pct,
        weak_percentage=weak_pct,
        counts_by_category=cat_counts,
        counts_by_severity=severity_counts,
        exclusion_count=exclusion_count,
        exclusion_summary=exclusion_summary,
        requirements=results
    )

# Cache for real-data evaluation to avoid re-running expensive predictions on every request
_real_eval_cache = None


def _compute_real_evaluation():
    global _real_eval_cache
    if _real_eval_cache is not None:
        return _real_eval_cache

    base = Path(__file__).resolve().parents[2] / "data"
    promise = base / "real_promise_nfr_heldout_candidate.csv"
    eirene = base / "eirene_real_annotated.csv"
    dfs = []
    if promise.exists():
        dfp = pd.read_csv(promise)
        dfp = dfp.assign(_source='promise')
        dfs.append(dfp)
    if eirene.exists():
        dfe = pd.read_csv(eirene)
        dfe = dfe.assign(_source='eirene')
        dfs.append(dfe)

    if not dfs:
        _real_eval_cache = {
            'rows_evaluated': 0,
            'counts': {c: 0 for c in classifier.categories},
            'by_source': {},
            'rows': [],
            'metrics_by_source': {}
        }
        return _real_eval_cache

    real_df = pd.concat(dfs, ignore_index=True)

    # Deduplicate to one row per sentence (requirement_text)
    deduped = real_df.drop_duplicates(subset=['requirement_text']).reset_index(drop=True)

    # Prepare Eirene ground-truth: per-sentence annotation and genuine-flaw flags per category
    eirene_truth = {}
    if eirene.exists():
        e_df = pd.read_csv(eirene)
        # group by requirement_text
        for text, group in e_df.groupby('requirement_text'):
            cat_annotated = {}
            cat_true = {}
            for _, r in group.iterrows():
                cat = r.get('flaw_category')
                if pd.isna(cat):
                    continue
                cat_annotated[cat] = True
                is_genuine = int(r.get('is_genuine_flaw', 0)) if not pd.isna(r.get('is_genuine_flaw', 0)) else 0
                if is_genuine:
                    cat_true[cat] = True
            eirene_truth[text] = {
                'annotated': cat_annotated,
                'true': cat_true
            }

    rows = []
    counts = {c: 0 for c in classifier.categories}
    by_source = {}
    metrics_by_source = {}

    # Precompute Eirene texts set once (if present) to avoid repeated IO
    eirene_texts = set()
    if eirene.exists():
        eirene_texts = set(pd.read_csv(eirene)['requirement_text'].unique())

    # iterate deduped sentences and classify once per sentence
    for _, row in deduped.iterrows():
        text = str(row.get('requirement_text', ''))
        raw_src = row.get('source', row.get('_source', 'unknown'))
        src_low = str(raw_src).lower() if raw_src is not None else ''
        if 'promise' in src_low:
            src_key = 'promise'
        elif 'eirene' in src_low:
            src_key = 'eirene'
        else:
            src_key = 'other'

        analysis = classifier.predict_sentence(text)
        pred_cats = {c: (1 if any(d['category'] == c for d in analysis['defects']) else 0) for c in classifier.categories}

        # update counts and by_source
        for c, v in pred_cats.items():
            if v:
                counts[c] += 1
                by_source.setdefault(src_key, {})
                by_source[src_key][c] = by_source[src_key].get(c, 0) + 1

        # collect row info
        rows.append({
                'text': text,
                'source': raw_src,
                'source_key': src_key,
                'score': analysis['score'],
                'status': analysis['status'],
                'defect_count': analysis['defect_count'],
                'predicted': pred_cats,
                'defects': [d['category'] for d in analysis['defects']]
            })

    # Compute precision/recall for sources that have ground truth (Eirene)
    if eirene.exists():
        eirene_rows = [r for r in rows if r['text'] in eirene_texts]
        metrics = {}
        for c in classifier.categories:
            # annotated sentences for this category
            annotated = []
            for r in eirene_rows:
                et = eirene_truth.get(r['text'], {'annotated': {}, 'true': {}})
                is_annotated = et['annotated'].get(c, False)
                if is_annotated:
                    true_label = 1 if et['true'].get(c, False) else 0
                    pred_label = r['predicted'].get(c, 0)
                    annotated.append((pred_label, true_label))

            tp = sum(1 for p, t in annotated if p == 1 and t == 1)
            fp = sum(1 for p, t in annotated if p == 1 and t == 0)
            fn = sum(1 for p, t in annotated if p == 0 and t == 1)
            prec = (tp / (tp + fp)) if (tp + fp) > 0 else None
            rec = (tp / (tp + fn)) if (tp + fn) > 0 else None
            metrics[c] = {
                'annotated_count': len(annotated),
                'tp': tp,
                'fp': fp,
                'fn': fn,
                'precision': prec,
                'recall': rec
            }
        metrics_by_source['eirene'] = metrics

    _real_eval_cache = {
        'rows_evaluated': len(rows),
        'counts': counts,
        'by_source': by_source,
        'rows': rows,
        'metrics_by_source': metrics_by_source
    }
    return _real_eval_cache

@router.post("/analyze-text", response_model=AnalysisResponse)
def analyze_text(payload: TextAnalysisRequest):
    """
    Analyzes raw requirements text payload.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    if len(payload.text) > 2_000_000:
        raise HTTPException(status_code=413, detail="Text payload exceeds maximum length limit (2MB).")

    sentences = preprocessor.extract_sentences(payload.text)
    exclusions = preprocessor.exclusion_log[:]
    return calculate_analysis_payload(sentences, exclusions=exclusions)

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_file(file: UploadFile = File(...)):
    """
    Extracts text from uploaded file (TXT/PDF/DOCX) and returns full requirement quality intelligence.
    """
    filename = file.filename or "uploaded document"
    try:
        raw_text = await DocumentParser.parse_file(file)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract text from '{filename}': {exc}"
        )

    sentences = preprocessor.extract_sentences(raw_text)
    exclusions = preprocessor.exclusion_log[:]
    if not sentences:
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract readable requirement statements from '{filename}'. The document may be image-based/scanned or contain non-standard formatting."
        )
    return calculate_analysis_payload(sentences, exclusions=exclusions)


@router.post("/export/csv")
def export_csv_report(payload: AnalysisResponse):
    """
    Generates downloadable CSV file containing detailed requirement quality analysis
    with UTF-8 BOM encoding for Excel compatibility and explicit Source IDs.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Requirement #", "Source ID", "Requirement Text", "Quality Score", "Status", "Severity",
        "Defect Count", "Defect Categories", "Defect Issues", "Example Rewrites",
        "Advisories (no score impact)"
    ])

    for idx, req in enumerate(payload.requirements, 1):
        # Extract explicit requirement ID if present, otherwise assign indexed ID
        req_id_match = re.match(r'^(?:\[?(REQ-\d+)\]?)\b', req.text.strip(), flags=re.IGNORECASE)
        source_id = req_id_match.group(1).upper() if req_id_match else f"REQ-{idx:03d}"
        
        rule_defects = [d for d in req.defects if not getattr(d, 'is_advisory', False)]
        advisory_defects = [d for d in req.defects if getattr(d, 'is_advisory', False)]
        
        cats = ", ".join(sorted(set([d.category for d in rule_defects]))) if rule_defects else "None"
        issues = " | ".join([f"{d.issue} ({d.severity})" for d in rule_defects]) if rule_defects else "None (Compliant)"
        rewrites = " | ".join(set([d.rewrite for d in rule_defects if d.rewrite != req.text])) if rule_defects else req.text
        advisories = " | ".join([f"{d.issue}: {d.reason[:80]}" for d in advisory_defects]) if advisory_defects else ""
        
        writer.writerow([
            idx, source_id, req.text, req.score, req.status, req.severity or "None",
            len(rule_defects), cats, issues, rewrites, advisories
        ])

    # Prepend UTF-8 Byte Order Mark (BOM) for seamless Microsoft Excel rendering
    csv_content = "\ufeff" + output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=specsense_analysis_{payload.document_id}.csv"}
    )

@router.get('/evaluation/summary')
def evaluation_summary():
    """Returns overall counts for real evaluation and breakdown by source."""
    data = _compute_real_evaluation()
    return {
        'rows_evaluated': data['rows_evaluated'],
        'counts': data['counts'],
        'by_source': data['by_source'],
        'metrics_by_source': data.get('metrics_by_source', {})
    }


@router.get('/evaluation/rows')
def evaluation_rows(flag: Optional[str] = Query(None, description="category flag name, e.g. is_ambiguous"),
                    value: int = Query(1, ge=0, le=1, description='1 to filter rows where flag present, 0 where absent'),
                    source: Optional[str] = Query(None, description='filter by source name (promise|eirene)'),
                    page: int = Query(1, ge=1),
                    page_size: int = Query(50, ge=1, le=500)):
    """Return paginated rows from the real evaluation. Filter by defect category and source."""
    data = _compute_real_evaluation()
    rows = data.get('rows', [])

    if flag:
        if value == 1:
            rows = [r for r in rows if flag in r.get('defects', [])]
        else:
            rows = [r for r in rows if flag not in r.get('defects', [])]

    if source:
        s_low = source.lower()
        rows = [r for r in rows if (r.get('source_key') == s_low) or (s_low in (r.get('source') or '').lower())]

    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rows[start:end]

    return {
        'page': page,
        'page_size': page_size,
        'total': total,
        'items': page_rows
    }

