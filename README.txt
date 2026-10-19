GOP+ Analyzer
Copyright (C) 2026 TPW-894
Licensed under GPL-3.0-or-later (see LICENSE)

Source code / ソースコード : https://github.com/TPW-894/GOP-plus-Analyzer
BOOTH                      : https://tpw-894.booth.pm


==============================================================
日本語
==============================================================

■ 概要
動画ファイルのフレーム構造を調べて表示するツールです。

  - GOPタイムライン: I / P / B フレームを色分けして並べ、フレームごとのサイズを棒グラフで表示
  - GOPの統計: フレーム数、GOP数、GOP長(平均/最大/最小)、種別ごとの平均サイズ、平均ビットレート
  - ブロック情報のオーバーレイ表示: 選択したフレームに 動きベクトル / ブロック分割 / QP をオーバーレイで表示
  - オーバーレイのみの表示、全フレームのキャッシュ生成と連続再生
  - 範囲を指定した、オーバーレイ付き動画 (MP4) の書き出し
  - ダークモード、日本語/English 表示

■ 動作環境
  - Windows 10 / 11 (64bit)
  - インストール不要。このフォルダごと好きな場所に置いて、"GOP+ Analyzer.exe" を起動してください。
  - FFmpeg (ffmpeg.exe / ffprobe.exe) は同梱しています。

■ ソースから実行する場合 (GitHub版)
  GitHubにはソースコードのみ置いています。exe、FFmpeg、licenses フォルダは、BOOTHの配布パッケージに含まれます。
  1. Python 3 をインストールし、 pip install -r requirements.txt を実行します。
  2. ffmpeg / ffprobe を PATH に追加するか、gop_plus_analyzer.py と同じフォルダに置きます。
  3. python gop_plus_analyzer.py を実行します。(動画ファイルを引数に渡すと、起動と同時に開きます)

■ 使い方
  1. "GOP+ Analyzer.exe" を起動し、動画ファイルをウィンドウにドロップするか、「開く...」ボタンから選択します。
  2. 解析が終わると、タイムラインに全フレームが表示されます。
  3. タイムライン上でフレームをクリックすると、そのフレームの画像と、ブロック情報がオーバーレイで表示されます。
  4. 「キャッシュ生成」で全フレームを描画しておくと、「再生」で連続再生できます。
  5. 「開始点」「終了点」で範囲を決め、「動画を書き出し...」でオーバーレイ付きのMP4を保存できます。

■ 操作
  タイムライン
    マウスホイール        拡大 / 縮小
    左ボタンでドラッグ    フレームを選択 (カーソルに追従)
    中ボタンでドラッグ    表示位置の移動
    ← / →               選択フレームを1つずつ移動
    右側のスライダー      サイズ棒グラフの中間点。上げるほど小さいサイズが大きく見える
    「自動」ボタン        中央値のサイズが高さ50%になる位置に自動設定
    「デコード順で表示」  表示順 / デコード順の切り替え
  プレビュー画像
    マウスホイール        拡大 / 縮小
    ドラッグ              移動
    ダブルクリック        全体表示
  オーバーレイ・再生・書き出し
    「オーバーレイのみ」  動画の画像を使わず、オーバーレイだけを暗い背景に表示
    「キャッシュ生成」    現在のオーバーレイ設定で全フレームを描画して保存 (進捗表示・キャンセル可)
    「再生」 / Space      キャッシュ生成後に、連続再生 / 停止 (オーバーレイ設定を変えると再度キャッシュが必要)
    「開始点」「終了点」  選択中のフレームを、書き出し範囲の開始 / 終了にする (「全体」で解除)
    「動画を書き出し...」 指定した範囲を、現在のオーバーレイ設定でMP4に保存 (音声なし。進捗表示・キャンセル可)
  その他
    「JSONを保存...」     解析結果(フレーム一覧)をJSONで保存
    「ダークモード」      表示テーマの切り替え
    「English」/「日本語」     表示言語の切り替え (再起動後に反映)

■ 対応コーデックについて
  - タイムライン(GOP表示)は、FFmpegで読める動画ならおおむね対応します。
  - ブロック情報のオーバーレイ表示は、FFmpegのデコーダが情報を出力するコーデックのみ対応します。
    動画を開くたびに自動で判定し、取得できない場合は画面に注記を表示します。

■ 注意
  - ブロック情報のオーバーレイは FFmpeg の codecview フィルタで画像に描画しているため、
    線の太さは動画の解像度に依存します。
  - 解析やキャッシュで作る一時ファイルは、%TEMP%\gop_plus_analyzer_* に保存され、終了時に自動で削除されます。
    キャッシュは全フレーム分の画像になるため、動画によっては容量が大きくなります。
  - 書き出しは H.264 (MP4) で、音声は含まれません。
  - 設定 (言語、ダークモード) は、レジストリ HKEY_CURRENT_USER\Software\TPW-894\GOP-Plus-Analyzer
    に保存されます。削除するときはフォルダを消し、必要ならこのキーも削除してください。
  - 動画の内容をネットワークへ送信することはありません (通信機能はありません)。
  - ウイルス対策ソフトが誤検知することがあります。ソースコードは上記のGitHubで公開しています。

