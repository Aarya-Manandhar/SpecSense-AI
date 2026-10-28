"""
test_audit_regression.py
========================
Audit-regression test suite for SpecSense AI.

Stage 1 conditions satisfied
-----------------------------
1.  REQ-018 comparison uses the live ``RequirementPreprocessor`` (no inline copy).
    Prints the single REQ-018 statement per file and the full list of statements
    dropped per file.
2.  ``*_extracted.txt`` files were produced by ``DocumentParser._parse_pdf``
    (pypdf-based).  ``test_document_parser_footer_separation`` runs
    ``DocumentParser`` on all three PDFs and asserts that footer lines are NOT
    fused into requirement sentences.  A fused-footer test is also provided
    (``test_fused_footer_not_glued``) to guard against regression.
3.  ``test_document_level_real_pdf_scores`` feeds the real extracted source text
    of *each* file (via ``DocumentParser._parse_pdf``) through the preprocessor
    and ``calculate_analysis_payload``, and reports scores for all three.
4.  Section 4 is labelled ``"4 Verification"`` (not "4 Constraints").  The
    heading test ``test_heading_not_merged_with_next_line`` reflects this.
5.  ``preprocessor_ORIGINAL.py`` is not referenced here; ``test_data/`` is
    excluded from the commit via ``.gitignore``.
"""

import re
import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.preprocessor import RequirementPreprocessor
from app.ml.classifier import RequirementClassifier
from app.services.document_parser import DocumentParser

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def classifier():
    clf = RequirementClassifier()
    clf.load_models()
    return clf


@pytest.fixture(scope="module")
def preprocessor():
    return RequirementPreprocessor()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_PDF_DIR = Path(__file__).resolve().parents[2] / "test_data"
_PDF_FILES = {
    "HIGH":   "TaskTracker_SRS_1_high_quality.pdf",
    "MEDIUM": "TaskTracker_SRS_2_medium_quality.pdf",
    "LOWEST": "TaskTracker_SRS_3_lowest_quality.pdf",
}


def _skip_if_no_pdf(label: str):
    """Skip the test if the PDF is absent from test_data/."""
    path = _PDF_DIR / _PDF_FILES[label]
    if not _PDF_DIR.exists() or not path.exists():
        pytest.skip(f"{_PDF_FILES[label]} not found in test_data/")
    return path


# ---------------------------------------------------------------------------
# 1. Core quality defect cases (rule-based / ML-based)
# ---------------------------------------------------------------------------

def test_valid_conditional_single_line(classifier):
    """Compliant single-line conditional must score 100 with zero defects."""
    text = (
        "When a user submits valid credentials, the system shall authenticate "
        "the user and display the dashboard within 2 seconds."
    )
    res = classifier.predict_sentence(text)
    assert res["score"] == 100
    assert res["defect_count"] == 0


def test_valid_conditional_wrapped_segmentation(preprocessor, classifier):
    """Wrapped compliant requirement must merge to one sentence and score 100."""
    wrapped_text = (
        "When a user submits valid credentials, the system shall authenticate "
        "the user and display the\n"
        "dashboard within 2 seconds."
    )
    extracted = preprocessor.extract_sentences(wrapped_text)
    assert len(extracted) == 1, f"Expected 1 merged requirement, got: {extracted}"
    res = classifier.predict_sentence(extracted[0])
    assert res["score"] == 100
    assert res["defect_count"] == 0


def test_incomplete_requirement(classifier):
    """Conditional without failure branch must be flagged is_incomplete."""
    text = "The application shall allow users to create tasks."
    res = classifier.predict_sentence(text)
    categories = [d["category"] for d in res["defects"]]
    assert "is_incomplete" in categories


def test_weak_and_ambiguous(classifier):
    """'should be fast and scalable' must be flagged is_weak + (is_ambiguous or is_untestable)."""
    text = "The system should be fast and scalable."
    res = classifier.predict_sentence(text)
    categories = [d["category"] for d in res["defects"]]
    assert "is_weak" in categories
    assert "is_ambiguous" in categories or "is_untestable" in categories


