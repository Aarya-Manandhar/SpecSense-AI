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


def test_section_4_system_features_not_excluded(preprocessor):
    """
    A document with no REQ- IDs where Section 4 is '4 System Features' containing real
    shall requirements. They must be kept because exclusion is strictly based on heading
    titles (Verification/Traceability), NOT section numbers like '4'.
    """
    raw = (
        "1 Scope and Purpose\n"
        "The system shall authenticate users with corporate SSO.\n"
        "4 System Features\n"
        "The system shall generate real-time metrics for each active worker.\n"
        "The system shall export batch reports in CSV format.\n"
        "5 Performance and Security\n"
        "The system shall respond to API queries within 250 milliseconds.\n"
        "6 Verification Procedures\n"
        "Every endpoint shall be verified through automated regression testing.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    assert len(sents) == 4, f"Expected 4 requirements from sections 1, 4, and 5, got {len(sents)}: {sents}"
    assert "The system shall authenticate users with corporate SSO." in sents
    assert "The system shall generate real-time metrics for each active worker." in sents
    assert "The system shall export batch reports in CSV format." in sents
    assert "The system shall respond to API queries within 250 milliseconds." in sents
    # Verification procedure under section 6 should be excluded
    assert not any("automated regression testing" in s for s in sents)
    reasons = [e["reason"] for e in preprocessor.exclusion_log]
    assert "section 4/5" in reasons


def test_stray_id_does_not_switch_to_numbered_mode(preprocessor):
    """
    Requires at least 3 ID-bearing lines (or >50% of candidate requirements)
    before switching to numbered mode. A document with one stray 'ISO-9001 ...'
    line or standard reference must remain in modal fallback mode and retain
    all unnumbered requirements.
    """
    raw = (
        "The system shall encrypt all sensitive customer records at rest.\n"
        "The system shall notify the user immediately upon password expiration.\n"
        "The application shall conform to ISO-9001 quality guidelines.\n"
        "The system shall log unauthorized access attempts.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    # Should stay in unnumbered/modal mode and extract all 4 valid requirements
    assert len(sents) == 4, f"Expected all 4 requirements in modal mode, got {len(sents)}: {sents}"
    # Should not have any 'unnumbered in numbered document' exclusions
    reasons = [e["reason"] for e in preprocessor.exclusion_log]
    assert "unnumbered in numbered document" not in reasons


def test_over_300_requirements_truncation_warning(preprocessor):
    """
    Document with >300 requirements triggers truncation warning and logs
    'truncation (max requirements reached)' in exclusion_log.
    """
    lines = [f"REQ-{i:04d} The system shall process transaction record {i}." for i in range(1, 325)]
    raw = "\n".join(lines)
    sents = preprocessor.extract_sentences(raw, max_requirements=300)
    assert len(sents) == 300, f"Expected exactly 300 requirements, got {len(sents)}"
    reasons = [e["reason"] for e in preprocessor.exclusion_log]
    assert any("truncation" in r for r in reasons), f"Expected truncation in reasons: {set(reasons)}"
    truncation_count = sum(1 for r in reasons if "truncation" in r)
    assert truncation_count == 24, f"Expected 24 truncated requirements, got {truncation_count}"


def test_verification_section_body_excluded(preprocessor):
    """
    A verification-titled section must exclude ALL body content, even lines that
    contain 'shall'.  A short title-case line like 'Test Cases' inside the section
    must also be excluded.  Nothing from section 4 onwards should appear in the
    extracted requirements.
    """
    raw = (
        "1 Scope\n"
        "The system shall authenticate users with MFA.\n"
        "The system shall store all audit records in encrypted storage.\n"
        "4 Verification\n"
        "Test Cases\n"
        "Each requirement shall be verified by automated unit testing.\n"
        "Inspection Records\n"
        "Verification results shall be recorded in the project log.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    # Only the two scope requirements must survive
    assert len(sents) == 2, f"Expected 2 requirements, got {len(sents)}: {sents}"
    assert "The system shall authenticate users with MFA." in sents
    assert "The system shall store all audit records in encrypted storage." in sents
    # All four verification-body lines must be in exclusion_log as section 4/5
    sec45_lines = [e["line"] for e in preprocessor.exclusion_log if e["reason"] == "section 4/5"]
    assert any("Each requirement shall be verified" in l for l in sec45_lines), (
        f"Verification body sentence missing from section 4/5 exclusions: {sec45_lines}"
    )
    assert any("Test Cases" in l for l in sec45_lines), (
        f"'Test Cases' title-case line missing from section 4/5 exclusions: {sec45_lines}"
    )


def test_numbered_system_features_after_verification_is_kept(preprocessor):
    """A numbered functional section after verification starts a new main section."""
    raw = (
        "1 Scope\n"
        "The system shall authenticate users with MFA.\n"
        "3 Verification\n"
        "Each requirement shall be verified by automated unit testing.\n"
        "4 System Features\n"
        "The system shall generate a daily task summary for each user.\n"
    )

    sents = preprocessor.extract_sentences(raw)

    assert "The system shall authenticate users with MFA." in sents
    assert "The system shall generate a daily task summary for each user." in sents
    assert not any("verified by automated" in s for s in sents)
    assert any(
        e["line"] == "Each requirement shall be verified by automated unit testing."
        and e["reason"] == "section 4/5"
        for e in preprocessor.exclusion_log
    )


def test_dotted_requirement_line_inside_verification_stays_excluded(preprocessor):
    """A 4.1 shall line remains verification content and is excluded."""
    raw = (
        "REQ-001 The system shall authenticate users with MFA.\n"
        "REQ-002 The system shall store audit records securely.\n"
        "REQ-003 The system shall notify users of account changes.\n"
        "4 Verification\n"
        "4.1 The system shall verify each account change by email.\n"
    )

    sents = preprocessor.extract_sentences(raw)

    assert len(sents) == 3, f"Expected only the three REQ lines, got: {sents}"
    assert not any("verify each account change" in s for s in sents)
    assert any(
        e["line"] == "4.1 The system shall verify each account change by email."
        and e["reason"] == "section 4/5"
        for e in preprocessor.exclusion_log
    )


def test_repeated_document_title_is_noise_inside_excluded_section(preprocessor):
    """A different repeated short document title is generic footer noise."""
    title = "Billing Portal Requirements v2.3"
    raw = (
        "REQ-001 The system shall authenticate users with MFA.\n"
        "REQ-002 The system shall store audit records securely.\n"
        "REQ-003 The system shall notify users of account changes.\n"
        "4 Verification\n"
        "Each requirement shall be verified by a documented test.\n"
        f"{title}\n{title}\n{title}\n"
    )

    preprocessor.extract_sentences(raw)

    title_entries = [e for e in preprocessor.exclusion_log if e["line"] == title]
    assert len(title_entries) == 3
    assert all(e["reason"] == "noise" for e in title_entries)
    assert all("Task Tracker SRS" not in e["line"] for e in preprocessor.exclusion_log)
    assert preprocessor._is_noise(f"{title} - Page 4")


def test_repeated_short_requirement_is_not_noise(preprocessor):
    """Three identical short requirement lines remain requirements, not footers."""
    requirement = "Users shall sign in."
    raw = "\n".join([requirement] * 3)

    sents = preprocessor.extract_sentences(raw)

    assert sents == [requirement]
    assert not any(
        e["line"] == requirement and e["reason"] == "noise"
        for e in preprocessor.exclusion_log
    )


def test_three_prose_standard_refs_do_not_trigger_numbered_mode(preprocessor):
    """
    Three prose references to standards (ISO-9001, TLS-1, RFC-2119) embedded in
    ordinary requirement sentences must NOT satisfy the ID threshold (requires >=3
    *standalone* ID-prefixed lines, not mid-sentence occurrences).  All unnumbered
    requirements must be retained in modal/fallback mode.
    """
    raw = (
        "The system shall conform to ISO-9001 quality management guidelines.\n"
        "All communication channels shall use TLS-1.3 or higher encryption.\n"
        "The word 'shall' in this document follows RFC-2119 conventions.\n"
        "The system shall authenticate users via single sign-on.\n"
        "The system shall log all failed login attempts for 90 days.\n"
    )
    sents = preprocessor.extract_sentences(raw)
    # Must stay in modal mode: all 4 requirement sentences kept
    # ('shall' convention meta-line is excluded as meta)
    assert len(sents) >= 4, f"Expected >=4 requirements in modal mode, got {len(sents)}: {sents}"
    assert any("ISO-9001" in s for s in sents), "ISO-9001 requirement dropped"
    assert any("TLS-1.3" in s for s in sents), "TLS-1.3 requirement dropped"
    assert any("single sign-on" in s for s in sents), "SSO requirement dropped"
    assert any("failed login" in s for s in sents), "Login-log requirement dropped"
    # No 'unnumbered in numbered document' exclusions should exist
    reasons = [e["reason"] for e in preprocessor.exclusion_log]
    assert "unnumbered in numbered document" not in reasons, (
        f"Numbered mode falsely triggered; exclusions: {reasons}"
    )


