# content-extract · 短视频文案提取与爆款拆解（全平台本地版）

把一条短视频/音频变成：**带时间戳的中文文稿 + 封面/关键帧 + 爆款拆解模板 + 知识库导入文件**。
全本地运行（faster-whisper），不上传音视频，不需要任何账号登录。支持 **Windows / macOS / Linux**，可被 Codex、Claude Code、Cursor 等任意 Agent 作为 Skill 使用。

## 效果（实测）
- 一条 2.5 分钟中文高尔夫教学视频，8 核 CPU、small 模型：转写 12 秒（实时率 0.08），整条流水线约 17 秒。
- 中文可直接阅读；行业术语可通过配置里的 `hotwords` / `replacements` 纠正（如"机球→击球"）。

## 给 Agent 的一句话安装提示
> 克隆 https://github.com/<you>/content-extract ，在仓库根目录运行 install 脚本（Windows 用 install.ps1，其余用 install.sh），然后按 SKILL.md 使用。

想作为 Skill 常驻：把整个仓库放到你的 Agent 的 skills 目录（如 `~/.claude/skills/content-extract`、`~/.codex/skills/content-extract` 或项目内 `.cursor/skills/`）。

## 手动安装
需要 Python 3.9+。ffmpeg 会通过 `imageio-ffmpeg` 自动带一个，无需另装（已装系统 ffmpeg 会优先使用）。

**macOS / Linux**
```sh
git clone https://github.com/<you>/content-extract && cd content-extract
sh install.sh
.venv/bin/python scripts/extract.py "https://www.youtube.com/watch?v=xxxx"
```

**Windows（PowerShell）**
```powershell
winget install Python.Python.3.12        # 如未安装 Python
git clone https://github.com/<you>/content-extract; cd content-extract
powershell -ExecutionPolicy Bypass -File install.ps1
.venv\Scripts\python.exe scripts\extract.py "D:\素材\视频 1.mp4"
```
可选：`winget install Gyan.FFmpeg` 安装系统 ffmpeg；中文乱码时先执行 `$env:PYTHONUTF8=1`。

自检：`python scripts/doctor.py`（会检查系统、Python、ffmpeg、依赖、中文文件名写入）。

## 用法
```
python scripts/extract.py <链接或本地文件> [-o 输出目录] [-c config.yaml] [--model small|medium|large-v3] [--keep-media]
```
默认输出到 `./extract-output/<时间>_<哈希>/`：

| 文件 | 内容 |
|---|---|
| transcript.md / .txt / .srt / segments.json | 文稿（带时间戳）、纯文本、字幕、分段 JSON |
| cover.jpg, frames/ | 封面与均匀抽取的关键帧 |
| breakdown.md | 拆解模板：钩子(前3秒自动摘录)、结构时间轴、卖点、CTA 候选、改写方向、受众适配（【待填】交给 Agent/人补全） |
| meta.json | 标题、作者、时长、平台、互动数、转写耗时、失败原因 |
| rag_record.jsonl | 一行一条，可导入任意 RAG/知识库 |

## 配置
`cp config.example.yaml config.yaml` 后修改：行业、受众及占比、文案类型、ASR 模型、术语热词与纠错表。`presets/golf-teaching-example.yaml` 是一个高尔夫教学门店的示例。

## 平台支持（匿名、无 cookie，2026-10 实测）
| 平台 | 状态 |
|---|---|
| 本地文件（mp4/mov/mp3/m4a/wav…） | ✅ 稳定 |
| YouTube | ✅ 可用 |
| B 站 | ⚠️ 常被风控（HTTP 412），失败时请手动下载后传本地文件 |
| 抖音 | ❌ 需要 cookie |
| 小红书 | ❌ 匿名常取不到视频 |

失败会写进 `meta.json` 的 `error`，不会中断批处理。本工具**刻意不读取浏览器 cookie、不登录任何账号**，以免账号被风控；请只处理你有权使用的公开内容，拆解仅用于学习结构，勿搬运。

## 已知限制
- 拆解中的主观判断（钩子类型、卖点、改写建议）需要 LLM 或人来填，脚本只生成结构化草稿。
- small 模型对专业术语有同音错字，可调大模型（medium 更准，约慢 3 倍）或加 replacements。
- 纯音乐/无人声视频文稿为空，仍会产出关键帧。

## License
MIT