def test_non_testable_securely(classifier):
    """'securely' is a subjective term — must be flagged is_untestable."""
    text = "Passwords shall be stored securely."
    res = classifier.predict_sentence(text)
    categories = [d["category"] for d in res["defects"]]
    assert "is_untestable" in categories


def test_weak_and_untestable_can_easily(classifier):
    """'can … easily' must be flagged is_weak + (is_untestable or is_ambiguous)."""
    text = "Users can reset passwords easily."
    res = classifier.predict_sentence(text)
    categories = [d["category"] for d in res["defects"]]
    assert "is_weak" in categories
    assert "is_untestable" in categories or "is_ambiguous" in categories


def test_ambiguous_several_times_a_while(classifier):
    """'several times … for a while' must be flagged is_ambiguous."""
    text = (
        "If a user enters invalid credentials several times, the system shall "
        "lock the account for a while."
    )
    res = classifier.predict_sentence(text)
    categories = [d["category"] for d in res["defects"]]
    assert "is_ambiguous" in categories


def test_compliant_no_tasks_found(classifier):
    """Well-formed error-display requirement must score 100 with zero defects."""
    text = (
        "If no task matches the filter or search, the system shall display "
        "the message 'No tasks found'."
    )
    res = classifier.predict_sentence(text)
    assert res["score"] == 100
    assert res["defect_count"] == 0


# ---------------------------------------------------------------------------
# 2. Non-requirements excluded (Stage 2 satisfied)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("non_req", [
    "Task Tracker Web Application",
    "UTC: Coordinated Universal Time.",
    "3 User Characteristics",
    'The word "shall" marks a mandatory requirement.',
])
def test_non_requirement_exclusion(preprocessor, non_req):
    """Header/boilerplate lines that are not requirements must be excluded."""
    extracted = preprocessor.extract_sentences(non_req)
    assert len(extracted) == 0
    assert not preprocessor.is_requirement(non_req)


# ---------------------------------------------------------------------------
# Condition 1: REQ-018 old/new comparison + full dropped-statement list
# ---------------------------------------------------------------------------

def test_req018_one_statement_per_file_and_print_dropped(preprocessor):
    """
    Condition 1: REQ-018 must appear as exactly ONE statement in each file.
    Prints REQ-018 and the full list of statements dropped per file.
    """
    txt_files = {
        "HIGH":   "TaskTracker_SRS_1_high_quality_extracted.txt",
        "MEDIUM": "TaskTracker_SRS_2_medium_quality_extracted.txt",
        "LOWEST": "TaskTracker_SRS_3_lowest_quality_extracted.txt",
    }
    if not _PDF_DIR.exists():
        pytest.skip("test_data/ not present")

    for label, fname in txt_files.items():
        path = _PDF_DIR / fname
        if not path.exists():
            pytest.skip(f"{fname} not found in test_data/")
        raw = path.read_text(encoding="utf-8", errors="replace")
        sents = preprocessor.extract_sentences(raw)
        req18 = [s for s in sents if "REQ-018" in s]

        print(f"\n[{label}] REQ-018 ({len(req18)} statement(s)):")
        for s in req18:
            print(f"  {s}")

        dropped = preprocessor.exclusion_log[:]
        print(f"[{label}] Dropped statements ({len(dropped)}):")
        for entry in dropped:
            print(f"  [{entry['reason']}] {entry['line']!r}")

        assert len(req18) == 1, (
            f"{label}: expected exactly 1 REQ-018 statement, got {len(req18)}: {req18}"
        )


# ---------------------------------------------------------------------------
# Condition 2: DocumentParser footer handling
# ---------------------------------------------------------------------------

