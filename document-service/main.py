import os
import re
from pathlib import Path

import fitz  # PyMuPDF
import httpx
from fastapi import FastAPI, HTTPException
from paddleocr import PaddleOCR
from pydantic import BaseModel

FILES_DIR = os.getenv("FILES_DIR", "/data/files")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8001")

app = FastAPI(title="Factory RAG Document Service")
ocr = PaddleOCR(lang="ch", use_angle_cls=True, show_log=False)


# ── Request/Response models ──────────────────────────────────────────

class ParsePdfRequest(BaseModel):
    file_path: str


class ParseImageRequest(BaseModel):
    file_path: str


class ChunkRequest(BaseModel):
    text: str
    chunk_size: int = 500
    chunk_overlap: int = 50


class EmbedRequest(BaseModel):
    texts: list[str]


class ParseResult(BaseModel):
    pages: list[dict]
    full_text: str
    page_count: int


class ChunkResult(BaseModel):
    chunks: list[dict]


class EmbedResult(BaseModel):
    embeddings: list[list[float]]


# ── Helpers ───────────────────────────────────────────────────────────

def _resolve_path(file_path: str) -> Path:
    """Resolve file path, stripping any URL prefix."""
    if file_path.startswith("http://") or file_path.startswith("https://"):
        raise HTTPException(400, "HTTP URLs not supported, use a local file path")
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(FILES_DIR) / path
    if not path.exists():
        raise HTTPException(400, f"File not found: {path}")
    return path


# ── Parse endpoints ───────────────────────────────────────────────────

@app.post("/api/parse/pdf", response_model=ParseResult)
def parse_pdf(req: ParsePdfRequest):
    """Extract text from PDF page by page with metadata."""
    path = _resolve_path(req.file_path)
    doc = fitz.open(str(path))
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append({
                "page_number": i + 1,
                "text": text.strip(),
                "char_count": len(text),
            })

    doc.close()
    full_text = "\n\n".join(p["text"] for p in pages)

    return ParseResult(
        pages=pages,
        full_text=full_text,
        page_count=len(pages),
    )


@app.post("/api/parse/image")
def parse_image(req: ParseImageRequest):
    """OCR an image file and return recognized text."""
    path = _resolve_path(req.file_path)
    result = ocr.ocr(str(path), cls=True)

    if not result or not result[0]:
        return {"text": "", "lines": []}

    lines = []
    for line in result[0]:
        text = line[1][0]
        confidence = line[1][1]
        lines.append({"text": text, "confidence": round(confidence, 4)})

    full_text = "\n".join(l["text"] for l in lines)
    return {"text": full_text, "lines": lines}


# ── Chunking ──────────────────────────────────────────────────────────

@app.post("/api/chunk", response_model=ChunkResult)
def chunk_text(req: ChunkRequest):
    """Sliding-window chunking with overlap. Splits on sentence boundaries where possible."""
    text = req.text
    chunk_size = req.chunk_size
    chunk_overlap = req.chunk_overlap
    chunks = []

    # Split on sentence boundaries (Chinese or English)
    sentences = re.split(r"(?<=[。！？.!?\n])\s*", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    current = ""
    idx = 0
    for sent in sentences:
        if len(current) + len(sent) <= chunk_size:
            current += sent
        else:
            if current:
                chunks.append({"chunk_index": idx, "text": current.strip(), "char_count": len(current)})
                idx += 1
                # Overlap: keep last portion
                if chunk_overlap > 0 and len(current) > chunk_overlap:
                    current = current[-chunk_overlap:] + sent
                else:
                    current = sent
            else:
                # Single sentence longer than chunk_size — must split
                for i in range(0, len(sent), chunk_size - chunk_overlap):
                    sub = sent[i:i + chunk_size]
                    chunks.append({"chunk_index": idx, "text": sub.strip(), "char_count": len(sub)})
                    idx += 1
                current = ""

    if current.strip():
        chunks.append({"chunk_index": idx, "text": current.strip(), "char_count": len(current)})

    return ChunkResult(chunks=chunks)


# ── Embedding proxy ───────────────────────────────────────────────────

@app.post("/api/embed", response_model=EmbedResult)
async def embed_texts(req: EmbedRequest):
    """Proxy batch embedding requests to the embedding service."""
    if not req.texts:
        raise HTTPException(400, "texts must not be empty")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{EMBEDDING_SERVICE_URL}/api/embed",
            json={"texts": req.texts},
        )
        if resp.status_code != 200:
            raise HTTPException(502, f"Embedding service error: {resp.text}")
        data = resp.json()
    return EmbedResult(embeddings=data["embeddings"])


# ── Health ────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "embedding_service": EMBEDDING_SERVICE_URL}
