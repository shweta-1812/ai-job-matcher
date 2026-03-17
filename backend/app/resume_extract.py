from pypdf import PdfReader
import docx

def extract_text_from_pdf_bytes(data: bytes) -> str:
    import io
    reader = PdfReader(io.BytesIO(data))
    parts = [(p.extract_text() or "") for p in reader.pages]
    return "\n".join(parts)

def extract_text_from_docx_bytes(data: bytes) -> str:
    import io
    f = io.BytesIO(data)
    d = docx.Document(f)
    return "\n".join(p.text for p in d.paragraphs)

def extract_resume_text(filename: str, data: bytes) -> str:
    suffix = filename.lower().split(".")[-1]
    if suffix == "pdf":
        return extract_text_from_pdf_bytes(data)
    if suffix == "docx":
        return extract_text_from_docx_bytes(data)
    return data.decode("utf-8", errors="ignore")
