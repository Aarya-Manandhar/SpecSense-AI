import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.preprocessor import RequirementPreprocessor

@pytest.fixture(scope="module")
def preprocessor():
    return RequirementPreprocessor()

def test_wrapped_lines_merged(preprocessor):
    """Wrapped lines in PDF/text must merge into a single complete sentence."""
    raw = (
        "When a user submits valid credentials, the system shall authenticate the user and display the\n"
        "dashboard within 2 seconds."
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 1, f"Expected 1 merged requirement, got {len(sents)}: {sents}"
    assert "within 2 seconds." in sents[0]
    assert sents[0] == "When a user submits valid credentials, the system shall authenticate the user and display the dashboard within 2 seconds."

def test_hyphenated_break_merged(preprocessor):
    """Hyphenated words broken across margin wraps should be reconstituted without hyphens."""
    raw = (
        "The system shall authen-\n"
        "ticate user credentials against the LDAP directory within 1 second."
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 1
    assert "authenticate" in sents[0]
    assert "authen-" not in sents[0]

def test_multiline_bullet_preserved(preprocessor):
    """Multiline bullet points must not be split into orphaned lines."""
    raw = (
        "* The system shall export all audit logs to an encrypted S3 bucket\n"
        "  within 15 minutes of session termination.\n"
        "* The system shall alert the administrator upon backup failure."
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 2
    assert "within 15 minutes" in sents[0]
    assert "The system shall alert" in sents[1]

def test_short_wrapped_fragment_retained(preprocessor):
    """Short fragments at the end of wrapped lines (e.g. 'minutes.') must not be dropped."""
    raw = (
        "The system shall lock the account after 5 failed attempts for 15\n"
        "minutes."
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 1
    assert sents[0] == "The system shall lock the account after 5 failed attempts for 15 minutes."

def test_source_id_preserved_in_statement(preprocessor):
    """
    Requirement IDs like REQ-01: and [REQ-002] must not be stripped.
    Stage 2 normalises 'REQ-01: body' -> 'REQ-01 body' (colon removed, ID kept).
    """
    raw = (
        "REQ-01: The system shall encrypt all stored user passwords.\n"
        "[REQ-002] The system shall log database failovers."
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 2
    # Stage 2 strips colon; ID is preserved as 'REQ-01 '
    assert "REQ-01" in sents[0], f"REQ-01 ID not found in: {sents[0]!r}"
    assert "[REQ-002]" in sents[1], f"[REQ-002] not found in: {sents[1]!r}"


def test_heading_not_merged_with_next_line(preprocessor):
    """Headings without terminal punctuation must never be merged into adjacent lines."""
    raw = (
        "Task Tracker Web Application\n"
        "3 Specific Requirements\n"
        "4 Verification\n"
        "The system shall authenticate the user within 2 seconds."
    )
    blocks = preprocessor._unwrap_text(raw)
    assert "Task Tracker Web Application" in blocks
    assert "3 Specific Requirements" in blocks
    assert "4 Verification" in blocks, (
        f"'4 Verification' not found in blocks: {blocks}"
    )
    assert "The system shall authenticate the user within 2 seconds." in blocks
    assert len(blocks) == 4

def test_page_footer_never_glued_into_sentence(preprocessor):
    """Page headers and footers like 'Page 12 of 84' must never be glued into a sentence."""
    raw = (
        "When a user submits valid credentials, the system shall authenticate the user and display the\n"
        "Page 12 of 84\n"
        "dashboard within 2 seconds."
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 1
    assert "Page 12 of 84" not in sents[0]
    assert sents[0] == "When a user submits valid credentials, the system shall authenticate the user and display the dashboard within 2 seconds."

def test_continuation_line_starting_with_number_merges(preprocessor):
    """A continuation line starting with a number like '10 MB, the system...' must merge."""
    raw = (
        "If the uploaded file exceeds\n"
        "10 MB, the system shall return an error notification."
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 1
    assert sents[0] == "If the uploaded file exceeds 10 MB, the system shall return an error notification."

def test_mid_sentence_proper_nouns_merge(preprocessor):
    """Mid-sentence proper noun titlecase words ('Chrome Firefox Edge') must merge, not be treated as a heading."""
    raw = (
        "The web application shall support modern browsers including\n"
        "Chrome Firefox Edge\n"
        "for all administrative user sessions."
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 1
    assert sents[0] == "The web application shall support modern browsers including Chrome Firefox Edge for all administrative user sessions."

def test_lone_number_inside_sentence_not_deleted(preprocessor):
    """A lone '15' line in the middle of a sentence must not be deleted as page number noise."""
    raw = (
        "The system shall lock the account after 5 failed attempts for\n"
        "15\n"
        "minutes."
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 1
    assert sents[0] == "The system shall lock the account after 5 failed attempts for 15 minutes."


def test_fallback_path_without_req_ids(preprocessor):
    """
    Fallback path test: document with no REQ- IDs.
    Extracts valid modal sentences while excluding section 4/5 and appendix lines.
    Verifies that the appendix check continues without leaking into requirements.
    """
    raw = (
        "1.1 Product Scope and Boundaries\n"
        "The system shall store all user profiles in an encrypted database.\n"
        "The system shall enforce multi-factor authentication for administrative users.\n"
        "4.0 Verification\n"
        "Each requirement shall be verified by automated unit testing.\n"
        "5 Traceability Matrix\n"
        "Verification procedures shall trace to functional requirements.\n"
        "Appendix A: System Diagnostics\n"
        "The diagnostic agent shall monitor port 8080.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    # Only the two functional requirements outside section 4/5 and appendix should be extracted
    assert len(sents) == 2, f"Expected 2 requirements, got {len(sents)}: {sents}"
    assert "The system shall store all user profiles in an encrypted database." in sents
    assert "The system shall enforce multi-factor authentication for administrative users." in sents

    # Verify exclusions in fallback path
    reasons = [e["reason"] for e in preprocessor.exclusion_log]
    assert "section 4/5" in reasons, f"Expected 'section 4/5' in exclusions: {reasons}"
    assert "appendix" in reasons, f"Expected 'appendix' in exclusions: {reasons}"
    assert "heading" in reasons or "meta" in reasons


def test_non_req_id_formats(preprocessor):
    """
    Validates support for non-REQ identifier formats:
    FR-12, [FR-12], DEMO-SRS-53, SYS_REQ_101.
    """
    raw = (
        "FR-12 The system shall compute sales tax based on jurisdiction.\n"
        "[FR-13] The system shall issue email receipts upon payment.\n"
        "DEMO-SRS-53: The system shall encrypt stored session tokens.\n"
        "SYS_REQ_101 The system shall maintain an audit log of access events.\n"
        "E-COMMERCE is an evolving domain.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 4, f"Expected 4 requirements, got {len(sents)}: {sents}"
    assert any("FR-12" in s for s in sents)
    assert any("[FR-13]" in s for s in sents)
    assert any("DEMO-SRS-53" in s for s in sents)
    assert any("SYS_REQ_101" in s for s in sents)
    # Non-requirement line 'E-COMMERCE...' should be excluded
    assert not any("E-COMMERCE" in s for s in sents)


def test_meta_does_not_drop_short_real_sentences(preprocessor):
    """
    Ensures that short requirement sentences containing words like 'scope',
    'overview', or 'purpose' are NOT dropped as metadata.
    """
    raw = (
        "The system shall define the project scope.\n"
        "The interface shall display a system overview.\n"
        "The component shall log its operational purpose.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 3, f"Expected 3 sentences, got {len(sents)}: {sents}"
    for s in sents:
        assert preprocessor.is_requirement(s)


def test_duplicate_and_truncation_exclusions_tracked(preprocessor):
    """
    Ensures that duplicate requirements and truncation events are properly
    recorded with explicit reasons in the exclusion log.
    """
    raw = (
        "REQ-001 The system shall authenticate users.\n"
        "REQ-001 The system shall authenticate users.\n"
    )
    sents = preprocessor.extract_sentences(raw, max_requirements=1)
    assert len(sents) == 1
    reasons = [e["reason"] for e in preprocessor.exclusion_log]
    assert "duplicate" in reasons, f"Expected duplicate in {reasons}"

