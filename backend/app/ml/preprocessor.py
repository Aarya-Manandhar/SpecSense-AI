import re
import spacy
from collections import Counter
from typing import Optional, List, Dict, Tuple


class RequirementPreprocessor:
    """
    Handles raw text cleaning and high-performance NLP sentence segmentation
    specifically optimized for Software Requirement Specifications (SRS).

    Stage 2 Features:
    -----------------
    1. REQ-ID parsing & metadata extraction:
       - Supports IDs like ``REQ-001  body``, ``REQ-01: body``, ``[REQ-002] body``.
       - Normalizes space/colon formatting while preserving ID tokens verbatim.
       - Stores metadata in ``self.extracted_metadata`` and ``self.requirement_metadata``.
    2. Numbered-requirement rule:
       - If a document contains numbered REQ lines (e.g. REQ-001), only those lines
         are scored/extracted as requirements.
       - All non-requirement lines are excluded and recorded in ``self.exclusion_log``
         with explicit reasons (heading, definition, meta, section 4/5, appendix,
         header/footer noise, too short).
    3. Modal rule fallback:
       - If a document does not contain numbered REQ lines, falls back to the modal
         rule: excludes boilerplate/headings and segments sentences containing
         modal requirement verbs (shall, should, must, will, may, can, could).
    4. Method ``is_requirement(text)``:
       - Determines whether a single string or candidate is a valid requirement.
    """

    _REQ_ID_RE = re.compile(
        r'^(?:\[(?P<b_id>[A-Z]{1,10}(?:[-_][A-Z0-9]+)*(?:[-_]\d+[A-Z0-9]*))\]|'
        r'(?P<p_id>[A-Z]{1,10}(?:[-_][A-Z0-9]+)*(?:[-_]\d+[A-Z0-9]*)))\s*:?\s*(?P<body>.+)$',
        re.IGNORECASE | re.DOTALL,
    )
    _PLAIN_REQ_RE = re.compile(
        r'^(?:\[?(?:[A-Z]{1,10}(?:[-_][A-Z0-9]+)*(?:[-_]\d+[A-Z0-9]*))\]?)(?:\s*:?\s+|$)',
        re.IGNORECASE,
    )

    _MODAL_RE = re.compile(
        r'\b(shall|should|must|will|may|can|could)\b',
        re.IGNORECASE,
    )

    def __init__(self, model_name: str = "en_core_web_sm"):
        try:
            # Blank English pipeline with sentencizer (fast, lightweight)
            self.nlp = spacy.blank("en")
            self.nlp.add_pipe("sentencizer")
        except Exception:
            try:
                self.nlp = spacy.load(
                    model_name,
                    disable=["tok2vec", "tagger", "parser", "ner",
                             "attribute_ruler", "lemmatizer"],
                )
                if "sentencizer" not in self.nlp.pipe_names:
                    self.nlp.add_pipe("sentencizer")
            except Exception:
                self.nlp = None

        # Stage 2 tracking state
        self.exclusion_log: List[Dict[str, str]] = []
        self.extracted_metadata: List[Dict[str, str]] = []
        self.requirement_metadata: Dict[str, Dict[str, str]] = {}

    # ── Text Cleaning ────────────────────────────────────────────────────────

    def clean_text(self, text: str) -> str:
        """
        Removes formatting noise, extra whitespace, control chars, surrogates,
        and line break artifacts.
        """
        if not text:
            return ""
        # Strip unicode surrogates (\ud800-\udfff) that break C-extension tokenizers
        text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
        # Remove null bytes & non-printable control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', text)
        # Replace multiple horizontal spaces with a single space
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    # ── Structural Classification Helpers ─────────────────────────────────────

    def _is_heading(self, line: str) -> bool:
        """
        Identifies lines that look like document headings or section titles
        so they are never merged into surrounding prose.
        """
        trimmed = line.strip()
        # 1. Section numbering: "3 User Characteristics", "4 Verification"
        if re.match(r'^[0-9]+(?:\.[0-9]+)*\s+[A-Z]', trimmed):
            return True
        # 2. Markdown headers: "# Section", "## Scope"
        if trimmed.startswith("#"):
            return True
        # 3. REQ-NNN lines are NOT headings
        if self._PLAIN_REQ_RE.match(trimmed):
            return False
        # 4. Document titles or standalone heading phrases
        words = trimmed.split()
        if 1 <= len(words) <= 7 and not re.search(r'[.!?:]$', trimmed):
            if not self._MODAL_RE.search(trimmed) and not re.search(
                r'\b(is|are|was|were|has|have)\b', trimmed, re.IGNORECASE
            ):
                capitalized = sum(1 for w in words if w[0].isupper())
                if capitalized >= len(words) * 0.7:
                    return True
        return False

    def _is_definition(self, line: str) -> bool:
        """Identifies definition, glossary, or acronym lines."""
        trimmed = line.strip()
        if re.match(r'^[A-Z0-9_\-\s]{2,15}:\s+[A-Z]', trimmed):
            return True
        if re.match(r'^(definitions|glossary|acronyms)\b', trimmed, re.IGNORECASE):
            return True
        return False

    def _is_meta(self, line: str) -> bool:
        """Identifies document metadata, conventions, or boilerplates."""
        trimmed = line.strip()
        # 1. Document metadata / convention statements (even if containing 'shall' / 'should')
        if re.match(
            r'^(?:The word [\'"]?shall[\'"]?|The word [\'"]?should[\'"]?'
            r'|Software Requirements Specification|Version\s+\d+'
            r'|Table of Contents|Prepared in the structure|Revision History'
            r'|Document\s+(?:Title|Author|Status|Version|Date|Control)'
            r'|Author\s*:|Date\s*:|Version\s*:)',
            trimmed, re.IGNORECASE,
        ):
            return True

        # 2. Sentences containing modal requirement verbs reflect requirement intent; never treat as meta
        if self._MODAL_RE.search(trimmed):
            return False

        # 3. Heading-level scope/overview/purpose markers without sentence-terminal punctuation
        if not re.search(r'[.!?]$', trimmed):
            if re.match(
                r'^(?:[0-9.]+\s+)?(?:document\s+|product\s+|system\s+)?(?:scope|overview|purpose|conventions|definitions)\s*$',
                trimmed,
                re.IGNORECASE,
            ):
                return True
        return False

    def _is_section_4_5(self, line: str) -> bool:
        """
        Identifies verification or traceability section headings.
        Exclusion is strictly based on heading titles (Verification, Qualification,
        Traceability), NOT on arbitrary section numbers like '4' or '5', ensuring
        structures where Section 4 or 5 contains functional requirements
        (e.g., '4 System Features') are never dropped.
        """
        trimmed = line.strip()
        # Must contain verification, qualification, or traceability in the heading title
        # e.g., "4 Verification", "Section 4: Verification", "4.0 Verification Matrix",
        # "5 Traceability", "Section 5 - Traceability Matrix", "Qualification Procedures"
        return bool(
            re.match(
                r'^(?:#+\s*)?(?:(?:section\s+)?[0-9]+(?:\.[0-9]+)*\s*[:.-]?\s*)?'
                r'(?:verification(?:\s+and\s+validation)?|qualification|traceability)'
                r'(?:\s+(?:matrix|table|method|methods|criteria|procedure|procedures|section))?\s*[:.-]?\s*$',
                trimmed,
                re.IGNORECASE,
            )
        )

    def _is_appendix(self, line: str) -> bool:
        """Identifies appendix lines, annexes, or supplemental reference headings."""
        trimmed = line.strip()
        if re.match(r'^(?:#+\s*)?(?:appendix|annex)(?:\s+[a-z0-9]+)?\b', trimmed, re.IGNORECASE):
            return True
        if re.match(r'^(?:#+\s*)?app\.\s+[a-z0-9]+\b', trimmed, re.IGNORECASE):
            return True
        if re.match(r'^(?:#+\s*)?(?:error\s+code\s+(?:summary|table|list)|appendix\s+table)\b', trimmed, re.IGNORECASE):
            return True
        return False

    def _is_noise(self, line: str) -> bool:
        """Identifies page headers, footers, or empty/decorative noise generically."""
        trimmed = line.strip()
        return bool(
            re.match(
                r'^(?:page\s+\d+(\s+of\s+\d+)?|\d+\s+of\s+\d+|\d+$|[-=_.*#~]{3,}$|[-=_.*#\s]+$'
                r'|confidential(\s*-\s*internal\s+use\s+only)?'
                r'|proprietary(\s+and\s+confidential)?'
                r'|internal\s+use\s+only|all\s+rights\s+reserved|draft\s*(?:v\d+[\d.]*)?'
                r'|.+\s+page\s+\d+)$',
                trimmed, re.IGNORECASE,
            )
        )

    def _repeated_short_footer_lines(self, lines: List[str]) -> set[str]:
        """Find repeated short lines likely to be page headers or footers.

        A line is considered a repeated footer only when its trimmed,
        case-insensitive form appears at least 3 times, is 1–80 characters,
        lacks sentence-ending punctuation, and contains no requirement modal.
        These last two checks preserve short real requirements and sentences.
        """
        normalized = [line.strip().casefold() for line in lines]
        counts = Counter(normalized)
        return {
            line for line, count in counts.items()
            if count >= 3
            and 0 < len(line) <= 80
            and not re.search(r'[.!?]$', line)
            and not self._MODAL_RE.search(line)
        }

    def _classify_exclusion_reason(self, line: str, in_numbered_doc: bool = False) -> str:
        """Returns the specific exclusion reason for a non-requirement line."""
        trimmed = line.strip()
        if self._is_noise(trimmed):
            return "noise"
        if self._is_section_4_5(trimmed):
            return "section 4/5"
        if self._is_appendix(trimmed):
            return "appendix"
        if self._is_definition(trimmed):
            return "definition"
        if self._is_meta(trimmed):
            return "meta"
        if self._is_heading(trimmed):
            return "heading"
        if len(trimmed) < 12:
            return f"too short ({len(trimmed)} chars)"
        if in_numbered_doc and self._MODAL_RE.search(trimmed):
            return "unnumbered in numbered document"
        return "meta"

    # ── Text Unwrapping & Line Reconstruction ────────────────────────────────

    def _unwrap_text(self, text: str) -> List[str]:
        """
        Unwraps hard margin line breaks and reconstructs broken hyphenated words
        from PDF/DOCX/TXT extraction while preserving bullet items and explicit
        IDs. Filters out page headers/footers and prevents headings from merging
        with prose.
        """
        # 1. Join hyphenated line breaks: e.g., 'authen-\n ticate' -> 'authenticate'
        text = re.sub(
            r'(\b[a-zA-Z]{2,})-\s*\r?\n\s*([a-zA-Z]{2,}\b)', r'\1\2', text
        )

        raw_lines = [l.rstrip() for l in text.splitlines()]
        merged_blocks = []
        current_block = ""

        # Indicators that unequivocally start a new structural item or list entry
        new_item_pattern = re.compile(
            r'^(?:[\-*•]\s+|[0-9]+[.)]\s+|\[?[A-Z]{1,10}(?:[-_][A-Z0-9]+)*(?:[-_]\d+[A-Z0-9]*)\]?'
            r'|#+\s+|appendix\b|annex\b)',
            re.IGNORECASE,
        )
        noise_pattern = re.compile(
            r'^(?:page\s+\d+(\s+of\s+\d+)?|\d+\s+of\s+\d+'
            r'|table\s+of\s+contents|[-=_.*#~]{3,}$|[-=_.*#\s]+$'
            r'|confidential(\s*-\s*internal\s+use\s+only)?'
            r'|proprietary(\s+and\s+confidential)?'
            r'|internal\s+use\s+only|all\s+rights\s+reserved|draft\s*(?:v\d+[\d.]*)?)$',
            re.IGNORECASE,
        )
        open_connector_pattern = re.compile(
            r'\b(including|with|for|against|from|to|by|between|of|into|the|a|an'
            r'|this|all|any|such|and|or|shall|must|will|should|can|could|may'
            r'|is|are|exceeds)\s*$',
            re.IGNORECASE,
        )

        for line in raw_lines:
            trimmed = line.strip()
            if not trimmed or noise_pattern.match(trimmed):
                continue

            # If line is only digits (e.g. '15')
            if re.match(r'^\d+$', trimmed):
                if not current_block or bool(
                    re.search(r'[.!?:]\s*[\'\""]?$', current_block)
                ):
                    continue

            if not current_block:
                current_block = trimmed
            else:
                ends_with_terminal = bool(
                    re.search(r'[.!?:]\s*[\'\""]?$', current_block)
                )
                starts_new_item = bool(new_item_pattern.match(trimmed))
                current_is_heading = self._is_heading(current_block)
                next_is_heading = self._is_heading(trimmed)

                # Open connectors cannot be followed by an independent heading
                if bool(open_connector_pattern.search(current_block)):
                    next_is_heading = False

                if (
                    not ends_with_terminal
                    and not starts_new_item
                    and not current_is_heading
                    and not next_is_heading
                ):
                    current_block += " " + trimmed
                else:
                    merged_blocks.append(current_block)
                    current_block = trimmed

        if current_block:
            merged_blocks.append(current_block)

        return merged_blocks

    # ── Stage 2: REQ-ID Normalisation & Parsing ──────────────────────────────

    def _normalise_req_id(self, block: str) -> Tuple[str, str]:
        """
        Normalizes a requirement statement with an explicit ID.
        Returns (normalized_statement, requirement_id).
        Examples:
          ``REQ-001  body`` -> (``REQ-001 body``, ``REQ-001``)
          ``REQ-01: body``  -> (``REQ-01 body``,  ``REQ-01``)
          ``[REQ-002] body``-> (``[REQ-002] body``, ``REQ-002``)
        """
        m = self._REQ_ID_RE.match(block)
        if m:
            b_id = m.group("b_id")
            p_id = m.group("p_id")
            body = m.group("body").strip()
            if b_id:
                req_id = b_id.upper()
                return f"[{req_id}] {body}", req_id
            else:
                req_id = p_id.upper()
                return f"{req_id} {body}", req_id
        return block, ""

    # ── Stage 2: Requirement Check Method ────────────────────────────────────

    def is_requirement(self, text: str) -> bool:
        """
        Determines whether a single line/statement qualifies as a requirement.
        - Numbered REQ lines (e.g. REQ-001) always qualify.
        - Headings, definitions, meta, section 4/5, appendix, and noise do NOT.
        - Prose containing modal verbs (shall, should, must, will, may, can, could)
          qualifies if not classified as non-requirement boilerplate.
        """
        trimmed = text.strip()
        if not trimmed or len(trimmed) < 12:
            return False
        if self._PLAIN_REQ_RE.match(trimmed):
            return True
        if (
            self._is_noise(trimmed)
            or self._is_heading(trimmed)
            or self._is_definition(trimmed)
            or self._is_meta(trimmed)
            or self._is_section_4_5(trimmed)
            or self._is_appendix(trimmed)
        ):
            return False
        return bool(self._MODAL_RE.search(trimmed))

    # ── Public API ────────────────────────────────────────────────────────────

    def extract_sentences(self, raw_text: str, max_requirements: int = 300) -> List[str]:
        """
        Segments raw document text into clean requirement statements.

        Stage 2 Logic:
        --------------
        * Extracts and preserves IDs as metadata (REQ-001, space or colon).
        * If the document has numbered REQ lines: scores/keeps ONLY those lines
          and logs everything else as excluded with a reason (heading, definition,
          meta, section 4/5, appendix, noise).
        * Otherwise falls back to the modal rule.
        """
        self.exclusion_log = []
        self.extracted_metadata = []
        self.requirement_metadata = {}

        if not raw_text or not raw_text.strip():
            return []

        cleaned_raw = self.clean_text(raw_text)
        lines = self._unwrap_text(cleaned_raw)
        repeated_short_lines = self._repeated_short_footer_lines(lines)

        # Detect whether the document uses numbered requirements:
        # Require at least 3 ID-bearing lines OR >50% of candidate modal lines
        id_bearing_count = sum(
            1 for l in lines if bool(self._PLAIN_REQ_RE.match(l.strip()))
        )
        modal_candidate_count = sum(
            1 for l in lines
            if len(l.strip()) >= 12
            and bool(self._MODAL_RE.search(l.strip()))
            and not self._is_heading(l.strip())
            and not self._is_noise(l.strip())
        )
        has_numbered_reqs = (
            id_bearing_count >= 3
            or (modal_candidate_count > 0 and (id_bearing_count / modal_candidate_count) > 0.5)
        )

        candidates = []
        current_section = "main"

        if has_numbered_reqs:
            # ── Stage 2: Numbered-requirement rule ───────────────────────────
            for line in lines:
                trimmed = line.strip()
                if self._is_section_4_5(trimmed):
                    current_section = "section_4_5"
                elif self._is_appendix(trimmed):
                    current_section = "appendix"
                elif self._is_heading(trimmed) and (
                    current_section == "main"
                    or re.match(r'^[0-9]+\s+[A-Z]', trimmed)
                ):
                    current_section = "main"

                if self._PLAIN_REQ_RE.match(trimmed) and current_section == "main":
                    norm_stmt, req_id = self._normalise_req_id(trimmed)
                    meta_entry = {
                        "id": req_id,
                        "text": norm_stmt,
                        "raw_line": line,
                    }
                    self.extracted_metadata.append(meta_entry)
                    self.requirement_metadata[norm_stmt] = meta_entry
                    candidates.append(norm_stmt)
                else:
                    if self._is_noise(trimmed) or trimmed.casefold() in repeated_short_lines:
                        reason = "noise"
                    elif current_section == "section_4_5":
                        reason = "section 4/5"
                    elif current_section == "appendix":
                        reason = "appendix"
                    else:
                        reason = self._classify_exclusion_reason(line, in_numbered_doc=True)
                    self.exclusion_log.append({"line": line, "reason": reason})
        else:
            # ── Stage 2: Modal rule fallback ─────────────────────────────────
            for line in lines:
                trimmed = line.strip()

                if self._is_noise(trimmed) or trimmed.casefold() in repeated_short_lines:
                    self.exclusion_log.append({"line": line, "reason": "noise"})
                    continue

                if self._is_section_4_5(trimmed):
                    current_section = "section_4_5"
                elif self._is_appendix(trimmed):
                    current_section = "appendix"
                elif self._is_heading(trimmed) and (
                    current_section == "main"
                    or re.match(r'^[0-9]+\s+[A-Z]', trimmed)
                ):
                    current_section = "main"

                if current_section == "section_4_5":
                    self.exclusion_log.append({"line": line, "reason": "section 4/5"})
                    continue
                if current_section == "appendix":
                    self.exclusion_log.append({"line": line, "reason": "appendix"})
                    continue

                if len(trimmed) < 12:
                    self.exclusion_log.append({"line": line, "reason": f"too short ({len(trimmed)} chars)"})
                    continue

                if self._is_definition(trimmed):
                    self.exclusion_log.append({"line": line, "reason": "definition"})
                    continue
                if self._is_meta(trimmed):
                    self.exclusion_log.append({"line": line, "reason": "meta"})
                    continue
                if self._is_heading(trimmed):
                    self.exclusion_log.append({"line": line, "reason": "heading"})
                    continue

                # Must contain at least one modal requirement verb
                if not self._MODAL_RE.search(trimmed):
                    self.exclusion_log.append({
                        "line": line,
                        "reason": "no modal requirement keyword",
                    })
                    continue

                # Strip bullet prefix for sentence segmentation
                line_cleaned = re.sub(r'^[\-*•]\s*', '', trimmed).strip()

                if self.nlp:
                    doc = self.nlp(line_cleaned)
                    for sent in doc.sents:
                        s_text = sent.text.strip()
                        s_cleaned = re.sub(r'^[\-*•]\s*', '', s_text).strip()
                        if self._MODAL_RE.search(s_cleaned):
                            if len(s_cleaned) < 12:
                                self.exclusion_log.append({
                                    "line": s_text,
                                    "reason": f"too short ({len(s_cleaned)} chars)",
                                })
                            elif len(s_cleaned) > 600:
                                self.exclusion_log.append({
                                    "line": s_text,
                                    "reason": "truncation (exceeds 600 chars)",
                                })
                            else:
                                candidates.append(s_cleaned)
                        else:
                            self.exclusion_log.append({
                                "line": s_text,
                                "reason": "no modal requirement keyword in sentence",
                            })
                else:
                    candidates.append(line_cleaned)

                if len(candidates) >= max_requirements * 2:
                    break

        # Filter duplicates while recording them in the exclusion log
        filtered_reqs = []
        seen = set()

        for cand in candidates:
            cand_lower = cand.lower()
            if cand_lower in seen:
                self.exclusion_log.append({"line": cand, "reason": "duplicate"})
                continue
            seen.add(cand_lower)
            if len(filtered_reqs) >= max_requirements:
                self.exclusion_log.append({
                    "line": cand,
                    "reason": "truncation (max requirements reached)",
                })
                continue
            filtered_reqs.append(cand)

        return filtered_reqs
