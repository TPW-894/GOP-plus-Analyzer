# Copyright (C) 2026 TPW-894 / Licensed under GPL-3.0-or-later

import json, os, re, shutil, subprocess, sys
from pathlib import Path

from i18n import tr

BASE = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
NOWIN = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
DEC_OPTS = ["-flags2", "+export_mvs", "-export_side_data", "venc_params"]


def find_tool(name):
    exe = name + (".exe" if os.name == "nt" else "")
    for p in (BASE / exe, BASE / "ffmpeg" / "bin" / exe):
        if p.exists():
            return str(p)
    return shutil.which(name)


def find_ffmpeg():
    return find_tool("ffmpeg")


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", creationflags=NOWIN)


def capabilities(ff):
    r = _run([ff, "-hide_banner", "-h", "filter=codecview"])
    t = r.stdout + r.stderr
    return {k: bool(re.search(rf"^\s+{k}\s", t, re.M)) for k in ("mv", "block", "qp")}


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


def flags_key(mv, block, qp, only):
    return f"{int(mv)}{int(block)}{int(qp)}{int(only)}"


def overlay_filters(mv, block, qp, only):
    f = []
    if only:
        f.append("format=yuv420p,lutyuv=y=48:u=128:v=128")
    opts = [o for o, on in (("mv=pf+bf+bb", mv), ("block=1", block), ("qp=1", qp)) if on]
    if opts:
        f.append("codecview=" + ":".join(opts))
    return f


def attempts(mv, block, qp):
    a = [(mv, block, qp)]
    if block or qp:
        a.append((mv, False, False))
    if mv:
        a.append((False, False, False))
    return a


def seek_args(frames, n):
    start = next((k for k in range(n, -1, -1) if frames[k][2]), 0)
    t0, t = frames[0][3], frames[start][3]
    seek = ["-ss", f"{max(0.0, t - (t0 or 0.0)):.6f}"] if t is not None and start > 0 else []
    return start, seek


def cache_dir(out_dir, key):
    return Path(out_dir) / f"all_{key}"


def find_cached(out_dir, n, key, limit=None):
    if limit is None or n < limit:
        p = cache_dir(out_dir, key) / f"{n:06d}.jpg"
        if p.exists():
            return p
    p = Path(out_dir) / f"block_{n}_{key}.png"
    return p if p.exists() else None


def render(src, frames, n, mv=True, block=False, qp=False, only=False, out_dir=None):
    ff = find_ffmpeg()
    if not ff:
        raise RuntimeError(tr("err_noffmpeg"))
    out = Path(out_dir or ".") / f"block_{n}_{flags_key(mv, block, qp, only)}.png"
    if out.exists():
        return out
    start, seek = seek_args(frames, n)
    err = ""
    for m, b, q in attempts(mv, block, qp):
        vf = ",".join([f"select=eq(n\\,{n - start})", *overlay_filters(m, b, q, only)])
        cmd = [ff, "-v", "error", "-y", *DEC_OPTS, *seek, "-i", str(src), "-vf", vf,
               "-frames:v", "1", "-fps_mode", "passthrough", str(out)]
        r = _run(cmd)
        if out.exists():
            return out
        err = err or r.stderr.strip()
    raise RuntimeError((err or tr("err_noout"))[-300:])


def cache_commands(src, out_dir, mv, block, qp, only):
    ff = find_ffmpeg()
    if not ff:
        raise RuntimeError(tr("err_noffmpeg"))
    d = cache_dir(out_dir, flags_key(mv, block, qp, only))
    cmds = []
    for m, b, q in attempts(mv, block, qp):
        vf = ",".join([*overlay_filters(m, b, q, only), "format=yuvj420p"])
        cmds.append([ff, "-v", "error", "-y", *DEC_OPTS, "-i", str(src), "-vf", vf, "-fps_mode", "passthrough",
                     "-c:v", "mjpeg", "-q:v", "3", "-start_number", "0", "-progress", "pipe:1", "-nostats",
                     str(d / "%06d.jpg")])
    return d, cmds


def export_commands(src, frames, a, b, fps, out, mv, block, qp, only):
    ff = find_ffmpeg()
    if not ff:
        raise RuntimeError(tr("err_noffmpeg"))
    start, seek = seek_args(frames, a)
    cmds = []
    for m, bl, q in attempts(mv, block, qp):
        vf = ",".join([f"select=between(n\\,{a - start}\\,{b - start})", f"setpts=N/({fps:.6f}*TB)",
                       *overlay_filters(m, bl, q, only)])
        cmds.append([ff, "-v", "error", "-y", *DEC_OPTS, *seek, "-i", str(src), "-vf", vf, "-an",
                     "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", f"{fps:.6f}",
                     "-movflags", "+faststart", "-progress", "pipe:1", "-nostats", str(out)])
    return cmds
