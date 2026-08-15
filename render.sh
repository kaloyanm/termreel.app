#!/usr/bin/env bash
# render.sh — turn a recorded .cast file into an mp4 (and optionally a gif)
# ready to drop into a video editor / YouTube upload.
#
# Requires: agg (https://github.com/asciinema/agg)   -> cast to gif
#           ffmpeg                                    -> gif to mp4 / direct render
#
# Usage:
#   ./render.sh session.cast output_basename [theme]
#
# themes: asciinema's built-in themes, e.g. monokai, solarized-dark, dracula

set -euo pipefail

CAST_FILE="${1:?usage: render.sh <session.cast> <output_basename> [theme]}"
OUT_BASE="${2:?usage: render.sh <session.cast> <output_basename> [theme]}"
THEME="${3:-dracula}"

echo "[*] Rendering ${CAST_FILE} -> ${OUT_BASE}.gif (theme: ${THEME})"
agg --theme "${THEME}" --font-size 18 --speed 1.0 "${CAST_FILE}" "${OUT_BASE}.gif"

echo "[*] Converting gif -> mp4"
ffmpeg -y -i "${OUT_BASE}.gif" \
  -movflags faststart -pix_fmt yuv420p \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
  "${OUT_BASE}.mp4"

echo "[+] Done: ${OUT_BASE}.mp4"
echo "    (optionally overlay voiceover/narration with ffmpeg -i ${OUT_BASE}.mp4 -i narration.mp3 -c:v copy -c:a aac out_final.mp4)"