■ ライセンス
  このソフトは GNU General Public License v3.0 以降 (GPL-3.0-or-later) で配布しています。
  全文は同梱の LICENSE を参照してください。
  このソフトは無保証です。使用によって生じた損害について、作者は責任を負いません。

  同梱している第三者ソフトウェア (FFmpeg、Python、Qt for Python など) については、
  THIRD_PARTY_NOTICES.txt と licenses フォルダ (BOOTHの配布パッケージに含まれます) を参照してください。

■ 連絡先
  不具合・質問・要望: BOOTHのメッセージ / X: <URL> / マシュマロ: <URL> / GitHub Issues


==============================================================
English
==============================================================

* Overview
A tool that inspects and displays the frame structure of a video file.

  - GOP timeline: I / P / B frames shown in color, with a per-frame size bar graph
  - GOP statistics: frame count, GOP count, GOP length (avg/max/min), average size per type, average bitrate
  - Block information overlay: motion vectors / block partitions / QP drawn over the selected frame
  - Overlay-only view, full-frame cache generation and continuous playback
  - Export of a selected range as a video (MP4) with the overlay
  - Dark mode, Japanese / English UI

* Requirements
  - Windows 10 / 11 (64-bit)
  - No installation needed. Put this folder anywhere and run "GOP+ Analyzer.exe".
  - FFmpeg (ffmpeg.exe / ffprobe.exe) is included.

* Running from source (GitHub)
  GitHub contains the source code only. The exe, FFmpeg and the "licenses" folder are in the BOOTH package.
  1. Install Python 3 and run: pip install -r requirements.txt
  2. Add ffmpeg / ffprobe to PATH, or put them in the same folder as gop_plus_analyzer.py.
  3. Run: python gop_plus_analyzer.py  (pass a video file as an argument to open it at startup)

* How to use
  1. Run "GOP+ Analyzer.exe", then drop a video file onto the window or select one with the "Open..." button.
  2. When analysis finishes, all frames are shown on the timeline.
  3. Click a frame on the timeline to see its image with the block information overlay.
  4. Build the cache to render all frames in advance, then use "Play" for continuous playback.
  5. Set the range with "Set in" / "Set out", then save an MP4 with the overlay using "Export video...".

* Controls
  Timeline
    Mouse wheel             Zoom in / out
    Left-button drag        Select frames (follows the cursor)
    Middle-button drag      Pan the view
    Left / Right arrows     Move the selection by one frame
    Slider on the right     Midpoint of the size bars. Raise it to make small sizes look larger
    "Auto" button           Set the midpoint so that the median size is at 50% height
    "Show in decode order"  Switch between display order and decode order
  Preview image
    Mouse wheel             Zoom in / out
    Drag                    Pan
    Double-click            Fit to window
  Overlay / playback / export
    "Overlay only"          Show only the overlay on a dark background, without the video image
    "Build cache"           Render all frames with the current overlay settings (progress, cancelable)
    "Play" / Space          Play / stop after the cache is built (changing overlay settings needs a new cache)
    "Set in" / "Set out"    Use the selected frame as the start / end of the export range ("All" clears it)
    "Export video..."       Save the range to MP4 with the current overlay settings (no audio; progress, cancelable)
  Other
    "Save JSON..."          Save the analysis result (frame list) as JSON
    "Dark mode"             Switch the theme
    "English" / "日本語"     Switch the UI language (applied after restart)

* Codec support
  - The timeline works with most videos that FFmpeg can read.
  - The block information overlay works only for codecs whose FFmpeg decoder outputs that information.
    The app checks this each time you open a video and shows a note when the information cannot be obtained.

* Notes
  - The block information overlay is drawn into the image by FFmpeg's codecview filter, so line thickness
    depends on the video resolution.
  - Temporary files created during analysis and caching are stored in %TEMP%\gop_plus_analyzer_* and deleted automatically on exit.
    The cache contains an image for every frame, so it can become large for some videos.
  - Exported videos are H.264 (MP4) and contain no audio.
  - Settings (language, dark mode) are stored in
    HKEY_CURRENT_USER\Software\TPW-894\GOP-Plus-Analyzer.
    To uninstall, delete the folder (and this registry key, if you wish).
  - Nothing is sent over the network (the app has no networking code).
  - Antivirus software may report false positives. The source code is public on GitHub (see above).

* License
  This software is distributed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).
  See the included LICENSE file for the full text.
  This software comes with NO WARRANTY. The author is not liable for any damage arising from its use.

  For bundled third-party software (FFmpeg, Python, Qt for Python, etc.),
  see THIRD_PARTY_NOTICES.txt and the "licenses" folder (included in the BOOTH package).

* Contact
  Bug reports, questions and feature requests: BOOTH message / X: <URL> / Marshmallow: <URL> / GitHub Issues
