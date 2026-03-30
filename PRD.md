# 爆款短视频拉片复刻系统 — 产品需求文档 (PRD)

**版本号**: v1.0.0
**文档版本**: 2026-03-30
**项目代号**: viral-video-analyzer
**项目路径**: `/Users/pureliu/viral-video-analyzer/`

---

## 一、产品概述

### 1.1 产品定位
一款 Web 应用，帮助短视频创作者分析抖音爆款视频的拍摄手法和爆款密码。用户输入抖音视频链接，系统自动下载视频、逐秒拉片分析、提取逐字稿、生成 AI 复刻提示词，并给出整体爆款因素分析。

### 1.2 核心用户流程
```
用户粘贴抖音链接 → 点击"开始分析" → 实时进度展示(SSE) → 结果页展示
```

### 1.3 结果页内容
1. **视频播放器** + 基础信息（标题/作者/点赞/评论/分享/时长）
2. **爆款分析**：钩子评分、爆点因素、节奏分析、情绪曲线、内容公式、目标受众、复刻蓝图
3. **完整口播文案**：带时间戳的逐字稿，点击可跳转视频对应位置
4. **逐秒拆解时间线**：每段包含帧缩略图、景别/运镜/构图/情绪标签、对应文案
5. **AI 提示词**（每段展开可见）：画面提示词 / 文案提示词 / 复刻提示词，支持一键复制

---

## 二、技术架构

### 2.1 技术栈

| 层 | 技术 | 版本 |
|---|---|---|
| 前端 | Next.js + TypeScript + Tailwind CSS | Next.js 16.2.1, Node 24.13.0 |
| 前端包管理 | pnpm | 10.29.3 |
| 后端 | Python FastAPI | Python 3.12.7, FastAPI 0.135.2 |
| 视频下载 | Playwright (headless Chromium) | playwright (Python) |
| 视频处理 | FFmpeg | 8.0.1 |
| 语音识别 | faster-whisper (本地, CPU) | 1.2.1, model: small |
| 多模态分析 | 豆包 Vision API (火山引擎 ARK) | doubao-1-5-vision-pro-32k |
| 进度推送 | SSE (sse-starlette) | 3.3.4 |
| AI SDK | OpenAI Python SDK (兼容豆包) | 2.30.0 |

### 2.2 架构图
```
┌─────────────────────────────────────────────────┐
│            Frontend (Next.js :3000)              │
│  首页(链接输入) → 进度页(SSE) → 结果页(展示)      │
└────────────────────┬────────────────────────────┘
                     │ REST API + SSE
┌────────────────────▼────────────────────────────┐
│            Backend (FastAPI :8000)                │
│                                                   │
│  ┌────────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ Playwright  │ │ FFmpeg   │ │ 豆包 Vision   │  │
│  │ 视频下载    │ │ 抽帧/音频│ │ API 分析      │  │
│  └────────────┘ └──────────┘ └───────────────┘  │
│  ┌────────────┐ ┌──────────────────────────┐    │
│  │ Whisper    │ │ Pipeline 编排 + SSE 推送  │    │
│  │ 语音识别   │ │                           │    │
│  └────────────┘ └──────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

### 2.3 处理流水线
```
用户提交链接
  │
  ├─ 1. Playwright 打开抖音页面，拦截 API 响应获取视频详情 JSON
  │     ├─ 解析元数据（标题/作者/数据）
  │     └─ 提取最高码率视频 URL → curl 下载
  │
  ├─ 2. 并行处理
  │     ├─ FFmpeg 每3秒抽帧 (fps=1/3) + 场景检测
  │     └─ FFmpeg 音频分离(16kHz WAV) → Whisper ASR 逐字稿
  │
  ├─ 3. 豆包 Vision API 逐帧分析（3并发）
  │     每帧输出：景别/运镜/构图/转场/文字/情绪/关键元素
  │
  ├─ 4. 分段合并(每3秒) + 生成三类 AI 提示词
  │     ├─ 画面生成提示词 (visual)
  │     ├─ 文案改写提示词 (copywriting)
  │     └─ 复刻拍摄提示词 (recreation)
  │
  └─ 5. 整体爆点分析
        输出：钩子评分/情绪曲线/爆点因素/内容公式/复刻蓝图
