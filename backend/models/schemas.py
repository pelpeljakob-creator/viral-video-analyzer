from pydantic import BaseModel
from typing import Optional


class AnalyzeRequest(BaseModel):
    url: str


class AnalyzeResponse(BaseModel):
    task_id: str
    status: str


class VideoMeta(BaseModel):
    title: str = ""
    author: str = ""
    author_id: str = ""
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    duration: float = 0.0
    thumbnail_url: Optional[str] = None


class TranscriptWord(BaseModel):
    word: str
    start: float
    end: float


class TranscriptSegment(BaseModel):
    text: str
    start: float
    end: float
    words: list[TranscriptWord] = []


class FrameAnalysis(BaseModel):
    timestamp: float
    frame_path: str
    shot_type: str = ""
    camera_movement: str = ""
    composition: str = ""
    transition: str = ""
    text_overlay: Optional[str] = None
    visual_description: str = ""
    mood: str = ""
    key_elements: list[str] = []


class AIPrompts(BaseModel):
    visual: str = ""
    copywriting: str = ""
    recreation: str = ""


class SegmentAnalysis(BaseModel):
    start_time: float
    end_time: float
    frames: list[FrameAnalysis] = []
    transcript: Optional[str] = None
    ai_prompts: AIPrompts = AIPrompts()


class ViralAnalysis(BaseModel):
    hook_score: int = 0
    hook_analysis: str = ""
    pacing_analysis: str = ""
    emotional_arc: str = ""
    key_viral_factors: list[str] = []
    target_audience: str = ""
    content_formula: str = ""
    recreation_blueprint: str = ""


class FullAnalysisResult(BaseModel):
    task_id: str
    video_meta: VideoMeta = VideoMeta()
    transcript: list[TranscriptSegment] = []
    segments: list[SegmentAnalysis] = []
    viral_analysis: ViralAnalysis = ViralAnalysis()
    created_at: str = ""
