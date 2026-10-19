# Copyright (C) 2026 TPW-894 / Licensed under GPL-3.0-or-later

import atexit, json, math, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QRectF, QPointF, QTimer
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPalette, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QHBoxLayout, QLabel,
                               QProgressBar, QPushButton, QSlider, QSplitter, QStyle, QVBoxLayout, QWidget)

import block_render
from i18n import LANG, settings, tr

TMP = Path(tempfile.mkdtemp(prefix="gop_plus_analyzer_"))
atexit.register(shutil.rmtree, TMP, ignore_errors=True)

BASE = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
COL = {"I": QColor("#e5484d"), "P": QColor("#3a6fe0"), "B": QColor("#9be564")}
OTHER = QColor("#888888")


QSS = """
QPushButton{background:palette(button);color:palette(buttontext);border:1px solid palette(mid);border-radius:0;padding:3px 10px;}
QPushButton:hover{background:palette(midlight);}
QPushButton:pressed{background:palette(mid);}
QPushButton#auto{padding:3px 0;}
QCheckBox::indicator{width:16px;height:16px;image:url(@OFF@);}
QCheckBox::indicator:checked{image:url(@ON@);}
QCheckBox::indicator:disabled{image:url(@OFFD@);}
QCheckBox::indicator:checked:disabled{image:url(@OND@);}
QSlider#mid{background:palette(base);}
QSlider#mid::groove:vertical{width:2px;background:palette(buttontext);}
QSlider#mid::handle:vertical{width:10px;height:6px;margin:0 -4px;background:palette(buttontext);}
QProgressBar{border:1px solid palette(mid);background:palette(base);text-align:center;height:14px;}
QProgressBar::chunk{background:palette(highlight);}
"""


def make_checks(fg, base, dis):
    out = {}
    for name, col, on in (("OFF", fg, False), ("ON", fg, True), ("OFFD", dis, False), ("OND", dis, True)):
        pm = QPixmap(16, 16)
        pm.fill(QColor(base))
        p = QPainter(pm)
        p.setPen(QPen(QColor(col), 1))
        p.drawRect(0, 0, 15, 15)
        if on:
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QPen(QColor(col), 2))
            p.drawPolyline(QPolygonF([QPointF(3.5, 8.5), QPointF(6.5, 11.5), QPointF(12.5, 4.5)]))
        p.end()
        f = TMP / f"chk_{name}_{col[1:]}.png"
        pm.save(str(f))
        out[name] = f.as_posix()
    return out


def apply_theme(app, dark):
    app.setStyle("Fusion")
    if dark:
        btn, win, fg, base, hi, hit, ph, dis = "#2f2f2f", "#232323", "#e6e6e6", "#191919", "#6a6a6a", "#ffffff", "#8c8c8c", "#6e6e6e"
    else:
        btn, win, fg, base, hi, hit, ph, dis = "#f7f7f7", "#ececec", "#1a1a1a", "#ffffff", "#b0b0b0", "#000000", "#777777", "#9a9a9a"
    pal = QPalette(QColor(btn), QColor(win))
    for role, col in ((QPalette.WindowText, fg), (QPalette.Base, base), (QPalette.AlternateBase, win),
                      (QPalette.Text, fg), (QPalette.ButtonText, fg), (QPalette.ToolTipBase, btn),
                      (QPalette.ToolTipText, fg), (QPalette.Highlight, hi), (QPalette.HighlightedText, hit),
                      (QPalette.PlaceholderText, ph)):
        pal.setColor(role, QColor(col))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        pal.setColor(QPalette.Disabled, role, QColor(dis))
    app.setPalette(pal)
    qss = QSS
    for k, v in make_checks(fg, base, dis).items():
        qss = qss.replace(f"@{k}@", v)
    app.setStyleSheet(qss)


def find_ffprobe():
    exe = "ffprobe.exe" if os.name == "nt" else "ffprobe"
    for p in (BASE / exe, BASE / "ffmpeg" / "bin" / exe):
        if p.exists():
            return str(p)
    return shutil.which("ffprobe")


def probe(ff, args):
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    r = subprocess.run([ff, "-v", "error", "-of", "json", *args], capture_output=True,
                       text=True, encoding="utf-8", creationflags=flags)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or tr("err_probe"))
    return json.loads(r.stdout)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def rate(s):
    try:
        a, b = s.split("/")
        return float(a) / float(b)
    except Exception:
        return 0.0


