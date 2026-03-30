import json
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from config import settings

router = APIRouter()


@router.get("/api/results/{task_id}")
async def get_results(task_id: str):
    result_path = os.path.join(settings.DATA_DIR, task_id, "result.json")
    if not os.path.exists(result_path):
        raise HTTPException(404, "Results not found")
    with open(result_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/api/video/{task_id}")
async def get_video(task_id: str):
    video_path = os.path.join(settings.DATA_DIR, task_id, "video.mp4")
    if not os.path.exists(video_path):
        raise HTTPException(404, "Video not found")
    return FileResponse(video_path, media_type="video/mp4")


@router.get("/api/frame/{task_id}/{filename}")
async def get_frame(task_id: str, filename: str):
    frame_path = os.path.join(settings.DATA_DIR, task_id, "frames", filename)
    if not os.path.exists(frame_path):
        raise HTTPException(404, "Frame not found")
    return FileResponse(frame_path, media_type="image/jpeg")
