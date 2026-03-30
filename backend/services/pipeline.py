import asyncio
import json
import os
from datetime import datetime

from config import settings
from models.schemas import (
    AIPrompts,
    FullAnalysisResult,
    SegmentAnalysis,
    VideoMeta,
)
from services.downloader import download_video
from services.transcriber import transcribe_with_whisper
from services.video_processor import extract_audio, extract_frames
from services.vision_analyzer import analyze_frame, generate_segment_prompts
from services.viral_analyzer import analyze_viral


async def run_pipeline(task_id: str, url: str, event_queue: asyncio.Queue):
    """Run the full analysis pipeline, emitting SSE events along the way."""
    task_dir = os.path.join(settings.DATA_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    try:
        # Stage 1: Download
        await event_queue.put({
            "type": "progress",
            "data": {"stage": "downloading", "progress": 0.05, "message": "正在下载视频..."},
        })
        meta = await download_video(url, task_dir)
        await event_queue.put({
            "type": "stage_complete",
            "data": {"stage": "downloading", "result": meta.model_dump()},
        })

        video_path = os.path.join(task_dir, "video.mp4")

        # Stage 2: Extract audio + frames in parallel
        await event_queue.put({
            "type": "progress",
            "data": {"stage": "extracting", "progress": 0.15, "message": "正在提取音频和关键帧..."},
        })

        audio_path, frames = await asyncio.gather(
            extract_audio(video_path, task_dir),
            extract_frames(video_path, os.path.join(task_dir, "frames")),
        )

        await event_queue.put({
            "type": "stage_complete",
            "data": {"stage": "extracting", "result": {"frame_count": len(frames)}},
        })

        # Stage 3: ASR
        await event_queue.put({
            "type": "progress",
            "data": {"stage": "transcribing", "progress": 0.30, "message": "正在识别语音..."},
        })
        transcript = await transcribe_with_whisper(audio_path)
        await event_queue.put({
            "type": "stage_complete",
            "data": {"stage": "transcribing", "result": {"segment_count": len(transcript)}},
        })

        # Stage 4: Vision analysis per frame (concurrent, batch of 3)
        total_frames = len(frames)
        BATCH_SIZE = 3
        for batch_start in range(0, total_frames, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_frames)
            progress = 0.35 + (batch_start / max(total_frames, 1)) * 0.35
            await event_queue.put({
                "type": "progress",
                "data": {
                    "stage": "analyzing_frames",
                    "progress": progress,
                    "message": f"正在分析画面 ({batch_start + 1}-{batch_end}/{total_frames})...",
                },
            })

            async def _analyze_one(i):
                prev_path = frames[i - 1]["path"] if i > 0 else None
                return await analyze_frame(
                    frames[i]["path"],
                    frames[i]["timestamp"],
                    meta.title,
                    prev_path,
                )

            results = await asyncio.gather(
                *[_analyze_one(i) for i in range(batch_start, batch_end)]
            )
            for i, analysis in zip(range(batch_start, batch_end), results):
                frames[i]["analysis"] = analysis
                frames[i]["analysis_text"] = analysis.visual_description

        await event_queue.put({
            "type": "stage_complete",
            "data": {"stage": "analyzing_frames"},
        })

        # Stage 5: Group into segments + generate prompts
        await event_queue.put({
            "type": "progress",
            "data": {"stage": "generating_prompts", "progress": 0.75, "message": "正在生成创作提示词..."},
        })

        segments = _group_segments(frames, transcript, meta.duration)

        for seg in segments:
            seg_data = {
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "frames": [
                    {"timestamp": f.timestamp, "analysis_text": f.visual_description}
                    for f in seg.frames
                ],
                "transcript": seg.transcript,
            }
            prompts = await generate_segment_prompts(seg_data, meta.title)
            seg.ai_prompts = AIPrompts(**prompts)

        await event_queue.put({
            "type": "stage_complete",
            "data": {"stage": "generating_prompts"},
        })

        # Stage 6: Viral analysis
        await event_queue.put({
            "type": "progress",
            "data": {"stage": "viral_analysis", "progress": 0.90, "message": "正在分析爆款密码..."},
        })

        full_transcript = " ".join(s.text for s in transcript)
        segments_summary = "\n".join(
            f"[{s.start_time:.1f}s-{s.end_time:.1f}s] "
            + "; ".join(f.visual_description for f in s.frames if f.visual_description)
            for s in segments
        )

        viral = await analyze_viral(meta, full_transcript, segments_summary)

        await event_queue.put({
            "type": "stage_complete",
            "data": {"stage": "viral_analysis"},
        })

        # Assemble result
        # Convert frame paths to be relative for frontend
        for seg in segments:
            for f in seg.frames:
                f.frame_path = f.frame_path.replace(task_dir + "/", "")

        result = FullAnalysisResult(
            task_id=task_id,
            video_meta=meta,
            transcript=transcript,
            segments=segments,
            viral_analysis=viral,
            created_at=datetime.now().isoformat(),
        )

        result_path = os.path.join(task_dir, "result.json")
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2, by_alias=True))

        await event_queue.put({
            "type": "done",
            "data": {"task_id": task_id},
        })

    except Exception as e:
        await event_queue.put({
            "type": "error",
            "data": {"error": str(e)},
        })


def _group_segments(
    frames: list[dict],
    transcript: list,
    duration: float,
) -> list[SegmentAnalysis]:
    """Group frames into ~3-second segments aligned with transcript."""
    if not frames:
        return []

    segment_duration = 3.0
    segments = []
    current_frames = []
    segment_start = 0.0

    for frame in frames:
        analysis = frame.get("analysis")
        if not analysis:
            continue

        if frame["timestamp"] - segment_start >= segment_duration and current_frames:
            seg_end = frame["timestamp"]
            seg_transcript = _get_transcript_for_range(transcript, segment_start, seg_end)
            segments.append(SegmentAnalysis(
                start_time=segment_start,
                end_time=seg_end,
                frames=current_frames,
                transcript=seg_transcript,
            ))
            current_frames = []
            segment_start = seg_end

        current_frames.append(analysis)

    # Last segment
    if current_frames:
        seg_transcript = _get_transcript_for_range(transcript, segment_start, duration)
        segments.append(SegmentAnalysis(
            start_time=segment_start,
            end_time=duration,
            frames=current_frames,
            transcript=seg_transcript,
        ))

    return segments


def _get_transcript_for_range(
    transcript: list,
    start: float,
    end: float,
) -> str:
    """Get transcript text that overlaps with a time range."""
    texts = []
    for seg in transcript:
        if seg.end > start and seg.start < end:
            texts.append(seg.text)
    return " ".join(texts) if texts else None
