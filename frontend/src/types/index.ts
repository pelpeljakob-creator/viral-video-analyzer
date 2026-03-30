export interface VideoMeta {
  title: string;
  author: string;
  author_id: string;
  likes: number | null;
  comments: number | null;
  shares: number | null;
  duration: number;
  thumbnail_url: string | null;
}

export interface TranscriptWord {
  word: string;
  start: number;
  end: number;
}

export interface TranscriptSegment {
  text: string;
  start: number;
  end: number;
  words: TranscriptWord[];
}

export interface FrameAnalysis {
  timestamp: number;
  frame_path: string;
  shot_type: string;
  camera_movement: string;
  composition: string;
  transition: string;
  text_overlay: string | null;
  visual_description: string;
  mood: string;
  key_elements: string[];
}

export interface AIPrompts {
  visual: string;
  copywriting: string;
  recreation: string;
}

export interface SegmentAnalysis {
  start_time: number;
  end_time: number;
  frames: FrameAnalysis[];
  transcript: string | null;
  ai_prompts: AIPrompts;
}

export interface ViralAnalysis {
  hook_score: number;
  hook_analysis: string;
  pacing_analysis: string;
  emotional_arc: string;
  key_viral_factors: string[];
  target_audience: string;
  content_formula: string;
  recreation_blueprint: string;
}

export interface FullAnalysisResult {
  task_id: string;
  video_meta: VideoMeta;
  transcript: TranscriptSegment[];
  segments: SegmentAnalysis[];
  viral_analysis: ViralAnalysis;
  created_at: string;
}

export interface SSEEventData {
  stage?: string;
  progress?: number;
  message?: string;
  result?: Record<string, unknown>;
  error?: string;
  task_id?: string;
}

export interface ProgressStage {
  key: string;
  label: string;
  status: "pending" | "in_progress" | "complete" | "error";
  message?: string;
}
