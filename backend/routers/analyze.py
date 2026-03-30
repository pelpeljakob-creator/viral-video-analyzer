import asyncio
import json
import os
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from config import settings
from models.schemas import AnalyzeResponse
from services.pipeline import run_pipeline

router = APIRouter()

# In-memory task store
tasks: dict[str, dict] = {}


class AnalyzeRequest(BaseModel):
    url: str
    detail: Optional[dict] = None  # Allow frontend to pass pre-fetched detail JSON


@router.post("/api/analyze", response_model=AnalyzeResponse)
async def start_analysis(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    event_queue = asyncio.Queue()
    tasks[task_id] = {
        "status": "queued",
        "events": event_queue,
    }

    # If detail JSON was provided, save it for the downloader
    if req.detail:
        task_dir = os.path.join(settings.DATA_DIR, task_id)
        os.makedirs(task_dir, exist_ok=True)
        detail_path = os.path.join(task_dir, "detail.json")
        with open(detail_path, "w", encoding="utf-8") as f:
            json.dump(req.detail, f, ensure_ascii=False)

    background_tasks.add_task(run_pipeline, task_id, req.url, event_queue)
    return AnalyzeResponse(task_id=task_id, status="queued")


@router.get("/api/analyze/{task_id}/stream")
async def stream_progress(task_id: str):
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")

    async def event_generator():
        queue = tasks[task_id]["events"]
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=300)
                yield {
                    "event": event["type"],
                    "data": json.dumps(event["data"], ensure_ascii=False),
                }
                if event["type"] in ("done", "error"):
                    break
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": "{}"}

    return EventSourceResponse(event_generator())
