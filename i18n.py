# Copyright (C) 2026 TPW-894 / Licensed under GPL-3.0-or-later

from PySide6.QtCore import QLocale, QSettings


def settings():
    return QSettings("TPW-894", "GOP-Plus-Analyzer")


def _detect():
    v = settings().value("lang", "")
    if v in ("ja", "en"):
        return v
    return "ja" if QLocale.system().language() == QLocale.Language.Japanese else "en"


LANG = _detect()

S = {
    "err_probe": ("ffprobe の実行に失敗しました", "ffprobe failed to run"),
    "err_noprobe": ("ffprobe が見つかりません。PATHに追加するか、このアプリと同じフォルダに置いてください。",
                    "ffprobe was not found. Add it to PATH or place it in the same folder as this app."),
    "err_noffmpeg": ("ffmpeg が見つかりません。PATHに追加するか、このアプリと同じフォルダに置いてください。",
                     "ffmpeg was not found. Add it to PATH or place it in the same folder as this app."),
    "err_noframes": ("映像フレームを取得できませんでした。動画ファイルではない可能性があります。",
                     "Could not read any video frames. The file may not be a video."),
    "err_noout": ("フレームを出力できませんでした", "Could not output the frame"),
    "tl_hint": ("フレームにカーソルを合わせると詳細を表示します。クリックで選択します。",
                "Hover over a frame for details. Click to select."),
    "keyframe": ("（キーフレーム）", " (keyframe)"),
    "detail": ("表示順 #{0} / デコード順 #{1} / {2}{3} / {4}{5} / GOP {6}（{7}/{8}）",
               "Display #{0} / Decode #{1} / {2}{3} / {4}{5} / GOP {6} ({7}/{8})"),
    "drop_here": ("動画ファイルをここにドロップ", "Drop a video file here"),
    "lane_type": ("フレーム種別", "Frame type"),
    "lane_size": ("サイズ（最大 {0} / 高さ50% = {1}）", "Size (max {0} / 50% height = {1})"),
    "iv_hint": ("フレームをクリックすると、ブロック情報をオーバーレイした画像を表示します",
                "Click a frame to show it with block information overlaid"),
    "title_hint": ("動画ファイルをウィンドウにドロップしてください", "Drop a video file onto this window"),
    "dec_order": ("デコード順で表示", "Show in decode order"),
    "open": ("開く...", "Open..."),
    "fit": ("全体表示", "Fit all"),
    "save_json": ("JSONを保存...", "Save JSON..."),
    "save_json_t": ("JSONを保存", "Save JSON"),
    "dark": ("ダークモード", "Dark mode"),
    "hint": ("ホイール: 拡大縮小 / 左ドラッグ: フレーム選択 / 中ボタンドラッグ: 移動 / ←→: 1フレーム",
             "Wheel: zoom / Left-drag: select frames / Middle-drag: pan / ←→: 1 frame"),
    "mv": ("動きベクトル", "Motion vectors"),
    "block": ("ブロック分割", "Block partitions"),
    "block_qp": ("ブロック分割/QP", "block partitions / QP"),
    "overlay": ("オーバーレイ:", "Overlay:"),
    "cap_no": ("このffmpegは未対応です", "Not supported by this ffmpeg"),
    "ffmpeg_missing": ("ffmpeg が見つかりません", "ffmpeg not found"),
    "fit_img": ("画像を全体表示", "Fit image"),
    "qp_low": ("QP 低", "QP low"),
    "qp_high": ("高", "high"),
    "gsl_tip": ("サイズ棒グラフの中間点。上げるほど、小さいサイズが大きく表示されます",
                "Midpoint of the size bars. Raising it makes small sizes appear larger"),
    "auto": ("自動", "Auto"),
    "auto_tip": ("中間点を自動設定（中央値のサイズが高さ50%になる位置）",
                 "Set the midpoint automatically (median size at 50% height)"),
    "open_title": ("動画を開く", "Open video"),
    "video_filter": ("動画 (*.*)", "Video (*.*)"),
    "analyzing": ("解析中...", "Analyzing..."),
    "error": ("エラー: ", "Error: "),
    "note": ("※ {0} では {1} を取得できない可能性があります", "* {0} may not provide: {1}"),
    "sep": ("・", ", "),
    "st_frames": ("フレーム数", "Frames"),
    "st_gops": ("GOP数", "GOPs"),
    "st_goplen": ("GOP長 平均/最大/最小", "GOP length avg/max/min"),
    "st_ipb": ("I/P/B", "I/P/B"),
    "st_avg": ("平均サイズ I/P/B", "Avg size I/P/B"),
    "st_br": ("平均ビットレート", "Avg bitrate"),
    "rendering": ("フレーム #{0} を描画中...", "Rendering frame #{0}..."),
    "render_err": ("ブロック描画エラー: ", "Render error: "),
    "lang_btn": ("English", "日本語"),
    "restart": ("言語を変更しました。再起動すると反映されます。", "Language changed. Restart to apply."),
}


def tr(key, *a):
    s = S[key][0 if LANG == "ja" else 1]
    return s.format(*a) if a else s