def analyze(src):
    src = Path(src)
    ff = find_ffprobe()
    if not ff:
        raise RuntimeError(tr("err_noprobe"))
    meta = probe(ff, ["-select_streams", "v:0", "-show_entries",
                      "stream=codec_name,profile,width,height,pix_fmt,r_frame_rate:format=duration",
                      "-i", str(src)])
    st = (meta.get("streams") or [{}])[0]
    raw = probe(ff, ["-select_streams", "v:0", "-show_entries",
                     "frame=pict_type,pts_time,pkt_dts_time,best_effort_timestamp_time,pkt_size,key_frame",
                     "-i", str(src)]).get("frames", [])
    if not raw:
        raise RuntimeError(tr("err_noframes"))
    rows = []
    for dec, f in enumerate(raw):
        t = next((num(f.get(k)) for k in ("best_effort_timestamp_time", "pts_time", "pkt_dts_time")
                  if num(f.get(k)) is not None), None)
        typ = f.get("pict_type", "?")
        key = int(f["key_frame"]) if "key_frame" in f else int(typ == "I")
        rows.append([typ, int(f.get("pkt_size") or 0), key, t, dec])
    order = sorted(range(len(rows)), key=lambda i: (rows[i][3] if rows[i][3] is not None else i, i))
    frames = [[*rows[i][:3], rows[i][3], rows[i][4], d] for d, i in enumerate(order)]
    data = {"info": {"file": src.name, "codec": st.get("codec_name"), "profile": st.get("profile"),
                     "width": st.get("width"), "height": st.get("height"), "pix_fmt": st.get("pix_fmt"),
                     "fps": rate(st.get("r_frame_rate", "")),
                     "duration": num(meta.get("format", {}).get("duration"))},
            "frames": frames}
    data["info"]["side"] = block_render.detect(src)
    (TMP / (src.stem + "_gop.json")).write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    return data


class Worker(QThread):
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            self.done.emit(analyze(self.path))
        except Exception as ex:
            self.failed.emit(str(ex))


def kb(n):
    return f"{n/1048576:.2f} MB" if n >= 1048576 else f"{n/1024:.1f} KB" if n >= 1024 else f"{n} B"


