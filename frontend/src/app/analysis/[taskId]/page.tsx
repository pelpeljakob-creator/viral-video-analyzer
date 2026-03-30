"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { getResults, getVideoUrl } from "@/lib/api";
import { FullAnalysisResult } from "@/types";
import ProgressStream from "@/components/ProgressStream";
import VideoPreview, { VideoPreviewHandle } from "@/components/VideoPreview";
import VideoMeta from "@/components/VideoMeta";
import ViralAnalysis from "@/components/ViralAnalysis";
import TranscriptView from "@/components/TranscriptView";
import TimelineView from "@/components/TimelineView";

export default function AnalysisPage() {
  const params = useParams();
  const taskId = params.taskId as string;

  const [status, setStatus] = useState<"analyzing" | "done" | "error">(
    "analyzing"
  );
  const [result, setResult] = useState<FullAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<VideoPreviewHandle>(null);

  const handleComplete = useCallback(async () => {
    try {
      const data = await getResults(taskId);
      setResult(data);
      setStatus("done");
    } catch {
      setError("获取结果失败");
      setStatus("error");
    }
  }, [taskId]);

  const handleError = useCallback((err: string) => {
    setError(err);
    setStatus("error");
  }, []);

  const handleSeek = useCallback((time: number) => {
    videoRef.current?.seekTo(time);
  }, []);

  // Check if results already exist (page refresh)
  useEffect(() => {
    getResults(taskId)
      .then((data) => {
        setResult(data);
        setStatus("done");
      })
      .catch(() => {
        // Results not ready, stay in analyzing state
      });
  }, [taskId]);

  if (status === "analyzing") {
    return (
      <main className="flex-1 flex items-center justify-center px-4 bg-gray-50">
        <ProgressStream
          taskId={taskId}
          onComplete={handleComplete}
          onError={handleError}
        />
      </main>
    );
  }

  if (status === "error") {
    return (
      <main className="flex-1 flex items-center justify-center px-4 bg-gray-50">
        <div className="text-center">
          <p className="text-red-500 text-lg mb-4">&#9888; 分析失败</p>
          <p className="text-gray-500 mb-6">{error}</p>
          <a
            href="/"
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            返回首页
          </a>
        </div>
      </main>
    );
  }

  if (!result) return null;

  return (
    <main className="flex-1 bg-gray-50 pb-16">
      <div className="max-w-4xl mx-auto px-4 pt-8">
        {/* Header */}
        <div className="mb-6">
          <a href="/" className="text-sm text-blue-500 hover:text-blue-700">
            &#8592; 返回首页
          </a>
        </div>

        {/* Video + Meta */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <VideoPreview ref={videoRef} src={getVideoUrl(taskId)} />
          <VideoMeta meta={result.video_meta} />
        </div>

        {/* Viral Analysis */}
        <div className="mb-6">
          <ViralAnalysis data={result.viral_analysis} />
        </div>

        {/* Transcript */}
        <div className="mb-6">
          <TranscriptView
            transcript={result.transcript}
            onSeek={handleSeek}
          />
        </div>

        {/* Timeline */}
        <TimelineView
          segments={result.segments}
          taskId={taskId}
          onSeek={handleSeek}
        />
      </div>
    </main>
  );
}
