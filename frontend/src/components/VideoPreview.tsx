"use client";

import { forwardRef, useImperativeHandle, useRef } from "react";

export interface VideoPreviewHandle {
  seekTo: (time: number) => void;
}

interface VideoPreviewProps {
  src: string;
}

const VideoPreview = forwardRef<VideoPreviewHandle, VideoPreviewProps>(
  ({ src }, ref) => {
    const videoRef = useRef<HTMLVideoElement>(null);

    useImperativeHandle(ref, () => ({
      seekTo: (time: number) => {
        if (videoRef.current) {
          videoRef.current.currentTime = time;
          videoRef.current.play().catch(() => {});
        }
      },
    }));

    return (
      <video
        ref={videoRef}
        src={src}
        controls
        className="w-full rounded-xl bg-black"
        playsInline
      />
    );
  }
);

VideoPreview.displayName = "VideoPreview";
export default VideoPreview;
