"use client";

import { TranscriptSegment } from "@/types";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

interface TranscriptViewProps {
  transcript: TranscriptSegment[];
  onSeek?: (time: number) => void;
}

export default function TranscriptView({ transcript, onSeek }: TranscriptViewProps) {
  if (!transcript.length) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">&#128221; 逐字稿</h2>
        <p className="text-sm text-gray-400">未检测到语音内容</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">&#128221; 完整口播文案</h2>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {transcript.map((seg, i) => (
          <div
            key={i}
            className="flex items-start gap-3 group cursor-pointer hover:bg-blue-50 rounded-lg px-2 py-1.5 -mx-2 transition-colors"
            onClick={() => onSeek?.(seg.start)}
          >
            <span className="text-xs text-blue-500 font-mono mt-0.5 whitespace-nowrap group-hover:font-semibold">
              [{formatTime(seg.start)}]
            </span>
            <span className="text-sm text-gray-700">{seg.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
