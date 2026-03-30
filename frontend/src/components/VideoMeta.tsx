import { VideoMeta as VideoMetaType } from "@/types";

function formatCount(n: number | null): string {
  if (n == null) return "-";
  if (n >= 10000) return (n / 10000).toFixed(1) + "万";
  return n.toLocaleString();
}

export default function VideoMeta({ meta }: { meta: VideoMetaType }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-1">{meta.title || "无标题"}</h3>
      <p className="text-sm text-gray-500 mb-4">@{meta.author || "未知"} · {meta.duration.toFixed(1)}秒</p>
      <div className="flex gap-6 text-sm">
        <div className="flex items-center gap-1.5">
          <span className="text-red-500">&#10084;</span>
          <span className="text-gray-700">{formatCount(meta.likes)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-gray-400">&#128172;</span>
          <span className="text-gray-700">{formatCount(meta.comments)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-gray-400">&#8599;</span>
          <span className="text-gray-700">{formatCount(meta.shares)}</span>
        </div>
      </div>
    </div>
  );
}
