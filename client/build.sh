#!/usr/bin/env bash
# Build standalone executables for the waynotes client (no Python needed at runtime).
#
# Usage: ./build.sh [--onedir] [--clean]
#   --onedir  Build unpacked directories instead of single files (faster startup).
#   --clean   Remove previous build artifacts before building.
#
# Output (in client/dist/):
#   waynotes         Qt panel (main.py)
#   waynotes-waybar  Waybar module (waybar.py), supports the `toggle` argument

set -euo pipefail

cd "$(dirname "$(realpath "$0")")"

mode="--onefile"
clean=0
for arg in "$@"; do
    case "$arg" in
        --onedir) mode="--onedir" ;;
        --clean) clean=1 ;;
        -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $arg" >&2; exit 1 ;;
    esac
done

if ! command -v uv >/dev/null 2>&1; then
    echo "error: uv is required to build (https://docs.astral.sh/uv/)" >&2
    exit 1
fi

if (( clean )); then
    rm -rf build dist ./*.spec
fi

uv sync --quiet

pyinstaller=(uv run --quiet --with "pyinstaller>=6.16" pyinstaller
    --noconfirm
    --log-level WARN
    "$mode"
    --specpath build
    --exclude-module tkinter
)

echo "==> building waynotes"
"${pyinstaller[@]}" --name waynotes --windowed main.py

echo "==> building waynotes-waybar"
"${pyinstaller[@]}" --name waynotes-waybar \
    --hidden-import main \
    waybar.py

echo
echo "Built:"
if [[ "$mode" == "--onefile" ]]; then
    ls -lh dist/waynotes dist/waynotes-waybar
else
    ls -d dist/waynotes/waynotes dist/waynotes-waybar/waynotes-waybar
fi