```

---

## 三、API 设计

| 方法 | 路径 | 功能 | 说明 |
|------|------|------|------|
| POST | `/api/analyze` | 提交分析 | Body: `{"url": "...", "detail": {...}}` detail 可选 |
| GET | `/api/analyze/{task_id}/stream` | SSE 进度流 | 事件类型: progress/stage_complete/done/error |
| GET | `/api/results/{task_id}` | 获取完整结果 | 返回 FullAnalysisResult JSON |
| GET | `/api/video/{task_id}` | 流式视频 | video/mp4, 支持 Range |
| GET | `/api/frame/{task_id}/{filename}` | 帧图片 | image/jpeg |
| GET | `/api/health` | 健康检查 | `{"status": "ok"}` |

### SSE 事件格式
```
event: progress
data: {"stage": "downloading", "progress": 0.05, "message": "正在下载视频..."}

event: stage_complete
data: {"stage": "downloading", "result": {"title": "...", "author": "...", ...}}

event: done
data: {"task_id": "xxx"}

event: error
data: {"error": "错误描述"}
```

### 进度阶段
| 阶段 | stage 值 | 进度范围 |
|------|---------|---------|
| 视频下载 | downloading | 0-0.15 |
| 音频+抽帧 | extracting | 0.15-0.30 |
| 语音识别 | transcribing | 0.30-0.35 |
| 画面分析 | analyzing_frames | 0.35-0.70 |
| 提示词生成 | generating_prompts | 0.70-0.90 |
| 爆款分析 | viral_analysis | 0.90-1.00 |

---

## 四、项目结构

```
viral-video-analyzer/
├── .gitignore
├── backend/
│   ├── main.py                     # FastAPI 入口, CORS
│   ├── config.py                   # 环境变量配置 (pydantic-settings)
│   ├── requirements.txt            # Python 依赖
│   ├── .env                        # API Key, Endpoint ID 等
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analyze.py              # POST /api/analyze, GET /stream
│   │   └── results.py              # GET /results, /video, /frame
│   ├── services/
│   │   ├── __init__.py
│   │   ├── downloader.py           # Playwright 下载抖音视频
│   │   ├── video_processor.py      # FFmpeg 抽帧/音频分离
│   │   ├── transcriber.py          # faster-whisper ASR
│   │   ├── vision_analyzer.py      # 豆包 Vision API 逐帧分析
│   │   ├── viral_analyzer.py       # 整体爆点分析
│   │   └── pipeline.py             # 流水线编排 + SSE 事件
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic 数据模型
│   └── data/                       # 运行时数据 (gitignore)
│       └── {task_id}/
│           ├── detail.json         # 抖音 API 响应
│           ├── video.mp4           # 下载的视频
│           ├── audio.wav           # 分离的音频
│           ├── frames/             # 抽取的帧图片
│           └── result.json         # 完整分析结果
├── frontend/
│   ├── package.json
│   ├── .env.local                  # NEXT_PUBLIC_API_URL
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx          # 根布局
│   │   │   ├── page.tsx            # 首页(链接输入)
│   │   │   └── analysis/[taskId]/
│   │   │       └── page.tsx        # 结果页
│   │   ├── components/
│   │   │   ├── UrlInput.tsx        # 链接输入组件
│   │   │   ├── ProgressStream.tsx  # SSE 进度展示
│   │   │   ├── VideoPreview.tsx    # 视频播放器 (ref暴露seekTo)
│   │   │   ├── VideoMeta.tsx       # 视频基础信息
│   │   │   ├── ViralAnalysis.tsx   # 爆款分析卡片
│   │   │   ├── TranscriptView.tsx  # 逐字稿(点击跳转)
│   │   │   ├── TimelineView.tsx    # 时间线容器
│   │   │   ├── SegmentCard.tsx     # 单段分析(可展开)
│   │   │   └── PromptCard.tsx      # AI提示词(可复制)
│   │   ├── lib/
│   │   │   ├── api.ts              # 后端 API 客户端
│   │   │   └── sse.ts              # SSE 客户端
│   │   └── types/
│   │       └── index.ts            # TypeScript 类型定义
│   └── public/
```

---

## 五、环境配置

### 5.1 系统要求
- macOS (已验证 Darwin 24.6.0, ARM64)
- Node.js >= 24.x (推荐通过 fnm 管理)
- Python 3.12.x
- pnpm >= 10.x
- FFmpeg >= 8.0 (`brew install ffmpeg`)
- Chrome 浏览器 (Playwright 自带 headless Chromium, 不依赖系统 Chrome)

### 5.2 后端 .env 配置
```env
DOUBAO_API_KEY=<火山引擎 ARK API Key>
DOUBAO_VISION_ENDPOINT=<ep-xxx 推理接入点ID, 关联 Doubao-vision-pro-32k>
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DATA_DIR=data
DOUYIN_COOKIE_FILE=cookies.txt
```

### 5.3 前端 .env.local 配置
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 5.4 火山引擎配置步骤
1. 注册火山引擎账号: https://console.volcengine.com
2. 进入方舟控制台: https://console.volcengine.com/ark
3. API Key 管理 → 创建 API Key → 记录 Key 值
4. 模型推理 → 创建推理接入点 → 选择 **Doubao-1.5-vision-pro-32k** 模型 → 记录 `ep-xxxx` ID
5. 将 API Key 和 ep-xxxx 填入 `backend/.env`

**注意**: 接入点必须关联 **视觉理解模型** (Doubao-vision-pro), 不是视频生成模型 (Seedance)

---

## 六、安装与启动

### 6.1 一键安装
```bash
cd ~/viral-video-analyzer

