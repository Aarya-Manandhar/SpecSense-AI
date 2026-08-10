import io
from fastapi import UploadFile

class DocumentParser:
    """
    Parses plain text from text payloads or uploaded files (PDF, DOCX, TXT, MD).
    """
    @staticmethod
    async def parse_file(file: UploadFile) -> str:
        content_bytes = await file.read()
        filename = file.filename.lower() if file.filename else ""
        
        if filename.endswith(".pdf"):
            return DocumentParser._parse_pdf(content_bytes)
        elif filename.endswith(".docx"):
            return DocumentParser._parse_docx(content_bytes)
        else:
            # Fallback for plain text, markdown, or raw text payloads
            return DocumentParser._parse_text(content_bytes)

    @staticmethod
    def _parse_pdf(content_bytes: bytes) -> str:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            text_pages = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_pages.append(extracted)
            return "\n".join(text_pages)
        except Exception:
            # Secondary fallback try PyPDF2 if available or plain text
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
                text_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                return "\n".join(text_pages)
            except Exception:
                return DocumentParser._parse_text(content_bytes)

    @staticmethod
    def _parse_docx(content_bytes: bytes) -> str:
        try:
            import docx
            doc = docx.Document(io.BytesIO(content_bytes))
            lines = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    lines.append(paragraph.text.strip())
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            lines.append(cell.text.strip())
            return "\n".join(lines)
        except Exception:
            return DocumentParser._parse_text(content_bytes)

    @staticmethod
    def _parse_text(content_bytes: bytes) -> str:
        try:
            return content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return content_bytes.decode("latin-1", errors="ignore")

