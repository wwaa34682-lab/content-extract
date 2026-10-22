#!/usr/bin/env python3
"""content-extract: 音视频/公开链接 -> 带时间戳文稿 + 关键帧 + 拆解模板 + RAG 导入文件。"""
import argparse, json, os, re, shutil, subprocess, sys, time, hashlib, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CTA_WORDS = ["关注", "点赞", "收藏", "评论", "私信", "链接", "预约", "报名", "下单", "主页", "扫码", "到店", "体验课"]

def load_cfg(path):
    import yaml
    p = Path(path) if path else (ROOT / "config.yaml" if (ROOT / "config.yaml").exists() else ROOT / "config.example.yaml")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

def ffmpeg_exe():
    p = shutil.which("ffmpeg")
    if p: return p
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception: return None

FF = ffmpeg_exe() or "ffmpeg"

def run(cmd):
    if cmd and cmd[0] == "ffmpeg": cmd = [FF] + cmd[1:]
    return subprocess.run(cmd, capture_output=True, text=True)

def slug(s, n=40):
    s = re.sub(r'[\\/:*?"<>|\s]+', "_", s).strip("_")
    return s[:n] or "item"

def download(url, work):
    """只用匿名下载，不读取任何浏览器 cookie。"""
    cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--ffmpeg-location", FF,
           "-f", "bv*[height<=720]+ba/b[height<=720]/b/ba", "--merge-output-format", "mp4",
           "--write-info-json", "--write-thumbnail", "-o", str(work / "source.%(ext)s"), url]
    r = run(cmd)
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip().splitlines()
        raise RuntimeError(err[-1] if err else "yt-dlp failed")
    info = {}
    j = next(work.glob("source*.info.json"), None)
    if j:
        d = json.loads(j.read_text(encoding="utf-8"))
        info = {k: d.get(k) for k in ["title", "uploader", "duration", "upload_date", "extractor_key",
                                         "view_count", "like_count", "comment_count", "webpage_url", "description"]}
        j.unlink()
    media = next(p for p in work.glob("source.*") if p.suffix not in (".json", ".webp", ".jpg", ".png", ".part"))
    for t in work.glob("source.*"):
        if t.suffix in (".webp", ".jpg", ".png"):
            run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(t), str(work / "cover.jpg")]); t.unlink()
    return media, info

def transcribe(media, work, cfg):
    from faster_whisper import WhisperModel
    a = cfg.get("asr", {})
    wav = work / "audio.wav"
    r = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    if r.returncode: raise RuntimeError("ffmpeg 抽音频失败: " + r.stderr[-300:])
    dev = a.get("device", "auto")
    model = WhisperModel(a.get("model", "small"), device=dev, compute_type=a.get("compute_type", "int8"))
    conv = None
    if a.get("simplified", True):
        try:
            import opencc; conv = opencc.OpenCC("t2s")
        except Exception: pass
    t0 = time.time()
    import wave, numpy as np
    with wave.open(str(wav), "rb") as w:  # 自己解码 16k 单声道 PCM，绕开 PyAV 版本兼容问题
        audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    segs, info = model.transcribe(audio, language=a.get("language") or None, vad_filter=True,
                                  initial_prompt="以下是普通话的句子，使用简体中文和标点。" + ("相关词：" + "、".join(a.get("hotwords") or []) if a.get("hotwords") else ""))
    out = []
    for s in segs:
        txt = s.text.strip()
        if conv: txt = conv.convert(txt)
        for k, v in (a.get("replacements") or {}).items(): txt = txt.replace(k, v)
        out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": txt})
    wav.unlink()
    return out, round(time.time() - t0, 1), info.duration

