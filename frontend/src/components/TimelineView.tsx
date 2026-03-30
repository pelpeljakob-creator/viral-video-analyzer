"use client";

import { SegmentAnalysis } from "@/types";
import SegmentCard from "./SegmentCard";

interface TimelineViewProps {
  segments: SegmentAnalysis[];
  taskId: string;
  onSeek?: (time: number) => void;
}

export default function TimelineView({
  segments,
  taskId,
  onSeek,
}: TimelineViewProps) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        &#127916; 逐秒拆解
      </h2>
      <div className="space-y-3">
        {segments.map((seg, i) => (
          <SegmentCard
            key={i}
            segment={seg}
            index={i}
            taskId={taskId}
            onSeek={onSeek}
          />
        ))}
      </div>
    </div>
  );
}