# 后端
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install faster-whisper playwright httpx
playwright install chromium

# 前端
cd ../frontend
pnpm install
```

### 6.2 启动
```bash
# Terminal 1: 后端
cd ~/viral-video-analyzer/backend
source .venv/bin/activate
uvicorn main:app --port 8000

# Terminal 2: 前端
cd ~/viral-video-analyzer/frontend
pnpm dev

# 访问 http://localhost:3000
```

### 6.3 requirements.txt 完整依赖
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0
pydantic-settings>=2.0
sse-starlette>=2.0
openai>=1.10.0
aiofiles>=24.0
python-multipart>=0.0.9
faster-whisper>=1.0.0
playwright>=1.40.0
httpx>=0.27.0
```

---

## 七、核心数据模型

### 7.1 FullAnalysisResult (完整分析结果)
```json
{
  "task_id": "4fdb0563",
  "video_meta": {
    "title": "视频标题...",
    "author": "作者昵称",
    "author_id": "sec_uid",
    "likes": 1532,
    "comments": 53,
    "shares": 469,
    "duration": 67.3,
    "thumbnail_url": "https://..."
  },
  "transcript": [
    {
      "text": "其实网红博主他们都是用后置拍摄的",
      "start": 0.0,
      "end": 2.48,
      "words": [
        {"word": "其实", "start": 0.0, "end": 0.28},
        {"word": "网红", "start": 0.28, "end": 0.52}
      ]
    }
  ],
  "segments": [
    {
      "start_time": 0.0,
      "end_time": 3.0,
      "frames": [
        {
          "timestamp": 0.0,
          "frame_path": "frames/001_0.0s.jpg",
          "shot_type": "中景",
          "camera_movement": "固定",
          "composition": "中心构图",
          "transition": "无(首帧)",
          "text_overlay": "其实网红博主他们都是用后置拍摄",
          "visual_description": "一位女子手持手机，手机屏幕显示其本人后置拍摄画面",
          "mood": "平静",
          "key_elements": ["女子", "手机", "手机屏幕中的影像"]
        }
      ],
      "transcript": "其实网红博主他们都是用后置拍摄的...",
      "ai_prompts": {
        "visual": "近景，室内柔和光线，一位女子手持手机...",
        "copywriting": "风格：科普讲解；句式：陈述句；字数：30字以内...",
        "recreation": "拍摄一个3秒开场：中景镜头，固定机位..."
      }
    }
  ],
  "viral_analysis": {
    "hook_score": 7,
    "hook_analysis": "前3秒通过展示女子手持手机...",
    "pacing_analysis": "信息密度适中，每3秒左右切换一次画面...",
    "emotional_arc": "好奇→理性→感叹→认可",
    "key_viral_factors": ["针对痛点提供解决方案", "直观展示产品功能"],
    "target_audience": "网红博主、自媒体从业者...",
    "content_formula": "痛点展示+产品介绍+功能演示+效果呈现",
    "recreation_blueprint": "1. 明确目标受众痛点\n2. 详细介绍产品功能\n3. 展示使用效果"
  },
  "created_at": "2026-03-30T00:02:35.123456"
}
```