def ts(x, srt=False):
    h, m, s = int(x // 3600), int(x % 3600 // 60), x % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",") if srt else f"{h:02d}:{m:02d}:{int(s):02d}"

def keyframes(media, work, cfg, duration):
    k = cfg.get("keyframes", {}); iv = k.get("interval_sec", 5); mx = k.get("max_frames", 12)
    fd = work / "frames"; fd.mkdir(exist_ok=True)
    if duration and duration / iv > mx: iv = duration / mx
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(media), "-vf", f"fps=1/{iv},scale=540:-2",
         "-frames:v", str(mx), str(fd / "f_%03d.jpg")])
    frames = sorted(fd.glob("*.jpg"))
    if not (work / "cover.jpg").exists():
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.5", "-i", str(media), "-frames:v", "1", str(work / "cover.jpg")])
    return [{"file": f"frames/{f.name}", "t": round(i * iv, 1)} for i, f in enumerate(frames)]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="本地音视频路径或公开作品链接")
    ap.add_argument("-o", "--out", default="./extract-output", help="输出根目录")
    ap.add_argument("-c", "--config", help="配置 yaml（默认 config.yaml 或 config.example.yaml）")
    ap.add_argument("--model", help="覆盖 ASR 模型，如 base/small/medium")
    ap.add_argument("--keep-media", action="store_true", help="保留下载的原视频")
    a = ap.parse_args()
    cfg = load_cfg(a.config)
    if a.model: cfg.setdefault("asr", {})["model"] = a.model
    if not ffmpeg_exe(): sys.exit("缺少 ffmpeg，先运行 scripts/doctor.py")
    is_url = re.match(r"https?://", a.input)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    work = Path(a.out) / f"{stamp}_{hashlib.md5(a.input.encode()).hexdigest()[:6]}"
    work.mkdir(parents=True)
    meta = {"source": a.input, "is_url": bool(is_url), "created": stamp, "status": "running"}
    try:
        if is_url:
            media, info = download(a.input, work); meta.update(info)
        else:
            src = Path(a.input).expanduser()
            if not src.exists(): raise RuntimeError("文件不存在")
            media = src; meta.update({"title": src.stem, "extractor_key": "local"})
        segs, asr_sec, dur = transcribe(media, work, cfg)
        meta.update({"duration": meta.get("duration") or round(dur, 1), "asr_model": cfg.get("asr", {}).get("model", "small"),
                     "asr_seconds": asr_sec, "rtf": round(asr_sec / dur, 3) if dur else None})
        has_video = "Video:" in run(["ffmpeg", "-hide_banner", "-i", str(media)]).stderr
        meta["frames"] = keyframes(media, work, cfg, dur) if has_video else []
        full = "".join(s["text"] for s in segs)
        (work / "transcript.txt").write_text(full + "\n", encoding="utf-8")
        (work / "transcript.md").write_text("\n".join(f"[{ts(s['start'])}] {s['text']}" for s in segs) + "\n", encoding="utf-8")
        (work / "transcript.srt").write_text("\n".join(f"{i}\n{ts(s['start'],1)} --> {ts(s['end'],1)}\n{s['text']}\n" for i, s in enumerate(segs, 1)), encoding="utf-8")
        (work / "segments.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding="utf-8")
        t0s = segs[0]["start"] if segs else 0
        hook = "".join(s["text"] for s in segs if s["start"] < t0s + 3.5) or (segs[0]["text"] if segs else "")
        cta = [s["text"] for s in segs if any(w in s["text"] for w in CTA_WORDS)][-3:]
        step = max(1, len(segs) // 8)
        outline = "\n".join(f"- [{ts(s['start'])}] {s['text'][:60]}" for s in segs[::step]) or "- （无语音）"
        tpl = (ROOT / "references" / "breakdown_template.md").read_text(encoding="utf-8")
        md = tpl.format(title=meta.get("title", ""), source=a.input, platform=meta.get("extractor_key", ""),
            uploader=meta.get("uploader", "") or "", duration=meta.get("duration"), industry=cfg.get("industry", ""),
            audience_profile=cfg.get("audience_profile", ""), hook=hook, outline=outline,
            cta_guess=" / ".join(cta) or "无",
            rewrite_rows="\n".join(f"| {t} | 【待填】 | 【待填】 |" for t in cfg.get("rewrite_types", [])),
            audience_rows="\n".join(f"| {x['name']} | {x.get('share','')}% | 【待填】 | {x.get('note','')} |" for x in cfg.get("audiences", [])))
        (work / "breakdown.md").write_text(md, encoding="utf-8")
        rec = {"id": "CE-" + hashlib.md5(a.input.encode()).hexdigest()[:10], "type": "对标拆解",
               "title": meta.get("title", ""), "source": meta.get("webpage_url") or (a.input if is_url else meta.get("title")),
               "platform": meta.get("extractor_key"), "date": stamp[:8], "status": "待确认",
               "content": f"标题：{meta.get('title','')}\n钩子：{hook}\n文稿：{full}"}
        (work / "rag_record.jsonl").write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
        if is_url and not a.keep_media: media.unlink(missing_ok=True)
        meta["status"] = "ok"
    except Exception as e:
        meta.update({"status": "failed", "error": str(e)})
    meta.pop("description", None) if meta.get("description") and len(meta["description"]) > 2000 else None
    (work / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": meta["status"], "dir": str(work.resolve()), "error": meta.get("error"),
                      "asr_seconds": meta.get("asr_seconds"), "rtf": meta.get("rtf")}, ensure_ascii=False))
    sys.exit(0 if meta["status"] == "ok" else 2)

if __name__ == "__main__":
    main()