class Timeline(QWidget):
    info = Signal(str)
    selected = Signal(int, int, str)
    playToggle = Signal()
    LANE_Y, LANE_H, BAR_Y = 20, 22, 60

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(120)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.F, self.gi, self.gs = [], [], []
        self.maxS, self.ppf, self.off = 1, 8.0, 0.0
        self.sel = self.hov = -1
        self.scrub, self.pan_x = False, None
        self.gamma = 1.0
        self.range, self.d2i = None, {}

    def set_frames(self, frames, dec=False):
        self.F = sorted(frames, key=lambda f: f[4]) if dec else list(frames)
        self.gi, self.gs, g = [], [], -1
        for i, f in enumerate(self.F):
            if f[2] or i == 0:
                g += 1
                self.gs.append(i)
            self.gi.append(g)
        self.maxS = max([f[1] for f in self.F] + [1])
        self.d2i = {f[5]: i for i, f in enumerate(self.F)}
        self.sel = self.hov = -1
        self.fit()
        self.refresh_info()

    def set_range(self, r):
        self.range = r
        self.update()

    def set_gamma(self, g):
        self.gamma = g
        self.update()

    def mid(self):
        return int(self.maxS * 0.5 ** (1 / self.gamma))

    def auto_gamma(self):
        sz = sorted(f[1] for f in self.F if f[1] > 0)
        if not sz:
            return 1.0
        pr = sz[len(sz) // 2] / self.maxS
        return 1.0 if pr >= 0.5 else max(0.15, math.log(0.5) / math.log(pr))

    def min_ppf(self):
        return min(48.0, self.width() / max(1, len(self.F)))

    def fit(self):
        self.ppf, self.off = self.min_ppf(), 0.0
        self.update()

    def clamp(self):
        self.off = max(0.0, min(self.off, max(0.0, len(self.F) - self.width() / self.ppf)))

    def at(self, x):
        i = math.floor(self.off + x / self.ppf)
        return i if 0 <= i < len(self.F) else -1

    def detail(self, i):
        if i < 0:
            return tr("tl_hint")
        f, g = self.F[i], self.gi[i]
        gl = (self.gs[g + 1] if g + 1 < len(self.gs) else len(self.F)) - self.gs[g]
        t = f" / {f[3]:.3f} s" if f[3] is not None else ""
        return tr("detail", f[5], f[4], f[0], tr("keyframe") if f[2] else "", kb(f[1]), t,
                  g + 1, i - self.gs[g] + 1, gl)

    def refresh_info(self):
        self.info.emit(self.detail(self.hov if self.hov >= 0 else self.sel))

    def select(self, i, scroll=False):
        if i < 0:
            return
        self.sel = i
        if scroll:
            w = self.width() / self.ppf
            if i < self.off:
                self.off = i
            elif i >= self.off + w:
                self.off = i - w + 1
            self.clamp()
        self.refresh_info()
        self.update()
        f = self.F[i]
        self.selected.emit(f[5], f[4], f[0])

    def wheelEvent(self, e):
        x = e.position().x()
        fx = self.off + x / self.ppf
        self.ppf = max(self.min_ppf(), min(48.0, self.ppf * (1.25 if e.angleDelta().y() > 0 else 0.8)))
        self.off = fx - x / self.ppf
        self.clamp()
        self.update()

    def index_at(self, x):
        x = max(0.0, min(self.width() - 1.0, x))
        return max(0, min(len(self.F) - 1, math.floor(self.off + x / self.ppf)))

    def mousePressEvent(self, e):
        self.setFocus()
        if not self.F:
            return
        if e.button() == Qt.LeftButton:
            self.scrub = True
            self.select(self.index_at(e.position().x()))
        elif e.button() == Qt.MiddleButton:
            self.pan_x = e.position().x()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        x = e.position().x()
        if self.pan_x is not None:
            self.off -= (x - self.pan_x) / self.ppf
            self.pan_x = x
            self.clamp()
            self.update()
            return
        if self.scrub:
            i = self.index_at(x)
            if i != self.sel:
                self.select(i)
        i = self.at(x)
        if i != self.hov:
            self.hov = i
            self.refresh_info()
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.scrub = False
        elif e.button() == Qt.MiddleButton:
            self.pan_x = None
            self.unsetCursor()

    def leaveEvent(self, e):
        if self.hov >= 0:
            self.hov = -1
            self.refresh_info()
            self.update()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Left, Qt.Key_Right) and self.F:
            d = -1 if e.key() == Qt.Key_Left else 1
            cur = self.sel if self.sel >= 0 else math.floor(self.off)
            self.select(max(0, min(len(self.F) - 1, cur + d)), True)
        elif e.key() == Qt.Key_Space:
            self.playToggle.emit()
        else:
            super().keyPressEvent(e)

    def resizeEvent(self, e):
        if self.F:
            self.ppf = max(self.ppf, self.min_ppf())
            self.clamp()

    def paintEvent(self, e):
        p = QPainter(self)
        W, H = self.width(), self.height()
        fg = self.palette().color(QPalette.WindowText)
        mu, grid = QColor(fg), QColor(fg)
        mu.setAlpha(150)
        grid.setAlpha(60)
        F, ppf, off = self.F, self.ppf, self.off
        p.fillRect(self.rect(), self.palette().color(QPalette.Base))
        if not F:
            p.setPen(mu)
            p.drawText(self.rect(), Qt.AlignCenter, tr("drop_here"))
            return
        bh = max(16, H - self.BAR_Y - 22)
        p.setPen(mu)
        p.drawText(QPointF(0, self.LANE_Y - 6), tr("lane_type"))
        p.drawText(QPointF(0, self.BAR_Y - 6), tr("lane_size", kb(self.maxS), kb(self.mid())))

        if self.range:
            ia, ib = self.d2i.get(self.range[0]), self.d2i.get(self.range[1])
            if ia is not None and ib is not None:
                x0, x1 = (min(ia, ib) - off) * ppf, (max(ia, ib) + 1 - off) * ppf
                rc = QColor(fg)
                rc.setAlpha(120)
                p.fillRect(QRectF(x0, 0, max(x1 - x0, 2), 3), rc)

        if ppf >= 6:
            alt = QColor(fg)
            alt.setAlpha(16)
            for i in range(math.floor(off), min(len(F), math.ceil(off + W / ppf) + 1)):
                if i % 2:
                    p.fillRect(QRectF((i - off) * ppf, self.LANE_Y, ppf, self.BAR_Y + bh - self.LANE_Y), alt)

        def cell(a, b, x, w):
            t, m, k = F[a][0], 0, False
            for i in range(a, b):
                f = F[i]
                m = max(m, f[1])
                k = k or bool(f[2])
                if f[0] == "I":
                    t = "I"
                elif f[0] == "P" and t == "B":
                    t = "P"
            c = COL.get(t, OTHER)
            p.fillRect(QRectF(x, self.LANE_Y, w, self.LANE_H), c)
            h = (m / self.maxS) ** self.gamma * bh
            p.fillRect(QRectF(x, self.BAR_Y + bh - h, w, max(h, 1)), c)
            if k and ppf >= 3:
                kc = QColor(COL["I"])
                kc.setAlpha(90)
                p.fillRect(QRectF(x, self.BAR_Y, 1, bh), kc)

        if ppf >= 2:
            i0, i1 = math.floor(off), min(len(F), math.ceil(off + W / ppf) + 1)
            w = max(1.0, ppf - (1 if ppf >= 4 else 0))
            for i in range(i0, i1):
                cell(i, i + 1, (i - off) * ppf, w)
        else:
            for x in range(W):
                a = math.floor(off + x / ppf)
                if a >= len(F):
                    break
                cell(a, min(len(F), max(a + 1, math.floor(off + (x + 1) / ppf))), x, 1)

        raw = 90 / ppf
        pw = 10 ** math.floor(math.log10(raw))
        step = next(m * pw for m in (1, 2, 5, 10) if m * pw >= raw)
        p.setPen(grid)
        p.drawLine(0, H - 18, W, H - 18)
        i = math.ceil(off / step) * step
        while (i - off) * ppf < W:
            x = (i - off) * ppf
            p.setPen(grid)
            p.drawLine(QPointF(x, H - 18), QPointF(x, H - 14))
            fr = F[int(i)] if int(i) < len(F) else None
            tt = f" ({fr[3]:.2f}s)" if fr and fr[3] is not None else ""
            p.setPen(mu)
            p.drawText(QPointF(x + 3, H - 3), f"#{int(i)}{tt}")
            i += step

        for idx, c in ((self.hov, mu), (self.sel, fg)):
            if idx < 0:
                continue
            x = (idx - off) * ppf
            p.setPen(QPen(c, 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(x, self.LANE_Y - 1, max(ppf, 2), self.LANE_H + 2))
            p.drawLine(QPointF(x + .5, self.BAR_Y), QPointF(x + .5, self.BAR_Y + bh))


class ImageView(QWidget):

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(200)
        self.pix, self.msg, self.s, self.o, self.d = None, "", 1.0, QPointF(0, 0), None
        self.show_msg(tr("iv_hint"))

    def show_msg(self, m):
        self.pix, self.msg = None, m
        self.update()

    def set_image(self, path):
        pix = QPixmap(str(path))
        same = self.pix is not None and pix.size() == self.pix.size()
        self.pix = pix
        if not same:
            self.fit()
        self.update()

    def fit(self):
        if not self.pix:
            return
        self.s = min(self.width() / self.pix.width(), self.height() / self.pix.height())
        self.o = QPointF((self.width() - self.pix.width() * self.s) / 2,
                         (self.height() - self.pix.height() * self.s) / 2)
        self.update()

    def wheelEvent(self, e):
        if not self.pix:
            return
        pos = e.position()
        ns = max(0.05, min(32.0, self.s * (1.25 if e.angleDelta().y() > 0 else 0.8)))
        self.o = pos - (pos - self.o) * (ns / self.s)
        self.s = ns
        self.update()

    def mousePressEvent(self, e):
        self.d = (e.position(), QPointF(self.o))

    def mouseMoveEvent(self, e):
        if self.d and self.pix:
            self.o = self.d[1] + (e.position() - self.d[0])
            self.update()

    def mouseReleaseEvent(self, e):
        self.d = None

    def mouseDoubleClickEvent(self, e):
        self.fit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), self.palette().color(QPalette.Base))
        if not self.pix:
            c = self.palette().color(QPalette.WindowText)
            c.setAlpha(150)
            p.setPen(c)
            p.drawText(self.rect(), Qt.AlignCenter, self.msg)
            return
        p.setRenderHint(QPainter.SmoothPixmapTransform, self.s < 1)
        p.translate(self.o)
        p.scale(self.s, self.s)
        p.drawPixmap(0, 0, self.pix)


