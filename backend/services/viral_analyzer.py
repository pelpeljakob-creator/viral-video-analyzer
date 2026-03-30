import asyncio
import functools
import json

from openai import OpenAI

from config import settings
from models.schemas import VideoMeta, ViralAnalysis


VIRAL_ANALYSIS_SYSTEM = """你是一位顶级的短视频运营专家和爆款分析师，曾分析过超过10000条百万赞爆款短视频。

你的任务是分析一条短视频的"爆款密码"——它为什么能火？能让人停留、点赞、转发的核心要素是什么？

请严格按以下JSON格式输出：
{
  "hook_score": 8,
  "hook_analysis": "前3秒钩子分析：具体描述开头如何抓住注意力",
  "pacing_analysis": "节奏分析：信息密度、画面切换频率、音乐节奏配合",
  "emotional_arc": "情绪曲线：描述从开头到结尾的情绪变化轨迹",
  "key_viral_factors": ["爆点因素1：具体描述", "爆点因素2：具体描述"],
  "target_audience": "目标受众画像描述",
  "content_formula": "这条视频的底层内容公式",
  "recreation_blueprint": "如何复刻这类爆款的分步指南：\\n1. ...\\n2. ...\\n3. ..."
}"""


def _get_client() -> OpenAI:
    return OpenAI(
        base_url=settings.DOUBAO_BASE_URL,
        api_key=settings.DOUBAO_API_KEY,
    )


def _analyze_viral_sync(
    meta: VideoMeta,
    full_transcript: str,
    segments_summary: str,
) -> ViralAnalysis:
    """Synchronous viral analysis (runs in thread pool)."""
    client = _get_client()

    likes_str = f"{meta.likes}" if meta.likes else "未知"
    comments_str = f"{meta.comments}" if meta.comments else "未知"
    shares_str = f"{meta.shares}" if meta.shares else "未知"

    user_content = f"""视频信息：
- 标题：{meta.title}
- 作者：{meta.author}
- 点赞数：{likes_str}
- 评论数：{comments_str}
- 分享数：{shares_str}
- 时长：{meta.duration:.1f}秒

完整口播/字幕文案：
{full_transcript or '（无语音内容）'}

逐秒画面分析摘要：
{segments_summary}

请深入分析这条视频的爆款密码。"""

    response = client.chat.completions.create(
        model=settings.DOUBAO_VISION_ENDPOINT,
        messages=[
            {"role": "system", "content": VIRAL_ANALYSIS_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        temperature=0.5,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ViralAnalysis(
            hook_score=0,
            hook_analysis=raw[:500],
        )

    return ViralAnalysis(**data)


async def analyze_viral(
    meta: VideoMeta,
    full_transcript: str,
    segments_summary: str,
) -> ViralAnalysis:
    """Async wrapper for viral analysis."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(_analyze_viral_sync, meta, full_transcript, segments_summary),
    )