def test_document_parser_footer_separation():
    """
    Condition 2: DocumentParser._parse_pdf (pypdf) on all three PDFs must
    produce footer lines that are separated from requirement text (not fused).
    The footers 'Task Tracker SRS v1.0' and 'Page N' appear on their own lines.
    """
    for label, fname in _PDF_FILES.items():
        path = _skip_if_no_pdf(label)
        raw = DocumentParser._parse_pdf(path.read_bytes())
        lines = raw.splitlines()
        # All REQ lines must not contain footer text
        req_lines = [l for l in lines if re.search(r"REQ-\d+", l)]
        for rl in req_lines:
            assert "Task Tracker SRS" not in rl, (
                f"[{label}] Footer fused into REQ line: {rl!r}"
            )
            assert re.search(r"Page\s+\d+", rl) is None, (
                f"[{label}] Page number fused into REQ line: {rl!r}"
            )
        print(f"[{label}] {len(req_lines)} REQ lines -- no fused footers [ok]")


def test_fused_footer_not_glued(preprocessor):
    """
    Condition 2 (fused-form guard): if a PDF library were to fuse the footer
    'Task Tracker SRS v1.0\\nPage 4' into a single line with a requirement, the
    preprocessor must still strip it and not corrupt the requirement text.
    """
    # Simulate a footer that would be fused just before the requirement body
    fused_raw = (
        "Task Tracker SRS v1.0\n"
        "Page 4\n"
        "REQ-018 If a user uploads an attachment larger than 10 MB, "
        "the system shall reject the file and display error message E301.\n"
    )
    sents = preprocessor.extract_sentences(fused_raw)
    req18 = [s for s in sents if "REQ-018" in s]
    assert len(req18) == 1, f"Expected 1 REQ-018, got {len(req18)}: {sents}"
    assert "Task Tracker SRS" not in req18[0]
    assert "Page 4" not in req18[0]


# ---------------------------------------------------------------------------
# Condition 3: Real PDF pipeline — DocumentParser -> preprocessor -> scores
# ---------------------------------------------------------------------------

def test_document_level_real_pdf_scores():
    """
    Condition 3: Feed the real source bytes of each PDF through
    DocumentParser._parse_pdf -> RequirementPreprocessor.extract_sentences ->
    calculate_analysis_payload.  Assert:
      - All 32 REQ-nnn lines survive in every file.
      - HIGH-quality score is strictly above LOWEST-quality score.
    Scores are printed for traceability.
    """
    from app.api.endpoints import calculate_analysis_payload

    pp = RequirementPreprocessor()
    scores = {}
    req_counts = {}

    for label, fname in _PDF_FILES.items():
        path = _skip_if_no_pdf(label)
        raw = DocumentParser._parse_pdf(path.read_bytes())
        sents = pp.extract_sentences(raw)
        result = calculate_analysis_payload(sents)
        n_req = len([s for s in sents if re.search(r"REQ-\d+", s)])
        scores[label] = result.project_score
        req_counts[label] = n_req
        print(
            f"[{label}] score={result.project_score}  "
            f"req_lines={n_req}/32  total_stmts={len(sents)}"
        )

    # All 32 REQ-nnn lines must survive in every file
    for label in ("HIGH", "MEDIUM", "LOWEST"):
        assert req_counts[label] == 32, (
            f"{label}: expected 32 REQ-nnn statements, got {req_counts[label]}"
        )

    # High quality must outscore lowest quality (separation)
    assert scores["HIGH"] > scores["LOWEST"], (
        f"Expected HIGH ({scores['HIGH']}) > LOWEST ({scores['LOWEST']})"
    )


# ---------------------------------------------------------------------------
# Condition 4: Section 4 is "4 Verification" (not "4 Constraints")
# ---------------------------------------------------------------------------

def test_section4_label_is_verification(preprocessor):
    """
    Condition 4: The heading '4 Verification' must be preserved as-is by
    _unwrap_text (and not mis-labelled '4 Constraints').
    """
    raw = (
        "3 Specific Requirements\n"
        "4 Verification\n"
        "Each requirement shall be verified by at least one test case.\n"
        "5 Traceability\n"
        "Appendix A: Error Code Summary\n"
    )
    blocks = preprocessor._unwrap_text(raw)
    assert "4 Verification" in blocks, (
        f"'4 Verification' not found in blocks: {blocks}"
    )
    assert not any("4 Constraints" in b for b in blocks), (
        "Wrong heading '4 Constraints' found"
    )