class JumpSlider(QSlider):
    HANDLE_H = 6

    def _jump(self, e):
        span = max(1, self.height() - self.HANDLE_H)
        pos = max(0, min(span, round(e.position().y() - self.HANDLE_H / 2)))
        self.setValue(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos, span, True))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.setSliderDown(True)
            self._jump(e)

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self._jump(e)

    def mouseReleaseEvent(self, e):
        self.setSliderDown(False)


class QpBar(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(120, 10)

    def paintEvent(self, e):
        g = QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0, QColor.fromHslF(113 / 360, 0.6, 0.5))
        g.setColorAt(0.5, QColor("#a8a8a8"))
        g.setColorAt(1, QColor.fromHslF(293 / 360, 0.6, 0.6))
        QPainter(self).fillRect(self.rect(), g)


class BlockWorker(QThread):
    done = Signal(str)
    failed = Signal(str)

    def __init__(self, *a, **k):
        super().__init__()
        self.a, self.k = a, k

    def run(self):
        try:
            self.done.emit(str(block_render.render(*self.a, **self.k)))
        except Exception as ex:
            self.failed.emit(str(ex))


class Job(QThread):
    progress = Signal(int)
    done = Signal(bool)
    failed = Signal(str)

    def __init__(self, cmds):
        super().__init__()
        self.cmds, self.proc, self.stop, self.count = cmds, None, False, 0

    def cancel(self):
        self.stop = True
        p = self.proc
        if p and p.poll() is None:
            p.terminate()

    def run(self):
        err = ""
        for cmd in self.cmds:
            if self.stop:
                break
            self.count = 0
            try:
                self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                             encoding="utf-8", errors="replace", creationflags=block_render.NOWIN)
            except Exception as ex:
                self.failed.emit(str(ex))
                return
            msgs = []
            for line in self.proc.stdout:
                line = line.strip()
                if line.startswith("frame=") and line[6:].strip().isdigit():
                    self.count = int(line[6:])
                    self.progress.emit(self.count)
                elif line and not re.match(r"^\w+=\S*$", line):
                    msgs.append(line)
            rc = self.proc.wait()
            if self.stop:
                break
            if rc == 0 and self.count > 0:
                self.done.emit(True)
                return
            err = err or "\n".join(msgs[-3:])
        if self.stop:
            self.done.emit(False)
        else:
            self.failed.emit(err or tr("err_noout"))


