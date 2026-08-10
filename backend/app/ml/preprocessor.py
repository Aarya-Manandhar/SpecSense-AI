import re
import spacy

class RequirementPreprocessor:
    """
    Handles raw text cleaning and NLP sentence segmentation 
    specifically optimized for Software Requirement Specifications (SRS).
    """
    def __init__(self, model_name: str = "en_core_web_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except Exception:
            # Fallback if model isn't downloaded yet
            import spacy.cli
            spacy.cli.download(model_name)
            self.nlp = spacy.load(model_name)

    def clean_text(self, text: str) -> str:
        """
        Removes formatting noise, extra whitespace, and line break artifacts.
        """
        if not text:
            return ""
        
        # Replace multiple spaces with a single space
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    def extract_sentences(self, raw_text: str) -> list[str]:
        """
        Segments raw document text into clean individual requirement sentences.
        """
        if not raw_text or not raw_text.strip():
            return []

        # Split raw text by explicit line breaks first to preserve requirement lines/bullets
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        candidates = []

        for line in lines:
            # Strip leading bullets or numbering e.g., "1.1 ", "REQ-01: ", "- "
            line_cleaned = re.sub(r'^(?:[0-9]+\.)+|^(?:[A-Z]+-[0-9]+:?)|^[\-*•]\s*', '', line).strip()
            if not line_cleaned:
                continue

            doc = self.nlp(line_cleaned)
            for sent in doc.sents:
                sent_str = sent.text.strip()
                # Clean stray bullets inside sentences
                sent_str = re.sub(r'^[\-*•]\s*', '', sent_str).strip()
                if len(sent_str) > 10:
                    candidates.append(sent_str)

        # Fallback if line splitting yielded nothing
        if not candidates:
            cleaned = self.clean_text(raw_text)
            doc = self.nlp(cleaned)
            for sent in doc.sents:
                sent_str = sent.text.strip()
                if len(sent_str) > 10:
                    candidates.append(sent_str)

        return candidates

