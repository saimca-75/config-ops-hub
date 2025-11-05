# backend/app/main.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import traceback
import logging
import json
from uuid import uuid4
import json
from pathlib import Path
from app.services.runner import create_job_and_run
from app.core.settings import settings

# -------------------------------------------------
# Create app and enable CORS
# -------------------------------------------------
app = FastAPI(title="Config Ops Hub Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000", "http://0.0.0.0:9000", "*"],  # allow local frontend
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

# -------------------------------------------------
# Logger setup
# -------------------------------------------------
logger = logging.getLogger("config_ops_hub")
logging.basicConfig(level=logging.INFO)

# -------------------------------------------------
# Health route
# -------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Backend is running."}

# -------------------------------------------------
# TASK ENDPOINTS
# -------------------------------------------------

@app.post("/tasks/ppt-to-video")
async def ppt_to_video(request: Request):
    """Convert PPT to video."""
    try:
        body = await request.json()
        uuids = body.get("uuids") or []
        if not isinstance(uuids, list):
            raise ValueError("'uuids' must be an array")

        injects = {"uuid_list": uuids}
        script_key = "ppt_to_video_updater.py"
        job_id, out_path, status = create_job_and_run(script_key, injects)
        return JSONResponse({"job_id": job_id, "status": status})
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("ppt-to-video failed: %s", tb)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/sheet-loading")
async def sheet_loading(request: Request):
    """Load a Google Sheet."""
    try:
        body = await request.json()
        url = body.get("google_sheet_url")
        if not url:
            raise ValueError("Missing google_sheet_url")

        injects = {"GOOGLE_SHEET_URL": url}
        script_key = "sheet_loading.py"
        job_id, out_path, status = create_job_and_run(script_key, injects)
        return JSONResponse({"job_id": job_id, "status": status})
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("sheet-loading failed: %s", tb)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/s3-updater")
async def s3_updater(request: Request):
    """Update S3 URLs."""
    try:
        body = await request.json()
        pairs = body.get("pairs") or []
        if not isinstance(pairs, list):
            raise ValueError("'pairs' must be an array")

        injects = {"multimedia_data": pairs}
        script_key = "s3_url_updater.py"
        job_id, out_path, status = create_job_and_run(script_key, injects)
        return JSONResponse({"job_id": job_id, "status": status})
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("s3-updater failed: %s", tb)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/get-question-ids-by-tags")
async def Getting_QuestionIDs_using_tag_names(request: Request):
    """Getting Question IDs for Tag Names."""
    try:
        body = await request.json()
        pairs = body.get("pairs") or []
        if not isinstance(pairs, list):
            raise ValueError("'pairs' must be an array")

        injects = {"multimedia_data": pairs}
        script_key = "getting_question_ids_for_tags.py"
        job_id, out_path, status = create_job_and_run(script_key, injects)
        return JSONResponse({"job_id": job_id, "status": status})
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("get-question-ids-by-tags failed: %s", tb)
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# NEW: Duration Remover
# -------------------------

@app.post("/tasks/duration-remover")
async def duration_remover(request: Request):
    """Remove durations for provided UUIDs."""
    try:
        body = await request.json()
        uuids = body.get("uuids") or []
        if not isinstance(uuids, list):
            raise ValueError("'uuids' must be an array")

        # 1) Write injects JSON to a file the job can read (same outputs dir used for logs).
        injects = {"uuid_list": uuids}
        script_key = "duration_remover.py"
        job_id, out_path, status = create_job_and_run(script_key, injects)
        return JSONResponse({"job_id": job_id, "status": status})
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("duration-remover failed: %s", tb)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------
# NEW: Unlock Resources For Users (UUIDs)
# ---------------------------------------
@app.post("/tasks/unlock-resources")
async def unlock_resources(request: Request):
    """Unlock resources for provided UUIDs."""
    try:
        body = await request.json()
        uuids = body.get("uuids") or []
        if not isinstance(uuids, list):
            raise ValueError("'uuids' must be an array")

        injects = {"uuid_list": uuids}
        script_key = "unlock_resources_for_users.py"
        job_id, out_path, status = create_job_and_run(script_key, injects)
        return JSONResponse({"job_id": job_id, "status": status})
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("unlock-resources failed: %s", tb)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------
# NEW: Old PPT -> New PPT (uuid,new_ppt)
# ---------------------------------------
@app.post("/tasks/oldppt-to-newppt")
async def oldppt_to_newppt(request: Request):
    """Map old PPT UUIDs to new PPT URLs."""
    try:
        body = await request.json()
        pairs = body.get("pairs") or []
        if not isinstance(pairs, list):
            raise ValueError("'pairs' must be an array")

        # Optional: quick shape validation
        for i, p in enumerate(pairs):
            if not isinstance(p, dict) or "uuid" not in p or "new_ppt_url" not in p:
                raise ValueError(f"'pairs[{i}]' must be an object with 'uuid' and 'new_ppt_url'")

        injects = {"pairs": pairs}
        script_key = "oldppt_to_newppt.py"
        job_id, out_path, status = create_job_and_run(script_key, injects)
        return JSONResponse({"job_id": job_id, "status": status})
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("oldppt-to-newppt failed: %s", tb)
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# Logs
# -------------------------------------------------
@app.get("/tasks/{job_id}/log")
async def get_job_log(job_id: str):
    """Return the job log for a given job ID."""
    try:
        log_path = Path(settings.outputs_dir) / f"{job_id}.log"
        if not log_path.exists():
            raise HTTPException(status_code=404, detail="Log file not found")
        text = log_path.read_text(encoding="utf-8", errors="replace")
        return {"log": text}
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Error reading log for %s: %s", job_id, tb)
        raise HTTPException(status_code=500, detail=str(e))
