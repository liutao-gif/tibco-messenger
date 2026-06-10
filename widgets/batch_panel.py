"""Batch send panel — send multiple messages at once."""

import time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QProgressBar, QLabel, QDialog, QDialogButtonBox,
    QTextEdit, QComboBox, QLineEdit, QSpinBox, QFormLayout, QHeaderView, QMessageBox,
    QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from models import BatchMessage


class _BatchEditDialog(QDialog):
    """Dialog for adding/editing a batch message."""

    def __init__(self, parent=None, msg: BatchMessage = None, subject_keys: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Message" if msg else "Add Message")
        self.resize(700, 450)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.subject_combo = QComboBox()
        self.subject_combo.setEditable(True)
        self.subject_combo.setMinimumWidth(300)
        if subject_keys:
            for name, subject in subject_keys.items():
                self.subject_combo.addItem(f"{name} → {subject}", subject)
        form.addRow("Subject:", self.subject_combo)

        self.thread_edit = QLineEdit()
        self.thread_edit.setText(msg.thread_id if msg else "1")
        self.thread_edit.setPlaceholderText("e.g. 1 or abc")
        self.thread_edit.setToolTip("Same value = same thread (sequential), different = parallel")
        form.addRow("Thread:", self.thread_edit)
        layout.addLayout(form)

        from widgets.message_editor import XmlHighlighter
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Menlo", 12))
        self.editor.setPlaceholderText("<Request>\n  <Body>\n    ...\n  </Body>\n</Request>")
        self._highlighter = XmlHighlighter(self.editor.document())
        layout.addWidget(self.editor, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if msg:
            idx = self.subject_combo.findData(msg.subject)
            if idx >= 0:
                self.subject_combo.setCurrentIndex(idx)
            else:
                self.subject_combo.setCurrentText(msg.subject)
            self.editor.setPlainText(msg.xml_body)

    def get_subject(self) -> str:
        data = self.subject_combo.currentData()
        if data:
            return data
        return self.subject_combo.currentText().strip()

    def get_message(self) -> BatchMessage:
        return BatchMessage(
            subject=self.get_subject(),
            xml_body=self.editor.toPlainText().strip(),
            thread_id=self.thread_edit.text().strip() or "1",
        )


class BatchPanel(QWidget):
    """Batch send panel with message table, controls, progress, and response viewer."""

    send_all_requested = pyqtSignal(list, str, float)  # messages, mode, timeout
    _result_ready = pyqtSignal(int, bool, str, str)  # index, success, response, error

    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages: list[BatchMessage] = []
        self._subject_keys: dict[str, str] = {}
        self._result_ready.connect(self.update_result)
        self._setup_ui()

    def set_subject_keys(self, keys: dict[str, str]):
        self._subject_keys = keys or {}

    def emit_result(self, index: int, success: bool, response: str = "", error: str = ""):
        """Thread-safe result update — emits signal to main thread."""
        self._result_ready.emit(index, success, response, error)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_add.clicked.connect(self._on_add)
        toolbar.addWidget(self.btn_add)

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self._on_edit)
        toolbar.addWidget(self.btn_edit)

        self.btn_remove = QPushButton("Remove")
        self.btn_remove.clicked.connect(self._on_remove)
        toolbar.addWidget(self.btn_remove)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self._on_clear)
        toolbar.addWidget(self.btn_clear)

        toolbar.addStretch()

        toolbar.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Send", "SendRequest"])
        toolbar.addWidget(self.mode_combo)

        toolbar.addWidget(QLabel("Timeout(s):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(20)
        toolbar.addWidget(self.timeout_spin)

        self.btn_send_all = QPushButton("Send All")
        self.btn_send_all.setObjectName("btn_send")
        self.btn_send_all.setToolTip("Send all messages in the list")
        self.btn_send_all.clicked.connect(self._on_send_all)
        toolbar.addWidget(self.btn_send_all)

        layout.addLayout(toolbar)

        # Splitter: table above, response viewer below
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(1)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Thread", "Subject", "Preview", "Status", "Response"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 100)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.table)

        # Response viewer
        from widgets.response_viewer import ResponseXmlHighlighter
        self.response_viewer = QTextEdit()
        self.response_viewer.setReadOnly(True)
        self.response_viewer.setFont(QFont("Menlo", 12))
        self.response_viewer.setPlaceholderText("Click a row to view response...")
        self._highlighter = ResponseXmlHighlighter(self.response_viewer.document())
        splitter.addWidget(self.response_viewer)

        splitter.setSizes([400, 200])
        layout.addWidget(splitter, 1)

        # Progress
        progress_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_row.addWidget(self.progress_bar, 1)

        self.summary_label = QLabel("")
        progress_row.addWidget(self.summary_label)

        layout.addLayout(progress_row)

    def _refresh_table(self):
        self.table.setRowCount(len(self._messages))
        for i, msg in enumerate(self._messages):
            self.table.setItem(i, 0, QTableWidgetItem(msg.thread_id))
            self.table.setItem(i, 1, QTableWidgetItem(msg.subject))
            preview = msg.xml_body.replace("\n", " ")[:80]
            self.table.setItem(i, 2, QTableWidgetItem(preview))
            resp_preview = (msg.response_text or "").replace("\n", " ")[:40]
            if resp_preview:
                item = QTableWidgetItem(resp_preview)
                item.setToolTip(msg.response_text or "")
                self.table.setItem(i, 4, item)
            elif self.table.item(i, 4) is None:
                self.table.setItem(i, 4, QTableWidgetItem(""))
            if self.table.item(i, 3) is None:
                self.table.setItem(i, 3, QTableWidgetItem(""))

    def _on_selection_changed(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._messages):
            return
        resp = self._messages[row].response_text
        if resp:
            # Pretty-print XML
            try:
                import re
                from xml.dom import minidom
                pretty = minidom.parseString(resp).toprettyxml(indent="  ")
                lines = pretty.split("\n")
                if lines and lines[0].startswith("<?xml"):
                    pretty = "\n".join(lines[1:])
                pretty = re.sub(r'\n\s*\n', '\n', pretty)
                self.response_viewer.setPlainText(pretty.strip())
            except Exception:
                self.response_viewer.setPlainText(resp)
        else:
            self.response_viewer.clear()

    def _on_add(self):
        dialog = _BatchEditDialog(self, subject_keys=self._subject_keys)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            msg = dialog.get_message()
            if msg.subject and msg.xml_body:
                self._messages.append(msg)
                self._refresh_table()
                self.table.selectRow(len(self._messages) - 1)

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            return
        msg = self._messages[row]
        dialog = _BatchEditDialog(self, msg, self._subject_keys)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_msg = dialog.get_message()
            if new_msg.subject and new_msg.xml_body:
                new_msg.response_text = msg.response_text
                self._messages[row] = new_msg
                self._refresh_table()
                self.table.selectRow(row)

    def _on_remove(self):
        row = self.table.currentRow()
        if row < 0:
            return
        del self._messages[row]
        self._refresh_table()

    def _on_clear(self):
        self._messages.clear()
        self._refresh_table()
        self.response_viewer.clear()
        self.progress_bar.setVisible(False)
        self.summary_label.setText("")

    def _on_send_all(self):
        if not self._messages:
            QMessageBox.warning(self, "Send All", "No messages to send.")
            return
        # Reset status column
        for i in range(len(self._messages)):
            self.table.setItem(i, 3, QTableWidgetItem("..."))
            self.table.setItem(i, 4, QTableWidgetItem(""))
            self._messages[i].response_text = ""
        self._refresh_table()
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self._messages))
        self.progress_bar.setValue(0)
        self.summary_label.setText(f"0 / {len(self._messages)}")

        mode = self.mode_combo.currentText()
        timeout = float(self.timeout_spin.value())
        self.send_all_requested.emit(list(self._messages), mode, timeout)

    def update_result(self, index: int, success: bool, response: str = "", error: str = ""):
        """Update a single row's status after sending."""
        if success and response:
            self._messages[index].response_text = response
        elif not success and error:
            self._messages[index].response_text = ""

        status_item = QTableWidgetItem("OK" if success else "FAIL")
        status_item.setForeground(QColor(100, 210, 120) if success else QColor(235, 100, 100))
        self.table.setItem(index, 3, status_item)

        resp_preview = response.replace("\n", " ")[:40] if response else ("—" if success else "")
        resp_item = QTableWidgetItem(resp_preview)
        if response:
            resp_item.setToolTip(response)
        self.table.setItem(index, 4, resp_item)

        if not success:
            old = self.table.item(index, 2)
            self.table.setItem(index, 2, QTableWidgetItem(
                old.text() + f"  [{error[:50]}]"
            ))

        self.progress_bar.setValue(self.progress_bar.value() + 1)
        done = self.progress_bar.value()
        total = len(self._messages)
        ok_count = sum(1 for m in self._messages if m.response_text)
        fail_count = done - ok_count
        self.summary_label.setText(f"{done} / {total}  |  OK: {ok_count}  FAIL: {fail_count}")

        # Auto-select the row to show response
        self.table.selectRow(index)

    def get_mode(self) -> str:
        return self.mode_combo.currentText()

    def get_timeout(self) -> float:
        return float(self.timeout_spin.value())