---

## 八、AI 提示词设计

### 8.1 逐帧分析 System Prompt
```
你是一位专业的短视频拍摄分析师和导演。你的任务是对短视频的每一帧画面进行专业的"拆片"分析。

请严格按照以下JSON格式输出分析结果，不要添加任何额外文字：

{
  "shot_type": "景别：大特写/特写/近景/中景/全景/远景",
  "camera_movement": "运镜：固定/左摇/右摇/上摇/下摇/推进/拉远/跟拍/环绕/手持晃动",
  "composition": "构图：中心构图/三分法/对角线/框架式/引导线/对称/留白",
  "transition": "与上一帧的转场方式：硬切/溶解/擦除/滑动/缩放/无(首帧)",
  "text_overlay": "画面上出现的文字内容，没有则为null",
  "visual_description": "用一句话描述画面内容和动作",
  "mood": "画面情绪：激昂/平静/悬疑/搞笑/温馨/紧张/震撼/治愈",
  "key_elements": ["画面中的关键视觉元素列表"]
}
```

### 8.2 提示词生成 System Prompt
```
你是一位短视频创作导演和文案专家。
根据提供的视频片段分析数据（包含画面分析和对应文案），请生成三种AI提示词：

1. **visual**：用于AI生图/生视频工具复现画面风格和内容
2. **copywriting**：用于AI写出类似风格和节奏的文案/口播稿
3. **recreation**：完整的拍摄指导，包括景别、运镜、道具、演员指导

请用JSON格式输出：{"visual": "...", "copywriting": "...", "recreation": "..."}
```

### 8.3 爆款分析 System Prompt
```
你是一位顶级的短视频运营专家和爆款分析师，曾分析过超过10000条百万赞爆款短视频。

你的任务是分析一条短视频的"爆款密码"。

请严格按以下JSON格式输出：
{
  "hook_score": 8,
  "hook_analysis": "前3秒钩子分析",
  "pacing_analysis": "节奏分析",
  "emotional_arc": "情绪曲线",
  "key_viral_factors": ["爆点因素"],
  "target_audience": "目标受众画像",
  "content_formula": "底层内容公式",
  "recreation_blueprint": "分步复刻指南"
}
```

---

## 九、关键实现细节

### 9.1 视频下载 (downloader.py)
- 使用 **Playwright headless Chromium** 打开抖音页面
- 通过 `page.on("response")` 拦截 `aweme/v1/web/aweme/detail` API 响应
- 从响应 JSON 中提取 `bit_rate` 列表，选最高码率的 `douyinvod.com` URL
- 用 `curl -L` 下载视频文件
- 支持 `v.douyin.com` 短链接自动解析（httpx HEAD 请求跟随重定向）

### 9.2 帧提取 (video_processor.py)
- `ffmpeg -vf "fps=1/3,scale=1280:-2"` 每3秒抽一帧
- `ffmpeg -vf "select='gt(scene,0.3)',showinfo"` 场景切换检测
- 两次提取的帧合并去重（相距 < 0.3s 的去掉）
- 音频分离: `ffmpeg -vn -acodec pcm_s16le -ar 16000 -ac 1`

