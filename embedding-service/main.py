from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import os

app = FastAPI(title="Factory RAG Embedding Service")

MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-large-zh-v1.5")
model = SentenceTransformer(MODEL_NAME)


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    dimensions: int


@app.post("/api/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    if not req.texts:
        raise HTTPException(status_code=400, detail="texts must not be empty")
    vectors = model.encode(
        req.texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return EmbedResponse(
        embeddings=vectors.tolist(),
        dimensions=vectors.shape[1],
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "dimensions": model.get_sentence_embedding_dimension(),
    }
