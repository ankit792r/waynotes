
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFrame,
    QScrollArea,
    QInputDialog,
    QMessageBox,
    QSizePolicy,
)

from todo_client import TodoClient


class WorkerSignals(QObject):
    finished = pyqtSignal(object, object)


class Worker(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.signals.finished.emit(self.function(), None)
        except Exception as exc:
            self.signals.finished.emit(None, str(exc))


class TodoRow(QFrame):
    def __init__(self, todo, on_toggle, on_edit, on_delete):
        super().__init__()
        self.todo = todo
        self.setObjectName("taskRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 10, 10)
        layout.setSpacing(10)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(todo["completed"])
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.toggled.connect(
            lambda checked: on_toggle(todo, checked)
        )
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        self.title_label = QLabel(todo["title"])
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName(
            "completedTitle" if todo["completed"] else "taskTitle"
        )
        self.title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_label.mouseDoubleClickEvent = (
            lambda event: on_edit(todo)
        )
        title_layout.addWidget(self.title_label)

        meta = QLabel("Completed" if todo["completed"] else "To do")
        meta.setObjectName("taskMeta")
        title_layout.addWidget(meta)

        layout.addLayout(title_layout, 1)

        self.edit_button = QPushButton("Edit")
        self.edit_button.setObjectName("iconButton")
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_button.clicked.connect(lambda: on_edit(todo))
        layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("×")
        self.delete_button.setObjectName("iconButton")
        self.delete_button.setFixedSize(30, 30)
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_button.clicked.connect(lambda: on_delete(todo))
        layout.addWidget(self.delete_button)


class TodoPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.client = TodoClient()
        self.pool = QThreadPool(self)
        self.workers = []
        self.todos = []
        self.current_filter = "all"
        self.request_in_progress = False

        self.setObjectName("todoPanel")
        self.setWindowTitle("Waynotes")
        self.setMinimumSize(380, 460)
        self.resize(430, 610)

        self._build_ui()
        self.refresh()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 18)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header.setSpacing(12)

        # heading_column = QVBoxLayout()
        # heading_column.setSpacing(5)

        eyebrow = QLabel("YOUR WORKSPACE")
        eyebrow.setObjectName("eyebrow")
        # heading_column.addWidget(eyebrow)

        heading = QLabel("Waynotes")
        heading.setObjectName("heading")
        # heading_column.addWidget(heading)

        subtitle = QLabel("A little progress every day.")
        subtitle.setObjectName("subtitle")
        # heading_column.addWidget(subtitle)

        # header.addLayout(heading_column, 1)

        # close_button = QPushButton("×")
        # close_button.setObjectName("iconButton")
        # close_button.setFixedSize(34, 34)
        # close_button.clicked.connect(self.hide)
        # header.addWidget(close_button, 0, Qt.AlignmentFlag.AlignTop)

        # root.addLayout(header)

        # Summary cards
        stats = QGridLayout()
        stats.setSpacing(10)

        pending_card, self.pending_value = self._create_stat_card(
            "IN PROGRESS", "0", "Tasks to finish", "pendingStat"
        )
        completed_card, self.completed_value = self._create_stat_card(
            "COMPLETED", "0", "Nicely done", "completedStat"
        )

        stats.addWidget(pending_card, 0, 0)
        stats.addWidget(completed_card, 0, 1)
        root.addLayout(stats)

        # Task section header
        # section_header = QHBoxLayout()

        # section_title = QLabel("Today's tasks")
        # section_title.setObjectName("sectionTitle")
        # section_header.addWidget(section_title)

        # section_header.addStretch()

        # self.count_label = QLabel("0 tasks")
        # self.count_label.setObjectName("countLabel")
        # section_header.addWidget(self.count_label)

        # root.addLayout(section_header)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("⌕   Search tasks...")
        self.search_input.textChanged.connect(self.render_todos)
        root.addWidget(self.search_input)

        # Filters
        filter_row = QHBoxLayout()
        filter_row.setSpacing(7)

        self.filter_buttons = {}

        for key, label in (
            ("all", "All"),
            ("pending", "Pending"),
            ("completed", "Completed"),
        ):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setObjectName("filterButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked, value=key: self.set_filter(value)
            )
            self.filter_buttons[key] = button
            filter_row.addWidget(button)

        self.filter_buttons["all"].setChecked(True)
        filter_row.addStretch()

        root.addLayout(filter_row)

        # Task list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.list_widget = QWidget()
        self.list_widget.setObjectName("listContainer")

        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(1, 2, 5, 2)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()

        self.scroll.setWidget(self.list_widget)
        root.addWidget(self.scroll, 1)

        self.empty_label = QLabel("You're all caught up.\nAdd a task below.")
        self.empty_label.setObjectName("emptyState")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        self.list_layout.insertWidget(0, self.empty_label)

        # Add task field
        add_frame = QFrame()
        add_frame.setObjectName("addTaskFrame")

        add_layout = QHBoxLayout(add_frame)
        add_layout.setContentsMargins(10, 8, 8, 8)
        add_layout.setSpacing(8)

        plus = QLabel("+")
        plus.setObjectName("addPlus")
        plus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plus.setFixedWidth(22)
        add_layout.addWidget(plus)

        self.add_input = QLineEdit()
        self.add_input.setObjectName("addInput")
        self.add_input.setFrame(False)
        self.add_input.setPlaceholderText("Add something to your list...")
        self.add_input.returnPressed.connect(self.add_todo)
        add_layout.addWidget(self.add_input, 1)

        self.add_button = QPushButton("↑")
        self.add_button.setObjectName("primaryButton")
        self.add_button.setFixedSize(34, 34)
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.clicked.connect(self.add_todo)
        add_layout.addWidget(self.add_button)

        root.addWidget(add_frame)

    def _create_stat_card(self, heading, value, description, name):
        card = QFrame()
        card.setObjectName("statCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        heading_label = QLabel(heading)
        heading_label.setObjectName("statHeading")
        layout.addWidget(heading_label)

        value_label = QLabel(value)
        value_label.setObjectName(name)
        layout.addWidget(value_label)

        description_label = QLabel(description)
        description_label.setObjectName("statDescription")
        layout.addWidget(description_label)

        return card, value_label

    def _run(self, function, callback):
        worker = Worker(function)
        self.workers.append(worker)

        def finished(result, error):
            if worker in self.workers:
                self.workers.remove(worker)
            callback(result, error)

        worker.signals.finished.connect(finished)
        self.pool.start(worker)

    def refresh(self):
        if self.request_in_progress:
            return

        self.request_in_progress = True
        self._run(self.client.list_todos, self._on_refresh)

    def _on_refresh(self, todos, error):
        self.request_in_progress = False

        if error:
            # self.status_label.setText("Daemon unavailable")
            # self.status_label.setToolTip(error)
            return

        self.todos = todos
        # self.status_label.setText("Connected")
        # self.status_label.setToolTip("")
        self.render_todos()

    def set_filter(self, value):
        self.current_filter = value

        for key, button in self.filter_buttons.items():
            button.setChecked(key == value)

        self.render_todos()

    def render_todos(self, *_):
        pending = sum(not todo["completed"] for todo in self.todos)
        completed = len(self.todos) - pending

        self.pending_value.setText(f"{pending:02d}")
        self.completed_value.setText(f"{completed:02d}")
        # self.count_label.setText(
        #     f"{len(self.todos)} task" +
        #     ("" if len(self.todos) == 1 else "s")
        # )

        query = self.search_input.text().strip().casefold()

        filtered = [
            todo for todo in self.todos
            if (
                self.current_filter == "all"
                or (
                    self.current_filter == "pending"
                    and not todo["completed"]
                )
                or (
                    self.current_filter == "completed"
                    and todo["completed"]
                )
            )
            and query in todo["title"].casefold()
        ]

        while self.list_layout.count() > 2:
            item = self.list_layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.empty_label.setVisible(not filtered)

        if not filtered:
            if query:
                self.empty_label.setText(
                    "No matching tasks.\nTry a different search."
                )
            elif self.current_filter == "completed":
                self.empty_label.setText(
                    "No completed tasks yet.\nKeep going!"
                )
            elif self.current_filter == "pending":
                self.empty_label.setText(
                    "You're all caught up.\nNo pending tasks."
                )
            else:
                self.empty_label.setText(
                    "You're all caught up.\nAdd a task below."
                )
            return

        for todo in filtered:
            row = TodoRow(
                todo,
                self.toggle_todo,
                self.edit_todo,
                self.delete_todo,
            )
            self.list_layout.insertWidget(
                self.list_layout.count() - 1, row
            )

    def add_todo(self):
        title = self.add_input.text().strip()
        if not title:
            return

        self.add_button.setEnabled(False)

        def done(result, error):
            self.add_button.setEnabled(True)

            if error:
                # self.status_label.setText("Couldn't add task")
                # self.status_label.setToolTip(error)
                return

            self.add_input.clear()
            # self.status_label.setText("Task added")
            self.refresh()

        self._run(lambda: self.client.create(title), done)

    def toggle_todo(self, todo, checked):
        self._mutate(
            lambda: self.client.update(
                todo["id"], completed=checked
            )
        )

    def edit_todo(self, todo):
        title, accepted = QInputDialog.getText(
            self,
            "Edit task",
            "Task title:",
            text=todo["title"],
        )

        if not accepted:
            return

        title = title.strip()
        if not title:
            QMessageBox.warning(
                self, "Invalid title", "Task title cannot be empty."
            )
            return

        self._mutate(
            lambda: self.client.update(todo["id"], title=title)
        )

    def delete_todo(self, todo):
        answer = QMessageBox.question(
            self,
            "Delete task",
            f"Delete “{todo['title']}”?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self._mutate(lambda: self.client.delete(todo["id"]))

    def _mutate(self, operation):
        def done(result, error):
            if error:
                # self.status_label.setText("Operation failed")
                #   self.status_label.setToolTip(error)
                return

            # self.status_label.setText("Changes saved")
            # self.status_label.setToolTip(error)
            self.refresh()

        self._run(operation, done)
