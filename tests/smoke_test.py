#!/usr/bin/env python3
"""冒烟测试：用 ffmpeg 生成 3 秒测试视频（色块+正弦音），跑完整流水线（tiny 模型），检查产物齐全。"""
import json, subprocess, sys, tempfile
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "scripts"))
from extract import ffmpeg_exe
with tempfile.TemporaryDirectory() as d:
    d = Path(d); vid = d / "测试 视频.mp4"
    subprocess.check_call([ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10:duration=3",
                           "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-shortest", "-pix_fmt", "yuv420p", str(vid)])
    r = subprocess.run([sys.executable, str(root / "scripts/extract.py"), str(vid), "-o", str(d / "out"), "--model", "tiny"],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout, r.stderr[-1500:])
    res = json.loads(r.stdout.strip().splitlines()[-1]); assert res["status"] == "ok", res
    out = Path(res["dir"])
    for f in ["meta.json", "transcript.md", "transcript.srt", "breakdown.md", "rag_record.jsonl", "cover.jpg"]:
        assert (out / f).exists(), f
    assert list((out / "frames").glob("*.jpg")), "frames"
print("SMOKE OK")
