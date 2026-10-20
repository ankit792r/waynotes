
def panel_stylesheet() -> str:
    return """
    * {
        font-family: "Inter", "Noto Sans", sans-serif;
        font-size: 13px;
    }

    QWidget#todoPanel {
        background: #17181f;
        color: #e5e7eb;
    }

    QLabel {
        background: transparent;
    }

    QLabel#eyebrow {
        color: #969bad;
        font-size: 10px;
        font-weight: 700;
    }

    QLabel#heading {
        color: #f5f6fa;
        font-size: 25px;
        font-weight: 750;
    }

    QLabel#subtitle {
        color: #9296a7;
        font-size: 12px;
    }

    QLabel#sectionTitle {
        color: #f0f1f6;
        font-size: 15px;
        font-weight: 650;
    }

    QLabel#countLabel {
        background: #292b3b;
        color: #b6bbff;
        border: 1px solid #3b3e55;
        border-radius: 9px;
        padding: 6px 9px;
        font-size: 11px;
        font-weight: 650;
    }

    QFrame#statCard {
        background: #22242d;
        border: 1px solid #30323d;
        border-radius: 12px;
    }

    QLabel#statHeading {
        color: #a5b4fc;
        font-size: 10px;
        font-weight: 700;
    }

    QLabel#pendingStat {
        color: #f5f6fa;
        font-size: 27px;
        font-weight: 750;
    }

    QLabel#completedStat {
        color: #86efac;
        font-size: 27px;
        font-weight: 750;
    }

    QLabel#statDescription {
        color: #9296a7;
        font-size: 11px;
    }

    QLabel#statusLabel {
        color: #85899a;
        font-size: 11px;
    }

    QLineEdit {
        background: #22242d;
        color: #f3f4f6;
        border: 1px solid #363946;
        border-radius: 9px;
        padding: 10px 12px;
        selection-background-color: #6366f1;
    }

    QLineEdit:hover {
        border-color: #4a4d5e;
    }

    QLineEdit:focus {
        border-color: #818cf8;
    }

    QLineEdit#addInput {
        background: transparent;
        border: none;
        padding: 7px 2px;
    }

    QLineEdit#addInput:focus {
        border: none;
        background: transparent;
    }

    QPushButton {
        background: #292b35;
        color: #e5e7eb;
        border: 1px solid #363946;
        border-radius: 8px;
        padding: 7px 11px;
    }

    QPushButton:hover {
        background: #343744;
        border-color: #484b5c;
    }

    QPushButton:pressed {
        background: #20212a;
    }

    QPushButton:checked {
        background: #34354b;
        color: #c7c9ff;
        border-color: #595c87;
    }

    QPushButton#filterButton {
        padding: 7px 12px;
        font-size: 11px;
    }

    QPushButton#primaryButton {
        background: #7477f5;
        color: #ffffff;
        border: 1px solid #8184ff;
        border-radius: 9px;
        font-size: 19px;
        font-weight: 650;
        padding: 4px;
    }

    QPushButton#primaryButton:hover {
        background: #8587ff;
    }

    QPushButton#iconButton {
        background: transparent;
        border: none;
        color: #9296a7;
        padding: 5px 8px;
    }

    QPushButton#iconButton:hover {
        background: #30323e;
        color: #ffffff;
    }

    QFrame#taskRow {
        background: #202129;
        border: 1px solid #2d2f3a;
        border-radius: 10px;
    }

    QFrame#taskRow:hover {
        background: #252731;
        border-color: #414456;
    }

    QLabel#taskTitle {
        color: #e9eaf0;
        font-size: 13px;
        font-weight: 500;
    }

    QLabel#completedTitle {
        color: #7e8291;
        font-size: 13px;
    }

    QLabel#taskMeta {
        color: #888c9d;
        font-size: 10px;
    }

    QLabel#emptyState {
        color: #9296a7;
        font-size: 12px;
        padding: 30px 10px;
    }

    QLabel#addPlus {
        color: #a5b4fc;
        font-size: 22px;
        font-weight: 400;
    }

    QFrame#addTaskFrame {
        background: #22242d;
        border: 1px solid #41445a;
        border-radius: 12px;
    }

    QCheckBox {
        spacing: 8px;
        background: transparent;
    }

    QCheckBox::indicator {
        width: 17px;
        height: 17px;
        border-radius: 6px;
        border: 1px solid #5c6072;
        background: #252731;
    }

    QCheckBox::indicator:hover {
        border-color: #a5b4fc;
    }

    QCheckBox::indicator:checked {
        background: #7477f5;
        border-color: #7477f5;
    }

    QScrollArea {
        border: none;
        background: transparent;
    }

    QScrollArea > QWidget > QWidget {
        background: transparent;
    }

    QScrollBar:vertical {
        width: 5px;
        background: transparent;
        margin: 2px 0;
    }

    QScrollBar::handle:vertical {
        background: #414453;
        border-radius: 2px;
        min-height: 24px;
    }

    QScrollBar::handle:vertical:hover {
        background: #656a80;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0;
    }

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: transparent;
    }
    """


def dialog_stylesheet() -> str:
    return """
    QMessageBox, QInputDialog {
        background: #1b1c24;
        color: #e5e7eb;
    }

    QMessageBox QLabel, QInputDialog QLabel {
        color: #e5e7eb;
    }

    QMessageBox QPushButton, QInputDialog QPushButton {
        min-width: 75px;
        padding: 8px 12px;
    }
    """
