# Copyright (C) 2026 TPW-894 / Licensed under GPL-3.0-or-later

import json, os, re, shutil, subprocess, sys
from pathlib import Path

from i18n import tr

BASE = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
_NOWIN = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def find_tool(name):
    exe = name + (".exe" if os.name == "nt" else "")
    for p in (BASE / exe, BASE / "ffmpeg" / "bin" / exe):
        if p.exists():
            return str(p)
    return shutil.which(name)


def find_ffmpeg():
    return find_tool("ffmpeg")


def detect(src):
    fp = find_tool("ffprobe")
    if not fp:
        return None
    r = _run([fp, "-v", "error", "-of", "json", "-flags2", "+export_mvs", "-export_side_data", "venc_params",
              "-select_streams", "v:0", "-read_intervals", "%+#30", "-show_frames", "-i", str(src)])
    try:
        frames = json.loads(r.stdout).get("frames", [])
    except Exception:
        return None
    if not frames:
        return None
    types = [sd.get("side_data_type", "").lower() for f in frames for sd in f.get("side_data_list", [])]
    return {"mv": any("motion" in t for t in types), "venc": any("param" in t for t in types)}


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", creationflags=_NOWIN)


def capabilities(ff):
    r = _run([ff, "-hide_banner", "-h", "filter=codecview"])
    t = r.stdout + r.stderr
    return {k: bool(re.search(rf"^\s+{k}\s", t, re.M)) for k in ("mv", "block", "qp")}


def render(src, frames, n, mv=True, block=False, qp=False, out_dir=None):
    ff = find_ffmpeg()
    if not ff:
        raise RuntimeError(tr("err_noffmpeg"))
    out = Path(out_dir or ".") / f"block_{n}_{int(mv)}{int(block)}{int(qp)}.png"
    if out.exists():
        return out

    start = next((k for k in range(n, -1, -1) if frames[k][2]), 0)
    t0, t = frames[0][3], frames[start][3]
    seek = ["-ss", f"{max(0.0, t - (t0 or 0.0)):.6f}"] if t is not None and start > 0 else []

    attempts = [(mv, block, qp)]
    if block or qp:
        attempts.append((mv, False, False))
    if mv:
        attempts.append((False, False, False))
    err = ""
    for m, b, q in attempts:
        opts = [o for o, on in (("mv=pf+bf+bb", m), ("block=1", b), ("qp=1", q)) if on]
        vf = f"select=eq(n\\,{n - start})" + (",codecview=" + ":".join(opts) if opts else "")
        cmd = [ff, "-v", "error", "-y", "-flags2", "+export_mvs", "-export_side_data", "venc_params",
               *seek, "-i", str(src), "-vf", vf, "-frames:v", "1", "-fps_mode", "passthrough", str(out)]
        r = _run(cmd)
        if out.exists():
            return out
        err = err or r.stderr.strip()
    raise RuntimeError((err or tr("err_noout"))[-300:])
