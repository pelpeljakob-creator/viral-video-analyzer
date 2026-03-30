import asyncio
import base64
import functools
import json

from openai import OpenAI

from config import settings
from models.schemas import FrameAnalysis


FRAME_ANALYSIS_SYSTEM = """你是一位专业的短视频拍摄分析师和导演。你的任务是对短视频的每一帧画面进行专业的"拆片"分析。

请严格按照以下JSON格式输出分析结果，不要添加任何额外文字：

{
  "shot_type": "景别：大特写/特写/近景/中景/全景/远景",
  "camera_movement": "运镜：固定/左摇/右摇/上摇/下摇/推进/拉远/跟拍/环绕/手持晃动",
  "composition": "构图：中心构图/三分法/对角线/框架式/引导线/对称/留白",
  "transition": "与上一帧的转场方式：硬切/溶解/擦除/滑动/缩放/无(首帧)",
  "text_overlay": "画面上出现的文字内容，没有则为null",
  "visual_description": "用一句话描述画面内容和动作",
  "mood": "画面情绪：激昂/平静/悬疑/搞笑/温馨/紧张/震撼/治愈",
  "key_elements": ["画面中的关键视觉元素列表"]
}"""

SEGMENT_PROMPT_SYSTEM = """你是一位短视频创作导演和文案专家。
根据提供的视频片段分析数据（包含画面分析和对应文案），请生成三种AI提示词：

1. **visual**：用于AI生图/生视频工具复现这个片段的画面风格和内容。描述要具体，包含景别、光线、人物动作、色调。
2. **copywriting**：用于AI写出类似风格和节奏的文案/口播稿。指明风格、句式、字数、情绪。
3. **recreation**：完整的拍摄指导，包括景别、运镜、道具、演员指导、后期处理。

请用JSON格式输出：
{
  "visual": "...",
  "copywriting": "...",
  "recreation": "..."
}"""


def _get_client() -> OpenAI:
    return OpenAI(
        base_url=settings.DOUBAO_BASE_URL,
        api_key=settings.DOUBAO_API_KEY,
    )


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _parse_json_response(raw: str) -> dict:
    """Parse JSON from model response, handling markdown code blocks."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    return json.loads(raw)


def _analyze_frame_sync(
    frame_path: str,
    timestamp: float,
    title: str,
    prev_frame_path: str | None = None,
) -> FrameAnalysis:
    """Synchronous frame analysis (runs in thread pool)."""
    client = _get_client()

    content = []

    if prev_frame_path:
        content.append({"type": "text", "text": f"上一帧（{timestamp - 1:.1f}秒）："})
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{_encode_image(prev_frame_path)}"},
        })

    context = "上一帧画面已附上，请对比分析转场方式。" if prev_frame_path else "这是视频的第一帧。"
    content.append({
        "type": "text",
        "text": f"这是短视频的第{timestamp:.1f}秒的画面。\n视频标题：{title}\n{context}\n\n请对这一帧进行专业的拍摄手法分析。",
    })
    content.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{_encode_image(frame_path)}"},
    })

    response = client.chat.completions.create(
        model=settings.DOUBAO_VISION_ENDPOINT,
        messages=[
            {"role": "system", "content": FRAME_ANALYSIS_SYSTEM},
            {"role": "user", "content": content},
        ],
        temperature=0.3,
        max_tokens=800,
    )

    raw = response.choices[0].message.content.strip()
    try:
        data = _parse_json_response(raw)
    except (json.JSONDecodeError, IndexError):
        data = {
            "shot_type": "",
            "camera_movement": "",
            "composition": "",
            "transition": "",
            "text_overlay": None,
            "visual_description": raw[:200],
            "mood": "",
            "key_elements": [],
        }

    return FrameAnalysis(
        timestamp=timestamp,
        frame_path=frame_path,
        **data,
    )


async def analyze_frame(
    frame_path: str,
    timestamp: float,
    title: str,
    prev_frame_path: str | None = None,
) -> FrameAnalysis:
    """Async wrapper for frame analysis."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(_analyze_frame_sync, frame_path, timestamp, title, prev_frame_path),
    )


def _generate_segment_prompts_sync(segment_data: dict, title: str) -> dict:
    """Synchronous prompt generation (runs in thread pool)."""
    client = _get_client()

    frames_summary = json.dumps(
        [{"timestamp": f["timestamp"], "analysis": f.get("analysis_text", "")} for f in segment_data.get("frames", [])],
        ensure_ascii=False,
    )

    response = client.chat.completions.create(
        model=settings.DOUBAO_VISION_ENDPOINT,
        messages=[
            {"role": "system", "content": SEGMENT_PROMPT_SYSTEM},
            {
                "role": "user",
                "content": f"视频标题：{title}\n\n片段时间：{segment_data['start_time']:.1f}s - {segment_data['end_time']:.1f}s\n\n画面分析：\n{frames_summary}\n\n对应口播文案：\n{segment_data.get('transcript', '无')}\n\n请生成三种提示词。",
            },
        ],
        temperature=0.5,
        max_tokens=1000,
    )

    raw = response.choices[0].message.content.strip()
    try:
        return _parse_json_response(raw)
    except (json.JSONDecodeError, IndexError):
        return {"visual": "", "copywriting": "", "recreation": raw[:500]}


async def generate_segment_prompts(segment_data: dict, title: str) -> dict:
    """Async wrapper for segment prompt generation."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(_generate_segment_prompts_sync, segment_data, title),
    )
