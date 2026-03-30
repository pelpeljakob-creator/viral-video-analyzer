"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import UrlInput from "@/components/UrlInput";
import { startAnalysis } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (url: string) => {
    setLoading(true);
    setError(null);
    try {
      const { task_id } = await startAnalysis(url);
      router.push(`/analysis/${task_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "提交失败，请重试");
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-4 bg-gray-50">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-gray-900 mb-3">
          爆款视频拆解器
        </h1>
        <p className="text-gray-500 text-lg">
          AI 秒级拉片分析，一键解码爆款密码
        </p>
      </div>

      <UrlInput onSubmit={handleSubmit} loading={loading} />

      {error && (
        <p className="mt-4 text-sm text-red-500">{error}</p>
      )}

      <div className="mt-16 grid grid-cols-3 gap-8 text-center max-w-lg">
        <div>
          <div className="text-3xl mb-2">&#128269;</div>
          <div className="text-sm font-medium text-gray-700">智能拉片</div>
          <div className="text-xs text-gray-400 mt-1">逐秒画面分析</div>
        </div>
        <div>
          <div className="text-3xl mb-2">&#128293;</div>
          <div className="text-sm font-medium text-gray-700">爆点解码</div>
          <div className="text-xs text-gray-400 mt-1">拆解爆款密码</div>
        </div>
        <div>
          <div className="text-3xl mb-2">&#9889;</div>
          <div className="text-sm font-medium text-gray-700">一键复刻</div>
          <div className="text-xs text-gray-400 mt-1">AI 提示词生成</div>
        </div>
      </div>
    </main>
  );
}
