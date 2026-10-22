#!/usr/bin/env python3
"""自检：系统、Python、ffmpeg（系统或 imageio-ffmpeg 内置）、Python 依赖、输出目录可写。"""
import importlib, os, shutil, sys, platform, subprocess, tempfile
ok = True
osn = platform.system()
print(f"系统 {osn} {platform.release()} {platform.machine()} | Python {sys.version.split()[0]} ({sys.executable})")
if osn == "Windows":
    print("  Windows：建议在 PowerShell 运行；路径含中文/空格没问题；如遇执行策略限制：Set-ExecutionPolicy -Scope Process Bypass")
    if os.environ.get("PYTHONUTF8") != "1": print("  提示：可设 $env:PYTHONUTF8=1 避免控制台中文乱码（非必需）")
if sys.version_info < (3, 9): print("✗ 需要 Python >= 3.9"); ok = False
ff = shutil.which("ffmpeg"); src = "系统"
if not ff:
    try: import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe(); src = "imageio-ffmpeg 内置"
    except Exception: ff = None
if ff and subprocess.run([ff, "-version"], capture_output=True).returncode == 0: print(f"✓ ffmpeg（{src}）{ff}")
else:
    ok = False; print("✗ ffmpeg → 运行 install 脚本（自动装 imageio-ffmpeg），或 Win: winget install Gyan.FFmpeg | mac: brew install ffmpeg | Ubuntu: sudo apt install ffmpeg")
for m in ("faster_whisper", "yt_dlp", "opencc", "yaml"):
    try: importlib.import_module(m); print("✓ " + m)
    except ImportError: print("✗ " + m + " → python scripts/install.py"); ok = False
try:
    with tempfile.TemporaryDirectory() as d: open(os.path.join(d, "测试.txt"), "w", encoding="utf-8").write("ok")
    print("✓ 中文文件名可写")
except Exception as e: print("✗ 中文文件名写入失败", e); ok = False
print("全部就绪" if ok else "有缺项，见上"); sys.exit(0 if ok else 1)
