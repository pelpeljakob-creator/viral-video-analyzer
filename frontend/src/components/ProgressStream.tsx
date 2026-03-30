"use client";

import { useEffect, useRef, useState } from "react";
import { connectSSE, SSEEvent } from "@/lib/sse";
import { ProgressStage } from "@/types";

const STAGE_CONFIG: Record<string, string> = {
  downloading: "下载视频",
  extracting: "提取音频和关键帧",
  transcribing: "语音识别",
  analyzing_frames: "AI 画面分析",
  generating_prompts: "生成创作提示词",
  viral_analysis: "爆款密码分析",
};

interface ProgressStreamProps {
  taskId: string;
  onComplete: () => void;
  onError: (error: string) => void;
}

export default function ProgressStream({
  taskId,
  onComplete,
  onError,
}: ProgressStreamProps) {
  const [stages, setStages] = useState<ProgressStage[]>(
    Object.entries(STAGE_CONFIG).map(([key, label]) => ({
      key,
      label,
      status: "pending",
    }))
  );
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("准备中...");
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = connectSSE(
      taskId,
      (event: SSEEvent) => {
        if (event.type === "progress") {
          const { stage, progress: p, message: msg } = event.data;
          if (p) setProgress(p);
          if (msg) setMessage(msg);
          if (stage) {
            setStages((prev) =>
              prev.map((s) => ({
                ...s,
                status:
                  s.key === stage
                    ? "in_progress"
                    : s.status === "in_progress" && s.key !== stage
                    ? "complete"
                    : s.status,
              }))
            );
          }
        } else if (event.type === "stage_complete") {
          const { stage } = event.data;
          if (stage) {
            setStages((prev) =>
              prev.map((s) =>
                s.key === stage ? { ...s, status: "complete" } : s
              )
            );
          }
        } else if (event.type === "done") {
          setProgress(1);
          setStages((prev) =>
            prev.map((s) => ({
              ...s,
              status: s.status === "pending" ? "complete" : s.status,
            }))
          );
          onComplete();
        } else if (event.type === "error") {
          onError(event.data.error || "未知错误");
        }
      },
      () => {
        onError("连接中断，请刷新重试");
      }
    );
    esRef.current = es;

    return () => {
      es.close();
    };
  }, [taskId, onComplete, onError]);

  return (
    <div className="w-full max-w-xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">分析进行中</h2>

      <div className="space-y-3 mb-6">
        {stages.map((stage) => (
          <div key={stage.key} className="flex items-center gap-3">
            <span className="w-5 text-center">
              {stage.status === "complete" && (
                <span className="text-green-500">&#10003;</span>
              )}
              {stage.status === "in_progress" && (
                <span className="inline-block w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              )}
              {stage.status === "pending" && (
                <span className="text-gray-300">&#9675;</span>
              )}
              {stage.status === "error" && (
                <span className="text-red-500">&#10007;</span>
              )}
            </span>
            <span
              className={
                stage.status === "complete"
                  ? "text-gray-900"
                  : stage.status === "in_progress"
                  ? "text-blue-600 font-medium"
                  : "text-gray-400"
              }
            >
              {stage.label}
            </span>
          </div>
        ))}
      </div>

      <div className="w-full bg-gray-100 rounded-full h-2.5 mb-2">
        <div
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${Math.round(progress * 100)}%` }}
        />
      </div>
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  );
}
