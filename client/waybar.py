#!/usr/bin/env python3
"""Waybar custom module: pending count + click to toggle the Qt panel."""

from __future__ import annotations

import json
import sys

from todo_client import TodoClient


def waybar_status() -> dict[str, str]:
    try:
        counts = TodoClient().count()
    except (ConnectionError, RuntimeError, OSError):
        return {
            "text": "—",
            "tooltip": "waynotes: daemon unavailable",
            "class": "unavailable",
        }

    pending = counts.get("pending", 0)
    completed = counts.get("completed", 0)
    total = counts.get("total", 0)

    if pending == 0 and total > 0:
        text = "✓"
        tooltip = f"todo: {total} done"
        css_class = "done"
    elif pending == 0:
        text = "0"
        tooltip = "todo: empty"
        css_class = "empty"
    else:
        text = "TODO: " + str(pending)
        tooltip = f"todo: {pending} pending"
        if completed:
            tooltip += f", {completed} done"
        css_class = "pending"

    return {"text": text, "tooltip": tooltip, "class": css_class}


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "toggle":
        from PyQt6.QtWidgets import QApplication

        app = QApplication([])
        from ui_control import send_toggle

        if send_toggle():
            return 0

        from main import start_panel

        return start_panel(app)

    print(json.dumps(waybar_status()), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
