"use client";

import { useState } from "react";
import { SegmentAnalysis } from "@/types";
import PromptCard from "./PromptCard";
import { getFrameUrl } from "@/lib/api";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

interface SegmentCardProps {
  segment: SegmentAnalysis;
  index: number;
  taskId: string;
  onSeek?: (time: number) => void;
}

export default function SegmentCard({
  segment,
  index,
  taskId,
  onSeek,
}: SegmentCardProps) {
  const [expanded, setExpanded] = useState(false);
  const firstFrame = segment.frames[0];

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
      <div
        className="flex items-start gap-4 p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Frame thumbnail */}
        {firstFrame?.frame_path && (
          <img
            src={getFrameUrl(taskId, firstFrame.frame_path)}
            alt={`第${formatTime(segment.start_time)}秒`}
            className="w-28 h-20 object-cover rounded-lg flex-shrink-0 cursor-pointer"
            onClick={(e) => {
              e.stopPropagation();
              onSeek?.(segment.start_time);
            }}
          />
        )}

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
              {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
            </span>
            <span className="text-xs text-gray-400">#{index + 1}</span>
          </div>

          {firstFrame && (
            <div className="grid grid-cols-3 gap-2 text-xs mb-2">
              <div>
                <span className="text-gray-400">景别</span>{" "}
                <span className="text-gray-700">{firstFrame.shot_type}</span>
              </div>
              <div>
                <span className="text-gray-400">运镜</span>{" "}
                <span className="text-gray-700">{firstFrame.camera_movement}</span>
              </div>
              <div>
                <span className="text-gray-400">情绪</span>{" "}
                <span className="text-gray-700">{firstFrame.mood}</span>
              </div>
            </div>
          )}

          {segment.transcript && (
            <p className="text-sm text-gray-600 truncate">
              &#128172; {segment.transcript}
            </p>
          )}
        </div>

        <span className="text-gray-300 mt-2 flex-shrink-0">
          {expanded ? "&#9650;" : "&#9660;"}
        </span>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="border-t border-gray-100 px-4 pb-4">
          {/* All frames in this segment */}
          {segment.frames.map((frame, fi) => (
            <div
              key={fi}
              className="mt-3 text-sm border-l-2 border-blue-200 pl-3"
            >
              <p className="text-xs text-blue-500 font-mono mb-1">
                {formatTime(frame.timestamp)}
              </p>
              <p className="text-gray-700 mb-1">{frame.visual_description}</p>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                  {frame.shot_type}
                </span>
                <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                  {frame.camera_movement}
                </span>
                <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                  {frame.composition}
                </span>
                {frame.transition && frame.transition !== "无" && (
                  <span className="bg-purple-50 text-purple-600 px-2 py-0.5 rounded">
                    转场: {frame.transition}
                  </span>
                )}
                {frame.text_overlay && (
                  <span className="bg-yellow-50 text-yellow-700 px-2 py-0.5 rounded">
                    文字: {frame.text_overlay}
                  </span>
                )}
              </div>
              {frame.key_elements.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {frame.key_elements.map((el, ei) => (
                    <span
                      key={ei}
                      className="text-xs text-gray-400"
                    >
                      #{el}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* AI Prompts */}
          <PromptCard prompts={segment.ai_prompts} />
        </div>
      )}
    </div>
  );
}