### 9.3 语音识别 (transcriber.py)
- **faster-whisper**, model="small", device="cpu", compute_type="int8"
- 启用 `word_timestamps=True` 和 `vad_filter=True`
- 通过 `asyncio.run_in_executor` 放到线程池执行，避免阻塞事件循环

### 9.4 视觉分析 (vision_analyzer.py)
- 豆包 Vision API, OpenAI SDK 兼容格式
- 每帧发送当前帧 + 上一帧（用于转场分析）
- 图片以 base64 编码嵌入请求
- **3帧并发**: `asyncio.gather` 批量调用
- 同步 SDK 调用通过 `run_in_executor` 异步化

### 9.5 SSE 进度推送 (pipeline.py + analyze.py)
- `asyncio.Queue` 作为事件通道
- `BackgroundTasks` 执行流水线
- `sse-starlette` 的 `EventSourceResponse` 推送事件
- 超时 300s 发 ping 保活

---

## 十、踩坑记录与解决方案

### 10.1 yt-dlp 无法下载抖音视频
**错误**: `ERROR: [Douyin] Fresh cookies (not necessarily logged in) are needed`

**原因**: yt-dlp 的 `--cookies-from-browser chrome` 虽然能提取 649 个 Cookie，但缺少关键的 `s_v_web_id` (HttpOnly Cookie)，导致抖音 API 返回空 JSON。

**手动导出 Cookie 文件也无效**: `document.cookie` 只能获取非 HttpOnly Cookie，缺少 `ttwid`、`odin_tt` 等关键 HttpOnly Cookie。

**最终解决方案**: 放弃 yt-dlp，改用 **Playwright headless Chromium** 直接打开抖音页面。Playwright 会自动处理 Cookie 和 JS 执行环境，通过拦截页面的 XHR 网络请求获取 `aweme/v1/web/aweme/detail` API 响应。

### 10.2 豆包 API 模型名 vs Endpoint ID
**错误**: `InvalidEndpointOrModel.NotFound - The model or endpoint doubao-1.5-vision-pro-250328 does not exist`

**原因**: 火山引擎方舟平台不支持直接使用模型名调用，必须先在控制台创建 **推理接入点**，获得 `ep-xxxx` 格式的 Endpoint ID。

**解决方案**:
1. 登录火山引擎控制台 → 模型推理 → 创建推理接入点
2. 搜索选择 **Doubao-1.5-vision-pro-32k** 模型
3. 创建后获得 `ep-20260329223212-dltgm` 格式的 ID
4. 在 `.env` 中配置 `DOUBAO_VISION_ENDPOINT=ep-xxx`

**注意**: 第一次错误创建了 Seedance (视频生成模型) 的接入点，返回 `InternalServiceError`。必须选择 **视觉理解模型** (vision-pro)。

### 10.3 Whisper 阻塞事件循环
**现象**: 提交分析后，SSE 无输出，后端卡死无响应，持续数分钟。

**原因**: `faster_whisper.WhisperModel.transcribe()` 是同步阻塞调用。在 `async def` 中直接调用会阻塞 uvicorn 的事件循环，导致 SSE 推送、API 响应全部卡住。

**解决方案**: 所有同步阻塞调用（Whisper、OpenAI SDK）都通过 `asyncio.run_in_executor(None, func)` 放到线程池执行:
```python
async def transcribe_with_whisper(audio_path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, functools.partial(_run_whisper_sync, audio_path)
    )
```
同样适用于 `vision_analyzer.py` 和 `viral_analyzer.py` 中的 OpenAI SDK 调用。

### 10.4 67帧分析耗时过长
**现象**: 67秒视频每秒抽1帧 = 67帧，每帧调一次豆包 API，5分钟只完成 11/67 帧。