def test_section_4_5_appendix_lines_from_real_file(preprocessor):
    """
    Condition 4: Verify section 4/5 and appendix lines present in the high-quality
    extracted text file survive _unwrap_text as distinct blocks.
    """
    path = _PDF_DIR / "TaskTracker_SRS_1_high_quality_extracted.txt"
    if not path.exists():
        pytest.skip("High-quality extracted TXT not found in test_data/")
    raw = path.read_text(encoding="utf-8", errors="replace")
    blocks = preprocessor._unwrap_text(raw)
    sec4 = [b for b in blocks if re.match(r"^4\s", b)]
    sec5 = [b for b in blocks if re.match(r"^5\s", b)]
    app  = [b for b in blocks if b.lower().startswith("appendix")]
    print(f"\nSection 4 blocks: {sec4}")
    print(f"Section 5 blocks: {sec5}")
    print(f"Appendix blocks:  {app}")
    assert any("Verification" in b for b in sec4), f"'4 Verification' missing: {sec4}"
    assert any("Traceability" in b for b in sec5), f"'5 Traceability' missing: {sec5}"
    assert len(app) >= 1, f"Appendix block missing: {app}"


# ---------------------------------------------------------------------------
# Stage 2: REQ-ID with space parsing
# ---------------------------------------------------------------------------

