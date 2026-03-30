# 爆款短视频拉片复刻系统

AI 驱动的短视频拉片分析工具 —— 输入抖音链接，自动完成秒级拆解、逐字稿提取、爆款密码分析、复刻提示词生成。

## 功能展示

### 首页
粘贴抖音视频链接，一键开始分析。

### 分析进度
SSE 实时推送，六个阶段逐步完成：下载视频 → 提取关键帧 → 语音识别 → 画面分析 → 提示词生成 → 爆款分析。

### 结果页
- **视频播放器** + 基础数据（点赞/评论/分享）
- **爆款分析**：钩子评分、爆点因素、情绪曲线、内容公式、复刻蓝图
- **完整口播文案**：带时间戳，点击跳转视频对应位置
- **逐秒拆解**：每段包含帧截图、景别/运镜/构图/情绪标签
- **AI 提示词**：画面提示词 / 文案提示词 / 复刻提示词，一键复制

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js + TypeScript + Tailwind CSS |
| 后端 | Python FastAPI |
| 视频下载 | Playwright (headless Chromium) |
| 视频处理 | FFmpeg |
| 语音识别 | faster-whisper (本地 CPU) |
| 多模态分析 | 豆包 Vision API (火山引擎) |
| 进度推送 | SSE (Server-Sent Events) |

## 快速开始

### 环境要求

- macOS / Linux
- Node.js >= 20
- Python >= 3.10
- FFmpeg (`brew install ffmpeg`)
- pnpm (`npm install -g pnpm`)

### 1. 克隆项目

```bash
git clone https://github.com/pelpeljakob-creator/viral-video-analyzer.git
cd viral-video-analyzer
```

### 2. 配置火山引擎 API

1. 注册 [火山引擎](https://console.volcengine.com) 账号
2. 进入 [方舟控制台](https://console.volcengine.com/ark) → API Key 管理 → 创建 API Key
3. 模型推理 → 创建推理接入点 → 选择 **Doubao-1.5-vision-pro-32k** → 记录 `ep-xxxx` ID

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`：
```env
DOUBAO_API_KEY=your-api-key-here
DOUBAO_VISION_ENDPOINT=ep-your-endpoint-id
```

### 3. 安装后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install faster-whisper playwright httpx
playwright install chromium
```

### 4. 安装前端

```bash
cd ../frontend
cp .env.local.example .env.local
pnpm install
```

### 5. 启动

```bash
# Terminal 1: 后端
cd backend && source .venv/bin/activate && uvicorn main:app --port 8000

# Terminal 2: 前端
cd frontend && pnpm dev
```

打开 http://localhost:3000 ，粘贴抖音视频链接即可使用。

## 工作原理

```
用户粘贴抖音链接
  │
  ├─ Playwright 打开抖音页面，拦截 API 获取视频详情
  │   └─ 提取最高码率视频 URL → 下载
  │
  ├─ FFmpeg 每3秒抽帧 + 场景切换检测
  │
  ├─ FFmpeg 音频分离 → Whisper 逐字稿（词级时间戳）
  │
  ├─ 豆包 Vision API 逐帧分析（3并发）
  │   └─ 景别 / 运镜 / 构图 / 转场 / 文字 / 情绪
  │
  ├─ 每段生成 3 类 AI 提示词
  │   ├─ 画面生成提示词（用于 AI 生图/生视频）
  │   ├─ 文案改写提示词（用于 AI 写口播稿）
  │   └─ 复刻拍摄提示词（完整拍摄指导）
  │
  └─ 整体爆款分析
      └─ 钩子评分 / 爆点因素 / 情绪曲线 / 内容公式 / 复刻蓝图
```

## 项目结构

```
viral-video-analyzer/
├── backend/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   ├── services/
│   │   ├── downloader.py       # Playwright 视频下载
│   │   ├── video_processor.py  # FFmpeg 抽帧/音频
│   │   ├── transcriber.py      # Whisper 语音识别
│   │   ├── vision_analyzer.py  # 豆包 Vision 逐帧分析
│   │   ├── viral_analyzer.py   # 爆款分析
│   │   └── pipeline.py         # 流水线编排 + SSE
│   ├── routers/                # API 路由
│   └── models/                 # 数据模型
├── frontend/
│   └── src/
│       ├── app/                # 页面（首页 + 结果页）
│       ├── components/         # UI 组件
│       ├── lib/                # API 客户端 + SSE
│       └── types/              # TypeScript 类型
└── PRD.md                      # 完整产品文档
```

## 性能参考

以 67 秒抖音视频实测：

| 阶段 | 耗时 |
|------|------|
| 视频获取+下载 | ~8s |
| 抽帧+音频分离 | ~3s |
| 语音识别 (CPU) | ~30s |
| AI 画面分析 (22帧) | ~90s |
| 提示词+爆款分析 | ~70s |
| **总计** | **~3 分钟** |

## 注意事项

- 首次运行 Whisper 会自动下载模型文件（约 500MB），请耐心等待
- 豆包 API 有免费额度（约 200 万 token），足够分析数十个视频
- 创建推理接入点时务必选择 **视觉理解模型** (Doubao-vision-pro)，不是视频生成模型

## 许可证

MIT