**解决方案**:
1. **降低抽帧频率**: `fps=1` → `fps=1/3`（每3秒一帧），67帧降至约22帧
2. **并发分析**: 每次用 `asyncio.gather` 并发3帧分析，总 API 调用批次从 67 降至 ~8

优化后: 67秒视频全流程约 3 分钟完成。

### 10.5 后端 uvicorn --reload 导致状态丢失
**现象**: pip 安装新包时，`--reload` 模式的 WatchFiles 检测到 `.venv` 目录变化，触发服务重启，内存中的 task store 被清空，正在运行的分析任务丢失。

**解决方案**: 生产运行时不使用 `--reload` 参数:
```bash
uvicorn main:app --port 8000  # 不加 --reload
```

### 10.6 端口冲突
**现象**: `Address already in use` (端口 8000 或 3000 被占用)

**解决方案**:
```bash
lsof -ti:8000 | xargs kill -9  # 释放后端端口
lsof -ti:3000 | xargs kill -9  # 释放前端端口
```

### 10.7 pip 安装超时
**现象**: `ReadTimeoutError: HTTPSConnectionPool(host='files.pythonhosted.org') Read timed out`

**解决方案**: 使用国内镜像源:
```bash
pip install <package> -i https://pypi.tuna.tsinghua.edu.cn/simple
# 或
pip install <package> -i https://mirrors.aliyun.com/pypi/simple/
```

---

## 十一、性能指标

基于测试视频（67.3秒，20.8MB）的实测数据：

| 阶段 | 耗时 | 说明 |
|------|------|------|
| Playwright 获取详情 | ~5s | 打开页面+拦截API |
| 视频下载 (curl) | ~3s | 20.8MB |
| FFmpeg 抽帧+音频 | ~3s | 22帧 + WAV |
| Whisper ASR (CPU) | ~30s | small model, 67s音频 |
| 豆包 Vision 分析 | ~90s | 22帧, 3并发, ~8批次 |
| 提示词生成 | ~60s | 7-8段, 逐段调用 |
| 爆款分析 | ~10s | 1次API调用 |
| **总计** | **~3分钟** | |

---

## 十二、后续迭代规划

### v1.1 (近期)
- [ ] 展开/收起箭头 HTML 实体渲染修复 (`&#9660;`)
- [ ] 分析历史记录列表页
- [ ] 支持抖音分享文本中提取链接 (已部分实现)
- [ ] 错误重试机制 (单帧分析失败不影响整体)

### v1.2 (中期)
- [ ] 交互式编辑器 (拖拽调整段落、修改文案)
- [ ] 导出复刻脚本 (Markdown / PDF)
- [ ] 分镜表导出
- [ ] BGM 分析 (音乐风格、节奏标记)

### v2.0 (远期)
- [ ] 多平台支持 (快手、小红书、B站)
- [ ] 批量分析
- [ ] 爆款模板库
- [ ] 基于分析结果直接生成复刻视频 (Seedance API)
- [ ] 用户系统 + 云端部署

---

## 附录 A: 两个 API Key 说明

本项目涉及两个火山引擎 API Key:

| Key | 用途 | 备注 |
|-----|------|------|
| `<API_KEY_1>` | 初始 Key, 视频拉片项目 | 无法直接用模型名调用 |
| `<API_KEY_2>` | 当前使用的 Key | 配合 ep-xxx Endpoint 使用 |

Endpoint ID: `<ep-xxx>` → 关联模型: Doubao-1.5-vision-pro-32k

---

## 附录 B: 快速验证命令

```bash
# 验证后端健康
curl http://localhost:8000/api/health

# 验证豆包 API
curl -X POST https://ark.cn-beijing.volces.com/api/v3/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{"model": "<ENDPOINT_ID>", "messages": [{"role": "user", "content": "回复OK"}], "max_tokens": 10}'

# 验证 FFmpeg
ffmpeg -version | head -1

# 验证 Playwright
cd backend && source .venv/bin/activate && python3 -c "from playwright.async_api import async_playwright; print('OK')"

# 验证 Whisper
python3 -c "from faster_whisper import WhisperModel; print('OK')"
```
