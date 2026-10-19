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
    "only": ("オーバーレイのみ", "Overlay only"),
    "only_tip": ("動画の画像を使わず、オーバーレイだけを暗い背景に描画します", "Draw only the overlay on a dark background, without the video image"),
    "cache_btn": ("キャッシュ生成", "Build cache"),
    "cache_tip": ("現在のオーバーレイ設定で全フレームを描画して保存します (再生に必要)", "Render all frames with the current overlay settings (required for playback)"),
    "play": ("▶ 再生", "▶ Play"),
    "stop": ("■ 停止", "■ Stop"),
    "play_tip": ("全フレームのキャッシュ生成が終わると再生できます (Space)", "Available after the full cache is built (Space)"),
    "range_in": ("開始点", "Set in"),
    "range_out": ("終了点", "Set out"),
    "range_all": ("全体", "All"),
    "range_tip": ("書き出す範囲を、選択中のフレームで指定します", "Set the export range using the selected frame"),
    "range_whole": ("範囲: 全体", "Range: all"),
    "range_label": ("範囲: {0} – {1} ({2}フレーム)", "Range: {0} – {1} ({2} frames)"),
    "export": ("動画を書き出し...", "Export video..."),
    "export_tip": ("現在のオーバーレイ設定で、指定した範囲をMP4に書き出します (音声なし)", "Export the range to MP4 with the current overlay settings (no audio)"),
    "export_title": ("動画を書き出し", "Export video"),
    "export_filter": ("MP4 動画 (*.mp4)", "MP4 video (*.mp4)"),
    "cancel": ("キャンセル", "Cancel"),
    "caching": ("キャッシュ生成中 {0}/{1}", "Building cache {0}/{1}"),
    "exporting": ("書き出し中 {0}/{1}", "Exporting {0}/{1}"),
    "cache_done": ("キャッシュ生成が完了しました", "Cache complete"),
    "export_done": ("書き出しが完了しました: {0}", "Export complete: {0}"),
    "canceled": ("キャンセルしました", "Canceled"),
    "job_err": ("処理エラー: ", "Error: "),
    "lang_btn": ("English", "日本語"),
    "restart": ("言語を変更しました。再起動すると反映されます。", "Language changed. Restart to apply."),
}


def tr(key, *a):
    s = S[key][0 if LANG == "ja" else 1]
    return s.format(*a) if a else s
