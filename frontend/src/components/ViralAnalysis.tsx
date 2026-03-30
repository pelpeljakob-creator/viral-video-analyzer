import { ViralAnalysis as ViralAnalysisType } from "@/types";

export default function ViralAnalysis({ data }: { data: ViralAnalysisType }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        &#128293; 爆款分析
      </h2>

      {/* Hook Score */}
      <div className="mb-5">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-sm font-medium text-gray-700">开头钩子评分</span>
          <span className="text-2xl font-bold text-blue-600">
            {data.hook_score}/10
          </span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
            style={{ width: `${data.hook_score * 10}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-gray-600">{data.hook_analysis}</p>
      </div>

      {/* Viral Factors */}
      {data.key_viral_factors.length > 0 && (
        <div className="mb-5">
          <h3 className="text-sm font-medium text-gray-700 mb-2">爆点因素</h3>
          <div className="flex flex-wrap gap-2">
            {data.key_viral_factors.map((factor, i) => (
              <span
                key={i}
                className="px-3 py-1 bg-orange-50 text-orange-700 rounded-full text-sm"
              >
                {factor}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Pacing */}
      <div className="mb-5">
        <h3 className="text-sm font-medium text-gray-700 mb-1">节奏分析</h3>
        <p className="text-sm text-gray-600">{data.pacing_analysis}</p>
      </div>

      {/* Emotional Arc */}
      <div className="mb-5">
        <h3 className="text-sm font-medium text-gray-700 mb-1">情绪曲线</h3>
        <p className="text-sm text-gray-600">{data.emotional_arc}</p>
      </div>

      {/* Content Formula */}
      <div className="mb-5">
        <h3 className="text-sm font-medium text-gray-700 mb-1">内容公式</h3>
        <p className="text-sm text-gray-900 font-medium bg-yellow-50 px-3 py-2 rounded-lg">
          {data.content_formula}
        </p>
      </div>

      {/* Target Audience */}
      <div className="mb-5">
        <h3 className="text-sm font-medium text-gray-700 mb-1">目标受众</h3>
        <p className="text-sm text-gray-600">{data.target_audience}</p>
      </div>

      {/* Recreation Blueprint */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-1">复刻蓝图</h3>
        <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-4 whitespace-pre-line">
          {data.recreation_blueprint}
        </div>
      </div>
    </div>
  );
}
