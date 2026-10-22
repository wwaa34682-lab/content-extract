#!/usr/bin/env python3
"""在仓库内创建 .venv 并安装依赖（跨平台）。之后用 .venv 的 python 运行 extract.py。"""
import subprocess, sys, venv, os
from pathlib import Path
root = Path(__file__).resolve().parent.parent; v = root / ".venv"
if not v.exists(): venv.create(v, with_pip=True)
py = v / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
subprocess.check_call([str(py), "-m", "pip", "install", "-q", "-U", "pip"])
subprocess.check_call([str(py), "-m", "pip", "install", "-q", "-r", str(root / "requirements.txt")])
subprocess.call([str(py), str(root / "scripts/doctor.py")])
print(f"\n运行： {py} {root/'scripts/extract.py'} <链接或文件>")