class Main(QWidget):
    def __init__(self, dark=True):
        super().__init__()
        self.setWindowTitle("GOP+ Analyzer")
        self.resize(1100, 880)
        self.setAcceptDrops(True)
        self.data = None
        self.worker = None
        self.job, self.complete, self.partial, self.range = None, set(), {}, None
        self.playing, self.p_t0, self.p_n0, self.p_last, self.p_fps = False, 0.0, 0, 0, 30.0
        self.pt = QTimer(self)
        self.pt.setInterval(15)
        self.pt.timeout.connect(self.play_tick)

        self.title = QLabel(tr("title_hint"))
        f = self.title.font()
        f.setPointSize(f.pointSize() + 3)
        f.setBold(True)
        self.title.setFont(f)
        self.meta = QLabel("")
        self.stats = QLabel("")
        self.stats.setWordWrap(True)
        self.tl = Timeline()
        self.detail = QLabel("")
        self.tl.info.connect(self.detail.setText)

        legend = QLabel(" ".join(f"<span style='color:{COL[k].name()}'>■</span> {k}" for k in "IPB"))
        self.dec = QCheckBox(tr("dec_order"))
        self.dec.toggled.connect(lambda _: self.data and self.tl.set_frames(self.data["frames"], self.dec.isChecked()))
        b_open, b_fit, b_save = QPushButton(tr("open")), QPushButton(tr("fit")), QPushButton(tr("save_json"))
        b_open.clicked.connect(self.open_dialog)
        b_fit.clicked.connect(self.tl.fit)
        b_save.clicked.connect(self.save_json)
        self.dk = QCheckBox(tr("dark"))
        self.dk.setChecked(dark)
        self.dk.toggled.connect(self.set_dark)
        b_lang = QPushButton(tr("lang_btn"))
        b_lang.clicked.connect(self.switch_lang)
        hint = QLabel(tr("hint"))
        hint.setEnabled(False)

        bar = QHBoxLayout()
        for w in (b_open, legend, self.dec, b_fit, b_save, self.dk, b_lang):
            bar.addWidget(w)
        bar.addStretch()
        lay = QVBoxLayout(self)
        for w in (self.title, self.meta, self.stats):
            lay.addWidget(w)
        lay.addLayout(bar)

        self.src, self.busy, self.pending, self._keep = None, False, False, []
        self.prev, self.drawn = -1, -1
        self.vid, self.outdir = 0, TMP
        self.rt = QTimer(self)
        self.rt.setInterval(60)
        self.rt.timeout.connect(self.tick)
        self.iv = ImageView()
        ff = block_render.find_ffmpeg()
        caps = block_render.capabilities(ff) if ff else {}
        self.ov = {k: QCheckBox(t) for k, t in (("mv", tr("mv")), ("block", tr("block")), ("qp", "QP"))}
        self.ov["mv"].setChecked(True)
        ovbar = QHBoxLayout()
        ovbar.addWidget(QLabel(tr("overlay")))
        for k, c in self.ov.items():
            if not caps.get(k):
                c.setEnabled(False)
                c.setChecked(False)
                c.setToolTip(tr("cap_no") if ff else tr("ffmpeg_missing"))
            c.toggled.connect(self.on_flags)
            ovbar.addWidget(c)
        self.only = QCheckBox(tr("only"))
        self.only.setToolTip(tr("only_tip"))
        self.only.toggled.connect(self.on_flags)
        ovbar.addWidget(self.only)
        b_reset = QPushButton(tr("fit_img"))
        b_reset.clicked.connect(self.iv.fit)
        self.bstat = QLabel("")
        ovbar.addWidget(b_reset)
        self.note = QLabel("")
        ovbar.addWidget(self.note)
        ovbar.addWidget(self.bstat, 1)
        self.qpleg = QWidget()
        ll = QHBoxLayout(self.qpleg)
        ll.setContentsMargins(0, 0, 0, 0)
        for w in (QLabel(tr("qp_low")), QpBar(), QLabel(tr("qp_high"))):
            ll.addWidget(w)
        self.qpleg.setVisible(False)
        self.ov["qp"].toggled.connect(lambda on: self.qpleg.setVisible(on and self.ov["qp"].isEnabled()))
        ovbar.addWidget(self.qpleg)
        self.tl.selected.connect(self.on_selected)

        sp = QSplitter(Qt.Vertical)
        sp.setChildrenCollapsible(False)
        self.gsl = JumpSlider(Qt.Vertical)
        self.gsl.setRange(0, 100)
        self.gsl.setMinimumHeight(30)
        self.gsl.setToolTip(tr("gsl_tip"))
        self.gsl.valueChanged.connect(self.on_gamma)
        sw = 27 if LANG == "ja" else 36
        b_mid = QPushButton(tr("auto"))
        b_mid.setToolTip(tr("auto_tip"))
        b_mid.setObjectName("auto")
        b_mid.setFixedWidth(sw)
        b_mid.clicked.connect(self.auto_mid)
        self.gsl.setObjectName("mid")
        self.gsl.setFixedWidth(sw)
        sidew = QWidget()
        sidew.setFixedWidth(sw)
        side = QVBoxLayout(sidew)
        side.setContentsMargins(0, 0, 0, 0)
        side.setSpacing(2)
        side.addWidget(b_mid)
        side.addWidget(self.gsl, 1, Qt.AlignHCenter)
        box = QWidget()
        hl = QHBoxLayout(box)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.tl, 1)
        hl.addWidget(sidew)
        sp.addWidget(box)
        sp.addWidget(self.iv)
        sp.setSizes([300, 520])
        lay.addWidget(sp, 1)
        lay.addLayout(ovbar)

        self.b_cache = QPushButton(tr("cache_btn"))
        self.b_cache.setToolTip(tr("cache_tip"))
        self.b_cache.clicked.connect(self.start_cache)
        self.b_play = QPushButton(tr("play"))
        self.b_play.setToolTip(tr("play_tip"))
        self.b_play.clicked.connect(self.toggle_play)
        b_in, b_out, b_all = QPushButton(tr("range_in")), QPushButton(tr("range_out")), QPushButton(tr("range_all"))
        for b in (b_in, b_out, b_all):
            b.setToolTip(tr("range_tip"))
        b_in.clicked.connect(lambda: self.set_range(0))
        b_out.clicked.connect(lambda: self.set_range(1))
        b_all.clicked.connect(self.reset_range)
        self.rlabel = QLabel(tr("range_whole"))
        self.b_export = QPushButton(tr("export"))
        self.b_export.setToolTip(tr("export_tip"))
        self.b_export.clicked.connect(self.start_export)
        self.pstat = QLabel("")
        self.pbar = QProgressBar()
        self.pbar.setMinimumWidth(160)
        self.b_cancel = QPushButton(tr("cancel"))
        self.b_cancel.clicked.connect(self.cancel_job)
        self.pbar.setVisible(False)
        self.b_cancel.setVisible(False)
        actbar = QHBoxLayout()
        for w in (self.b_cache, self.b_play, b_in, b_out, b_all, self.rlabel, self.b_export):
            actbar.addWidget(w)
        actbar.addStretch()
        for w in (self.pstat, self.pbar, self.b_cancel):
            actbar.addWidget(w)
        lay.addLayout(actbar)
        self.tl.playToggle.connect(self.toggle_play)
        self.update_buttons()

        foot = QHBoxLayout()
        foot.addWidget(self.detail, 1)
        foot.addWidget(hint)
        lay.addLayout(foot)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if urls:
            self.start(urls[0])

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("open_title"), "", tr("video_filter"))
        if path:
            self.start(path)

    def start(self, path):
        if self.worker and self.worker.isRunning():
            return
        self.title.setText(Path(path).name)
        self.src = path
        self.vid += 1
        self.outdir = TMP / f"v{self.vid}"
        self.outdir.mkdir(exist_ok=True)
        self.data, self.pending, self.prev, self.drawn = None, False, -1, -1
        self.stop_play()
        self.cancel_job()
        self.complete, self.partial, self.range = set(), {}, None
        self.tl.set_frames([])
        self.update_range()
        self.pstat.setText("")
        self.update_buttons()
        self.iv.show_msg(tr("iv_hint"))
        self.meta.setText("")
        self.stats.setText("")
        self.detail.setText(tr("analyzing"))
        QApplication.setOverrideCursor(Qt.BusyCursor)
        self.worker = Worker(path)
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_failed(self, msg):
        QApplication.restoreOverrideCursor()
        self.detail.setText(tr("error") + msg)

    def on_done(self, d):
        QApplication.restoreOverrideCursor()
        self.data = d
        i = d["info"]
        self.meta.setText(" / ".join(str(x) for x in (
            i["codec"], i["profile"], i["width"] and f"{i['width']}×{i['height']}", i["pix_fmt"],
            i["fps"] and f"{i['fps']:.3f} fps") if x))
        self.tl.set_frames(d["frames"], self.dec.isChecked())
        self.show_stats()
        self.auto_mid()
        side, miss = i.get("side"), []
        if side is not None:
            if not side["mv"]:
                miss.append(tr("mv"))
            if not side["venc"]:
                miss.append(tr("block_qp"))
        self.note.setText(tr("note", i["codec"], tr("sep").join(miss)) if miss else "")
        self.update_buttons()

    def show_stats(self):
        F, gs = self.tl.F, self.tl.gs
        c, s = {}, {}
        for f in F:
            c[f[0]] = c.get(f[0], 0) + 1
            s[f[0]] = s.get(f[0], 0) + f[1]
        L = [(gs[k + 1] if k + 1 < len(gs) else len(F)) - a for k, a in enumerate(gs)]
        fps, dur = self.data["info"]["fps"], self.data["info"]["duration"]
        dur = dur or (len(F) / fps if fps else 0)
        avg = lambda t: kb(round(s[t] / c[t])) if t in c else "-"
        items = [(tr("st_frames"), len(F)), (tr("st_gops"), len(gs)),
                 (tr("st_goplen"), f"{len(F) / len(gs):.1f} / {max(L)} / {min(L)}"),
                 (tr("st_ipb"), f"{c.get('I', 0)} / {c.get('P', 0)} / {c.get('B', 0)}"),
                 (tr("st_avg"), f"{avg('I')} / {avg('P')} / {avg('B')}"),
                 (tr("st_br"), f"{sum(f[1] for f in F) * 8 / dur / 1e6:.2f} Mbps" if dur else "-")]
        self.stats.setText("　　".join(f"<span style='color:gray'>{k}</span> <b>{v}</b>" for k, v in items))

    def flags(self):
        o = {k: c.isChecked() and c.isEnabled() for k, c in self.ov.items()}
        return o["mv"], o["block"], o["qp"], self.only.isChecked()

    def lookup(self, n):
        key = block_render.flags_key(*self.flags())
        limit = None if key in self.complete else self.partial.get(key, 0)
        return block_render.find_cached(self.outdir, n, key, limit)

    def cur_disp(self):
        return self.tl.F[self.tl.sel][5] if 0 <= self.tl.sel < len(self.tl.F) else None

    def on_flags(self, *_):
        self.stop_play()
        self.update_buttons()
        self.render_block()

    def render_block(self):
        n = self.cur_disp()
        if not (self.data and self.src and n is not None):
            return
        hit = self.lookup(n)
        if hit:
            self.drawn = self.tl.sel
            self.bstat.setText("")
            self.iv.set_image(hit)
            return
        if self.busy:
            return
        self.drawn = self.tl.sel
        self.busy = True
        QTimer.singleShot(200, lambda: self.bstat.setText(tr("rendering", n)) if self.busy else None)
        opts = dict(zip(("mv", "block", "qp", "only"), self.flags()))
        w = BlockWorker(self.src, self.data["frames"], n, out_dir=self.outdir, **opts)
        self._keep.append(w)
        g = self.vid
        w.done.connect(lambda path: self.on_block(path, g, n))
        w.failed.connect(lambda m: self.on_block_fail(m, g, n))
        w.start()

    def on_block(self, path, g=None, n=None):
        self.busy = False
        if g != self.vid:
            return
        self.bstat.setText("")
        cur = self.cur_disp()
        if cur is None:
            return
        if cur != n:
            self.render_block()
        else:
            self.iv.set_image(path)

    def on_block_fail(self, msg, g=None, n=None):
        self.busy = False
        if g != self.vid:
            return
        self.bstat.setText(tr("render_err") + (msg.strip().splitlines() or [""])[-1])
        if self.cur_disp() not in (None, n):
            self.render_block()

    def update_buttons(self):
        has = bool(self.data and self.src)
        idle = self.job is None
        key = block_render.flags_key(*self.flags())
        self.b_cache.setEnabled(has and idle)
        self.b_export.setEnabled(has and idle)
        self.b_play.setEnabled(self.playing or (has and idle and key in self.complete))

    def set_range(self, which):
        n = self.cur_disp()
        if not self.data or n is None:
            return
        a, b = self.range or (0, len(self.data["frames"]) - 1)
        a, b = (n, max(b, n)) if which == 0 else (min(a, n), n)
        self.range = (a, b)
        self.update_range()

    def reset_range(self):
        self.range = None
        self.update_range()

    def update_range(self):
        self.tl.set_range(self.range)
        r = self.range
        self.rlabel.setText(tr("range_label", r[0], r[1], r[1] - r[0] + 1) if r else tr("range_whole"))

    def begin_job(self, job, total, kind, out=None):
        self.job = job
        g = self.vid
        key = block_render.flags_key(*self.flags())
        name = "caching" if kind == "cache" else "exporting"
        self.pbar.setRange(0, max(1, total))
        self.pbar.setValue(0)
        self.pbar.setVisible(True)
        self.b_cancel.setVisible(True)
        self.pstat.setText(tr(name, 0, total))

        def on_progress(c):
            if g != self.vid:
                return
            self.pbar.setValue(min(c, total))
            self.pstat.setText(tr(name, c, total))
            if kind == "cache":
                self.partial[key] = max(0, c - 2)

        def finish():
            if self.job is job:
                self.job = None
                self.pbar.setVisible(False)
                self.b_cancel.setVisible(False)
            self.update_buttons()

        def on_done(ok):
            finish()
            if g != self.vid:
                return
            if kind == "cache":
                if ok:
                    self.complete.add(key)
                    self.partial.pop(key, None)
                    self.pstat.setText(tr("cache_done"))
                else:
                    keep = max(0, job.count - 2)
                    for p in block_render.cache_dir(self.outdir, key).glob("*.jpg"):
                        if int(p.stem) >= keep:
                            p.unlink(missing_ok=True)
                    self.partial[key] = keep
                    self.pstat.setText(tr("canceled"))
            elif ok:
                self.pstat.setText(tr("export_done", out))
            else:
                Path(out).unlink(missing_ok=True)
                self.pstat.setText(tr("canceled"))
            self.update_buttons()

        def on_failed(msg):
            finish()
            if g != self.vid:
                return
            if kind == "export" and out:
                Path(out).unlink(missing_ok=True)
            self.pstat.setText(tr("job_err") + (msg.strip().splitlines() or [""])[-1])

        job.progress.connect(on_progress)
        job.done.connect(on_done)
        job.failed.connect(on_failed)
        self._keep.append(job)
        self.update_buttons()
        job.start()

    def cancel_job(self):
        if self.job:
            self.job.cancel()

    def start_cache(self):
        if self.job or not (self.data and self.src):
            return
        fl = self.flags()
        key = block_render.flags_key(*fl)
        try:
            d, cmds = block_render.cache_commands(self.src, self.outdir, *fl)
        except Exception as ex:
            self.pstat.setText(tr("job_err") + str(ex))
            return
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)
        self.complete.discard(key)
        self.partial[key] = 0
        self.begin_job(Job(cmds), len(self.data["frames"]), "cache")

    def start_export(self):
        if self.job or not (self.data and self.src):
            return
        frames = self.data["frames"]
        a, b = self.range or (0, len(frames) - 1)
        default = str(Path(self.src).with_name(Path(self.src).stem + "_overlay.mp4"))
        path, _ = QFileDialog.getSaveFileName(self, tr("export_title"), default, tr("export_filter"))
        if not path:
            return
        fps = self.data["info"]["fps"] or 30.0
        try:
            cmds = block_render.export_commands(self.src, frames, a, b, fps, path, *self.flags())
        except Exception as ex:
            self.pstat.setText(tr("job_err") + str(ex))
            return
        self.begin_job(Job(cmds), b - a + 1, "export", path)

    def toggle_play(self):
        if self.playing:
            self.stop_play()
            return
        key = block_render.flags_key(*self.flags())
        if self.job or key not in self.complete or not self.tl.F:
            return
        n0 = self.cur_disp() or 0
        if self.dec.isChecked():
            self.dec.setChecked(False)
        if n0 >= len(self.tl.F) - 1:
            n0 = 0
        self.playing = True
        self.p_n0, self.p_last = n0, n0
        self.p_fps = self.data["info"]["fps"] or 30.0
        self.p_t0 = time.perf_counter()
        self.b_play.setText(tr("stop"))
        self.pt.start()

    def stop_play(self):
        if self.playing:
            self.playing = False
            self.pt.stop()
            self.b_play.setText(tr("play"))
            self.update_buttons()

    def play_tick(self):
        last = len(self.tl.F) - 1
        n = self.p_n0 + int((time.perf_counter() - self.p_t0) * self.p_fps)
        end = n >= last
        n = min(n, last)
        if n != self.p_last:
            self.p_last = n
            self.tl.select(n, True)
            hit = self.lookup(self.tl.F[n][5])
            if hit:
                self.iv.set_image(hit)
        if end:
            self.stop_play()

    MAX_SWITCH = 3

    def on_selected(self, *_):
        if self.playing:
            if self.tl.sel == self.p_last:
                return
            self.stop_play()
        if not self.rt.isActive():
            self.rt.start()

    def tick(self):
        cur = self.tl.sel
        d = abs(cur - self.prev)
        self.prev = cur
        if d <= self.MAX_SWITCH and cur != self.drawn:
            self.render_block()
        elif d == 0:
            self.rt.stop()

    def on_gamma(self, v):
        self.tl.set_gamma(1 - 0.85 * v / 100)

    def auto_mid(self):
        v = round((1 - self.tl.auto_gamma()) / 0.85 * 100)
        if self.gsl.value() == v:
            self.on_gamma(v)
        else:
            self.gsl.setValue(v)

    def set_dark(self, on):
        apply_theme(QApplication.instance(), on)
        settings().setValue("dark", on)

    def switch_lang(self):
        settings().setValue("lang", "en" if LANG == "ja" else "ja")
        self.detail.setText(tr("restart"))

    def save_json(self):
        if not self.data:
            return
        name = Path(self.data["info"]["file"]).stem + "_gop.json"
        path, _ = QFileDialog.getSaveFileName(self, tr("save_json_t"), name, "JSON (*.json)")
        if path:
            shutil.copy(TMP / name, path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("GOP+ Analyzer")
    dark = settings().value("dark", True, type=bool)
    apply_theme(app, dark)
    w = Main(dark)
    w.show()
    if len(sys.argv) > 1:
        w.start(sys.argv[1])
    sys.exit(app.exec())