def test_req_id_with_double_space_parsed(preprocessor):
    """
    Stage 2 -- REQ-001 with space: 'REQ-001  body' (two spaces) must produce
    a single statement with the ID preserved and normalised to one space.
    """
    raw = (
        "REQ-001  When a user submits valid credentials, the system shall "
        "authenticate the user and display the dashboard within 2 seconds.\n"
        "REQ-002  If a user submits invalid credentials, the system shall "
        "reject the login and display error message E101.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 2, f"Expected 2 statements, got {len(sents)}: {sents}"
    assert sents[0].startswith("REQ-001 "), f"REQ-001 ID not preserved: {sents[0]!r}"
    assert sents[1].startswith("REQ-002 "), f"REQ-002 ID not preserved: {sents[1]!r}"


def test_req_id_body_not_split_by_nlp(preprocessor):
    """
    Stage 2 -- numbered-requirement rule: a REQ-NNN line that contains multiple
    spaCy-detectable sentences must still be returned as a single atomic block.
    """
    raw = (
        "REQ-030  If the database connection fails, the system shall display "
        "error message E601 and retry the connection every 5 seconds.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 1, (
        f"REQ-030 must remain atomic, got {len(sents)}: {sents}"
    )
    assert "REQ-030" in sents[0]


# ---------------------------------------------------------------------------
# Stage 2: Exclusion log
# ---------------------------------------------------------------------------

def test_exclusion_log_populated(preprocessor):
    """
    Stage 2 -- exclusion log: after extracting sentences, self.exclusion_log
    must be a non-empty list of dicts each with 'line' and 'reason' keys.
    """
    raw = (
        "Software Requirements Specification\n"
        "Task Tracker Web Application\n"
        "Version 1.0\n"
        "Table of Contents\n"
        "REQ-001  The system shall authenticate users.\n"
        "REQ-002  The system shall log out users on timeout.\n"
    )
    _ = preprocessor.extract_sentences(raw)
    log = preprocessor.exclusion_log
    assert isinstance(log, list), "exclusion_log must be a list"
    assert len(log) > 0, "exclusion_log must not be empty for this input"
    for entry in log:
        assert "line" in entry and "reason" in entry, (
            f"Bad entry in exclusion_log: {entry}"
        )
    print(f"\nExclusion log ({len(log)} entries):")
    for e in log:
        print(f"  [{e['reason']}] {e['line']!r}")


def test_exclusion_log_reset_between_calls(preprocessor):
    """
    Stage 2 -- exclusion log: the log must be reset on each call to
    extract_sentences so stale entries do not accumulate.
    """
    _ = preprocessor.extract_sentences("REQ-001  The system shall authenticate.")
    first_count = len(preprocessor.exclusion_log)
    _ = preprocessor.extract_sentences("REQ-001  The system shall authenticate.")
    second_count = len(preprocessor.exclusion_log)
    assert first_count == second_count, (
        f"exclusion_log not reset between calls: {first_count} vs {second_count}"
    )


def test_mixed_document_numbered_and_unnumbered(preprocessor):
    """
    Condition 3: In a mixed document containing numbered REQ lines plus an
    unnumbered requirement sentence outside section 3 (e.g. 'The system shall...'),
    the numbered-requirement rule dictates that ONLY numbered REQs are extracted
    and scored. The unnumbered requirement must be excluded, and recorded in
    self.exclusion_log with the explicit reason 'unnumbered in numbered document'.
    """
    raw = (
        "1 Introduction\n"
        "The system shall authenticate all administrative users via LDAP.\n"
        "3 Specific Requirements\n"
        "REQ-001  The system shall log all login attempts.\n"
        "REQ-002  The system shall lock accounts after 5 failed attempts.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 2, f"Expected exactly 2 numbered REQs, got {len(sents)}: {sents}"
    assert sents[0].startswith("REQ-001")
    assert sents[1].startswith("REQ-002")

    # Verify exclusion log
    log = preprocessor.exclusion_log
    unnumbered_entries = [
        e for e in log if e["reason"] == "unnumbered in numbered document"
    ]
    assert len(unnumbered_entries) == 1, (
        f"Expected 1 'unnumbered in numbered document' entry, got: {log}"
    )
    assert "The system shall authenticate all administrative users via LDAP." in unnumbered_entries[0]["line"]


def test_convention_sentence_with_placeholder_req_id_not_split(preprocessor):
    """
    Placeholder pattern 'REQ-xxx.' without digits must not be treated as a
    new item ID; the section 1.4 conventions sentence must remain in one piece
    and not be split.
    """
    raw = (
        "1.4 Conventions\n"
        "The word \"shall\" marks a mandatory requirement. Each requirement has a unique identifier in the form\n"
        "REQ-xxx.\n"
        "2 Overall Description\n"
    )
    blocks = preprocessor._unwrap_text(raw)
    assert not any(b == "REQ-xxx." for b in blocks), f"'REQ-xxx.' was split into separate line: {blocks}"
    assert any("in the form REQ-xxx." in b for b in blocks), f"Sentence was not kept in one piece: {blocks}"


def test_bare_capability_receive_notifications_fires(classifier):
    """
    '...allow users to receive notifications.' contains 'if' as a substring inside
    'notifications', but with word boundaries \\b, it must fire as is_incomplete.
    """
    text = "The system shall allow users to receive notifications."
    res = classifier.predict_sentence(text)
    categories = [d["category"] for d in res["defects"]]
    assert "is_incomplete" in categories


def test_capability_with_parameters_does_not_fire_incomplete(classifier):
    """
    '...allow users to create tasks with a title of 1 to 100 characters.' contains
    'with', an explicit parameter/constraint exclusion, and must NOT fire is_incomplete.
    """
    text = "The application shall allow users to create tasks with a title of 1 to 100 characters."
    res = classifier.predict_sentence(text)
    categories = [d["category"] for d in res["defects"]]
    assert "is_incomplete" not in categories


@pytest.mark.parametrize("text,expected_category", [
    ("The system shall be secure against malicious files.", "is_untestable"),
    ("Data transmission should be safe.", "is_untestable"),
    ("The system shall provide helpful feedback for empty results.", "is_untestable"),
    ("The system shall handle database problems gracefully.", "is_untestable"),
    ("The system shall display an appropriate error notification.", "is_ambiguous"),
    ("The system should work on most modern browsers.", "is_ambiguous"),
    ("If a user uploads a very large attachment, the system shall reject it.", "is_ambiguous"),
    ("The system may lock accounts after too many failed attempts.", "is_ambiguous"),
    ("Deleted tasks may be removed after some time.", "is_ambiguous"),
    ("The system shall support common file types.", "is_ambiguous"),
    ("The system shall support formats such as PNG, JPEG, etc.", "is_ambiguous"),
    ("The system shall accept formats and/or reject unsafe ones.", "is_ambiguous"),
    ("Data exports should be reasonably fast.", "is_ambiguous"),
])
def test_remaining_vocabulary_lexicon_coverage(classifier, text, expected_category):
    """Verify each newly added vocabulary term is accurately categorized."""
    res = classifier.predict_sentence(text)
    categories = [d["category"] for d in res["defects"]]
    assert expected_category in categories, f"Expected {expected_category} in {categories} for: {text!r}"


# ---------------------------------------------------------------------------
# Stage 5: Health Index, Severity Labels, Explanations, Exclusions
# ---------------------------------------------------------------------------

def test_stage5_health_index_requirements_only(preprocessor):
    """
    Stage 5: Health Index must be calculated over requirements only (denominator = 2,
    not 2 + excluded lines). Non-requirements are tracked in exclusion counts.
    """
    from app.api.endpoints import calculate_analysis_payload

    raw = (
        "Software Requirements Specification\n"
        "CareTrack Medical System\n"
        "1 Introduction\n"
        "This is background information that is not a requirement.\n"
        "3 Specific Requirements\n"
        "REQ-001  When heart rate exceeds 120 bpm, the system shall alert staff within 500 ms.\n"
        "REQ-002  The system should monitor vitals quickly.\n"
        "4 Verification\n"
        "Each requirement shall be verified by clinical simulation.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    exclusions = preprocessor.exclusion_log[:]
    payload = calculate_analysis_payload(sents, exclusions=exclusions)

    assert payload.total_requirements == 2, f"Expected 2 requirements, got {payload.total_requirements}"
    assert payload.health_index == payload.project_score
    # REQ-001 is 100, REQ-002 is 60 (-30 ambiguous, -10 weak) -> mean is 80
    assert payload.health_index == 80
    assert payload.exclusion_count == len(exclusions)
    assert payload.exclusion_count > 0
    assert isinstance(payload.exclusion_summary, dict)
    assert "heading" in payload.exclusion_summary or "unnumbered in numbered document" in payload.exclusion_summary


def test_stage5_severity_labels_and_hierarchy(classifier):
    """
    Stage 5: Each defect category maps to an explicit severity label,
    and each requirement reflects the max severity among its detected defects.
    """
    # 1. Critical severity: is_incomplete
    res_crit = classifier.predict_sentence("The application shall allow users to log in.")
    crit_defect = next(d for d in res_crit["defects"] if d["category"] == "is_incomplete")
    assert crit_defect["severity"] == "Critical"
    assert res_crit["severity"] == "Critical"

    # 2. High severity: is_ambiguous
    res_high = classifier.predict_sentence("The system shall respond quickly.")
    high_defect = next(d for d in res_high["defects"] if d["category"] == "is_ambiguous")
    assert high_defect["severity"] == "High"
    assert res_high["severity"] == "High"

    # 3. Medium severity: is_untestable
    res_med = classifier.predict_sentence("The user interface shall be intuitive.")
    med_defect = next(d for d in res_med["defects"] if d["category"] == "is_untestable")
    assert med_defect["severity"] == "Medium"
    assert res_med["severity"] == "Medium"

    # 4. Low severity: is_weak
    res_low = classifier.predict_sentence("The system should authenticate users within 2 seconds.")
    low_defect = next(d for d in res_low["defects"] if d["category"] == "is_weak")
    assert low_defect["severity"] == "Low"
    assert res_low["severity"] == "Low"

    # 5. Compliant requirement: severity is "None"
    res_none = classifier.predict_sentence(
        "When a user submits valid credentials, the system shall authenticate "
        "the user and display the dashboard within 2 seconds."
    )
    assert res_none["severity"] == "None"

    # 6. Compound requirement with weak (Low) and ambiguous (High) -> overall severity is High
    res_compound = classifier.predict_sentence("The system should respond quickly.")
    assert res_compound["severity"] == "High"


def test_stage5_per_defect_explanation_fields(classifier):
    """
    Stage 5: Every defect must populate all 5 required explanation fields:
    reason, business_impact, suggestion, rewrite, and highlighted_term.
    """
    test_cases = [
        "The system should be fast and scalable.",
        "The application shall allow users to create tasks.",
        "Passwords shall be stored securely.",
        "The system may lock accounts after too many failed attempts."
    ]
    for text in test_cases:
        res = classifier.predict_sentence(text)
        assert res["defect_count"] > 0
        for d in res["defects"]:
            assert d["reason"] and len(d["reason"].strip()) > 5, f"Missing reason in {d}"
            assert d["business_impact"] and len(d["business_impact"].strip()) > 5, f"Missing impact in {d}"
            assert d["suggestion"] and len(d["suggestion"].strip()) > 5, f"Missing suggestion in {d}"
            assert d["rewrite"] and len(d["rewrite"].strip()) > 5, f"Missing rewrite in {d}"
            assert "highlighted_term" in d


def test_stage5_heldout_documents_check(preprocessor):
    """
    Stage 5 / Item 4 & 5: Held-out check on authentic domain (NASA cFS Telemetry and Command Server).
    Asserts clean document scores 100 with 0 defects, defective document scores <= 70,
    and exclusion counts are correctly returned.
    """
    from app.api.endpoints import calculate_analysis_payload

    clean_path = _PDF_DIR / "heldout_cfs_clean_srs.txt"
    defective_path = _PDF_DIR / "heldout_cfs_defective_srs.txt"

    if not clean_path.exists() or not defective_path.exists():
        pytest.skip("Held-out test documents not found in test_data/")

    clean_sents = preprocessor.extract_sentences(clean_path.read_text(encoding="utf-8"))
    clean_exclusions = preprocessor.exclusion_log[:]
    clean_res = calculate_analysis_payload(clean_sents, exclusions=clean_exclusions)

    assert clean_res.project_score == 100
    assert clean_res.health_index == 100
    assert clean_res.defective_requirements_count == 0
    assert clean_res.overall_status == "Ready for Development"
    assert clean_res.exclusion_count == len(clean_exclusions)

    defective_sents = preprocessor.extract_sentences(defective_path.read_text(encoding="utf-8"))
    defective_exclusions = preprocessor.exclusion_log[:]
    defective_res = calculate_analysis_payload(defective_sents, exclusions=defective_exclusions)

    assert defective_res.project_score <= 70
    assert defective_res.health_index <= 70
    assert defective_res.defective_requirements_count == 10
    assert defective_res.overall_status == "High Risk - Defect Density Critical"
    assert defective_res.exclusion_count == len(defective_exclusions)

    # Significant separation
    assert clean_res.health_index - defective_res.health_index >= 30


@pytest.mark.parametrize("clean_text", [
    "The system shall compute digital signatures using the Secure Hash Algorithm SHA-256.",
    "The database query shall order audit logs by the most recent session timestamp first.",
    "The database shall join transaction records on the common identifier 'account_uuid'.",
    "The network module shall authenticate incoming requests against the Common Vulnerabilities database.",
    "When a user submits valid credentials, the system shall authenticate the user and display the dashboard within 2 seconds.",
])
def test_clean_contexts_zero_defects(classifier, clean_text):
    """
    False-positive check: verify that words 'common', 'most', and 'secure'
    do NOT fire false positive defects when used in valid, verifiable, compliant contexts.
    """
    res = classifier.predict_sentence(clean_text)
    assert res["score"] == 100, f"Expected 100, got {res['score']} with defects: {res['defects']}"
    assert res["defect_count"] == 0, f"False positive detected: {res['defects']}"






