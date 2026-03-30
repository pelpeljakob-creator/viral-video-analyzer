import asyncio
import json
import os
import re
from glob import glob


async def _run_cmd(cmd: list[str]) -> tuple[bytes, bytes]:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{stderr.decode()}")
    return stdout, stderr


async def get_video_duration(video_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", video_path,
    ]
    stdout, _ = await _run_cmd(cmd)
    info = json.loads(stdout)
    return float(info["format"]["duration"])


async def extract_audio(video_path: str, output_dir: str) -> str:
    """Extract audio as 16kHz mono WAV for ASR."""
    audio_path = os.path.join(output_dir, "audio.wav")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        audio_path,
    ]
    await _run_cmd(cmd)
    return audio_path


async def extract_frames(video_path: str, frames_dir: str) -> list[dict]:
    """Extract frames at 1fps + scene change detection."""
    os.makedirs(frames_dir, exist_ok=True)

    duration = await get_video_duration(video_path)

    # 1-FPS extraction → change to 1 frame per 3 seconds for efficiency
    fps_cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", "fps=1/3,scale=1280:-2",
        "-q:v", "2", "-start_number", "1",
        os.path.join(frames_dir, "%03d.jpg"),
    ]
    await _run_cmd(fps_cmd)

    # Rename with timestamps
    frames = []
    raw_files = sorted(glob(os.path.join(frames_dir, "[0-9]*.jpg")))
    for i, f in enumerate(raw_files):
        ts = float(i * 3)  # 1 frame per 3 seconds
        new_name = os.path.join(frames_dir, f"{i + 1:03d}_{ts:.1f}s.jpg")
        os.rename(f, new_name)
        frames.append({"path": new_name, "timestamp": ts})

    # Scene change detection
    scene_cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", "select='gt(scene,0.3)',showinfo,scale=1280:-2",
        "-vsync", "vfn", "-q:v", "2",
        os.path.join(frames_dir, "scene_%03d.jpg"),
    ]
    process = await asyncio.create_subprocess_exec(
        *scene_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr_data = await process.communicate()

    # Parse timestamps from showinfo
    scene_times = []
    for line in stderr_data.decode().split("\n"):
        match = re.search(r"pts_time:(\d+\.?\d*)", line)
        if match:
            scene_times.append(float(match.group(1)))

    # Merge scene frames if not too close to existing frames
    scene_files = sorted(glob(os.path.join(frames_dir, "scene_*.jpg")))
    for j, (scene_file, ts) in enumerate(zip(scene_files, scene_times)):
        nearest_dist = min((abs(f["timestamp"] - ts) for f in frames), default=999)
        if nearest_dist > 0.3:
            new_name = os.path.join(frames_dir, f"s{j + 1:03d}_{ts:.1f}s.jpg")
            os.rename(scene_file, new_name)
            frames.append({"path": new_name, "timestamp": ts})
        else:
            os.remove(scene_file)

    # Clean up remaining scene files
    for f in glob(os.path.join(frames_dir, "scene_*.jpg")):
        os.remove(f)

    frames.sort(key=lambda f: f["timestamp"])
    return frames
