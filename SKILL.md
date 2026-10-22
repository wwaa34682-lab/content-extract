---
name: content-extract
description: 把短视频/音频（本地文件或抖音、B站、小红书、YouTube 等公开链接）转成带时间戳的中文文稿、关键帧和"钩子-结构-卖点-CTA-改写方向-受众适配"拆解模板，并输出可导入知识库(RAG)的 JSONL。当用户要"把这个视频转文字""拆解对标作品""分析爆款结构""批量整理竞品视频文案"时使用。全本地运行，Linux/macOS/Windows 通用。
---

# content-extract

## 何时用
- 用户给出视频/音频文件或公开作品链接，想要文字稿、字幕、关键帧或爆款拆解。
- 想把对标内容沉淀进知识库或选题库。

## 首次安装（每台机器一次）
在仓库根目录：
- macOS/Linux：`sh install.sh`
- Windows (PowerShell)：`powershell -ExecutionPolicy Bypass -File install.ps1`
然后运行 `<venv python> scripts/doctor.py`，全部 ✓ 再继续。venv python 路径：macOS/Linux `.venv/bin/python`，Windows `.venv\Scripts\python.exe`。
ASR 模型（faster-whisper，默认 small，约 460MB）首次运行时自动下载。

## 用法
```
<venv python> scripts/extract.py <链接或文件> [-o 输出目录] [-c 配置.yaml] [--model small|medium] [--keep-media]
```
标准输出最后一行是 JSON：`{"status": "ok|failed", "dir": ..., "error": ...}`。退出码 0 成功，2 失败。

## 产物（每条一个目录）
`transcript.md`（带时间戳）/ `transcript.txt` / `transcript.srt` / `segments.json` / `cover.jpg` / `frames/` / `breakdown.md`（拆解模板，【待填】处由你补全）/ `meta.json` / `rag_record.jsonl`。

## Agent 工作步骤
1. 跑 doctor；缺项就跑 install。
2. 跑 extract；若 `status=failed`，把 `error` 原样告诉用户（常见：平台需要 cookie/风控），建议用户自行下载后传本地文件。**不要**自行读取浏览器 cookie 或使用用户账号登录。
3. 读 `transcript.md`、看 `frames/` 若干帧，填完 `breakdown.md` 的所有【待填】，参考 `references/breakdown_guide.md`。
4. 根据用户配置（`config.yaml` 的行业、受众占比、文案类型）给出改写建议；只借鉴结构，不搬运原文。
5. 需要入库时，把 `rag_record.jsonl` 交给用户的知识库导入流程；本工具不写任何外部系统。

## 配置
复制 `config.example.yaml` 为 `config.yaml`，改行业、受众及占比、文案类型、术语热词与纠错表。`presets/` 下有示例。
