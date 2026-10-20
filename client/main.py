#!/usr/bin/env python3

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from notes_ui import TodoPanel
from theme import dialog_stylesheet, panel_stylesheet
from ui_control import listen_for_toggle, send_toggle


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(panel_stylesheet() + dialog_stylesheet())


def toggle_panel(panel: TodoPanel) -> None:
    if panel.isVisible():
        panel.hide()
    else:
        panel.show()
        panel.raise_()
        panel.activateWindow()


def start_panel(app: QApplication) -> int:
    apply_theme(app)
    panel = TodoPanel()
    app._waynotes_control_server = listen_for_toggle(
        lambda: toggle_panel(panel)
    )
    panel.show()
    return app.exec()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Waynotes")

    if send_toggle():
        return 0

    return start_panel(app)


if __name__ == "__main__":
    sys.exit(main())