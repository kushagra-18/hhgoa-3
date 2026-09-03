import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from src.config import settings
from src.database.session import init_db, get_db_session
from src.database.repository import PipelineRepository
from src.pipeline import FaceVerificationPipeline

app = FastAPI(
    title="HH Goa 2026: Face-to-Blockchain Pipeline",
    description="End-to-end pipeline: Face scan input -> Social media search -> Blockchain upload/verification",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static UI files and dynamic data directory
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/data-files", StaticFiles(directory=str(settings.DATA_DIR)), name="data-files")

# Initialize pipeline instance
pipeline_service = FaceVerificationPipeline()


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def serve_index():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "API running. UI index.html not yet built."}


@app.post("/api/pipeline/run")
async def run_pipeline(
    file: UploadFile = File(...),
):
    """Execute end-to-end face scan, social search, and blockchain verification."""
    # Save uploaded file
    file_ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    filename = f"upload_{uuid.uuid4().hex[:12]}{file_ext}"
    dest_path = settings.UPLOADS_DIR / filename

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = pipeline_service.run(image_input=str(dest_path), save_db=True)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pipeline/run-stream")
async def run_pipeline_stream(
    file: UploadFile = File(...),
):
    """Execute end-to-end pipeline streaming real-time progress events via SSE."""
    file_ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    filename = f"upload_{uuid.uuid4().hex[:12]}{file_ext}"
    dest_path = settings.UPLOADS_DIR / filename

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    def event_generator():
        try:
            for event in pipeline_service.run_stream(image_input=str(dest_path), save_db=True):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            err_dict = {
                "type": "error",
                "percent": 100,
                "title": "Error",
                "message": str(e),
            }
            yield f"data: {json.dumps(err_dict)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/pipeline/tamper-test/{attestation_id}")
def test_tampering(attestation_id: int):
    """Demonstrate cryptographic tamper-evidence live for a specific attestation."""
    res = pipeline_service.test_tampering_for_attestation(attestation_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@app.get("/api/pipeline/history")
def get_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session),
):
    """List historical pipeline executions."""
    repo = PipelineRepository(db)
    return repo.list_all_pipeline_runs(limit=limit)


@app.get("/api/pipeline/vector-search/{scan_id}")
def search_similar_embeddings(
    scan_id: int,
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db_session),
):
    """Demonstrate pgvector cosine similarity search across historical embeddings."""
    repo = PipelineRepository(db)
    target_scan = repo.get_face_scan(scan_id)
    if not target_scan or not target_scan.embedding_json:
        raise HTTPException(status_code=404, detail="Scan embedding not found")
    
    import json
    import numpy as np
    target_emb = np.array(json.loads(target_scan.embedding_json), dtype=np.float32)
    matches = repo.search_similar_faces(target_emb, top_k=top_k)
    
    return [
        {
            "scan": scan.to_dict(),
            "similarity_score": round(score, 4),
        }
        for scan, score in matches
    ]
