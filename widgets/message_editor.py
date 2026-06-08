"""Message editor and sender panel."""

import time
import xml.etree.ElementTree as ET

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QComboBox, QLabel, QSpinBox, QGroupBox, QSplitter, QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QTextCursor, QColor, QSyntaxHighlighter, QTextCharFormat


class XmlHighlighter(QSyntaxHighlighter):
    """Simple XML syntax highlighter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []

        # XML tags
        tag_fmt = QTextCharFormat()
        tag_fmt.setForeground(QColor(0, 0, 180))
        tag_fmt.setFontWeight(QFont.Weight.Bold)

        import re
        self._rules = [
            (re.compile(r"</?[a-zA-Z0-9_\.\-:]+"), tag_fmt),
            (re.compile(r"/?>"), tag_fmt),
            # Attributes
            (re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_\.\-]*="[^"]*"'), QTextCharFormat()),
        ]
        attr_fmt = QTextCharFormat()
        attr_fmt.setForeground(QColor(180, 80, 0))
        self._rules.append((re.compile(r'[a-zA-Z_][a-zA-Z0-9_\.\-]*='), attr_fmt))

        # Values in quotes
        val_fmt = QTextCharFormat()
        val_fmt.setForeground(QColor(0, 120, 0))
        self._rules.append((re.compile(r'"[^"]*"'), val_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class MessageEditor(QGroupBox):
    send_requested = pyqtSignal(str, str, float)  # subject, xml_body, timeout
    save_template_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Message Editor", parent)
        self._subject_keys: dict[str, str] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Top bar: target subject + mode + timeout
        top_row = QHBoxLayout()

        top_row.addWidget(QLabel("Target:"))

        self.subject_combo = QComboBox()
        self.subject_combo.setEditable(True)
        self.subject_combo.setMinimumWidth(250)
        self.subject_combo.setToolTip("Select a named target or type a subject directly")
        top_row.addWidget(self.subject_combo, 1)

        top_row.addWidget(QLabel("Mode:"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Send", "SendRequest"])
        top_row.addWidget(self.mode_combo)

        top_row.addWidget(QLabel("Timeout (s):"))

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(20)
        top_row.addWidget(self.timeout_spin)

        # Validate button
        btn_validate = QPushButton("Validate XML")
        btn_validate.clicked.connect(self._on_validate)
        top_row.addWidget(btn_validate)

        # Format button
        btn_format = QPushButton("Format XML")
        btn_format.clicked.connect(self._on_format)
        top_row.addWidget(btn_format)

        layout.addLayout(top_row)

        # Editor area with line numbers
        editor_layout = QHBoxLayout()

        self.line_numbers = QTextEdit()
        self.line_numbers.setReadOnly(True)
        self.line_numbers.setFixedWidth(44)
        self.line_numbers.setObjectName("line_numbers")
        self.line_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setFont(QFont("Menlo", 12))
        self.line_numbers.setFrameShape(QTextEdit.Shape.NoFrame)

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Menlo", 12))
        self.editor.setPlaceholderText(
            'Enter XML message body here...\n\nExample:\n<Request>\n  <Body>\n    <LotID>ABC123</LotID>\n  </Body>\n</Request>'
        )
        self.editor.setTabStopDistance(20)
        self.editor.textChanged.connect(self._update_line_numbers)

        self.highlighter = XmlHighlighter(self.editor.document())

        editor_layout.addWidget(self.line_numbers)
        editor_layout.addWidget(self.editor, 1)
        layout.addLayout(editor_layout, 1)

        # Bottom: send button
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self.size_label = QLabel("Size: 0 B")
        self.size_label.setObjectName("status_info")
        bottom_row.addWidget(self.size_label)

        btn_save_tpl = QPushButton("Save Template")
        btn_save_tpl.setToolTip("Save current message as a template")
        btn_save_tpl.clicked.connect(lambda: self.save_template_requested.emit())
        bottom_row.addWidget(btn_save_tpl)

        self.btn_send = QPushButton("⏎  Send")
        self.btn_send.setObjectName("btn_send")
        self.btn_send.setToolTip("Send message (Cmd+Enter)")
        self.btn_send.clicked.connect(self._on_send)
        bottom_row.addWidget(self.btn_send)

        layout.addLayout(bottom_row)

        # Shortcut
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self._on_send)
        QShortcut(QKeySequence("Ctrl+Enter"), self).activated.connect(self._on_send)

        self._update_line_numbers()

    def _update_line_numbers(self):
        text = self.editor.toPlainText()
        lines = text.count("\n") + 1
        nums = "\n".join(str(i) for i in range(1, lines + 1))
        self.line_numbers.setText(nums)

        # Sync scroll
        self.line_numbers.verticalScrollBar().setValue(
            self.editor.verticalScrollBar().value()
        )

        size = len(text.encode("utf-8"))
        if size < 1024:
            self.size_label.setText(f"Size: {size} B")
        else:
            self.size_label.setText(f"Size: {size / 1024:.1f} KB")

    def set_subject_keys(self, keys: dict[str, str]):
        """Update the subject combo with named targets."""
        self._subject_keys = keys
        self.subject_combo.clear()
        for name, subject in keys.items():
            self.subject_combo.addItem(f"{name} → {subject}", subject)
        self.subject_combo.setCurrentText("")

    def set_subject(self, subject: str):
        self.subject_combo.setCurrentText(subject)

    def get_subject(self) -> str:
        data = self.subject_combo.currentData()
        if data:
            return data
        return self.subject_combo.currentText().strip()

    def get_xml_body(self) -> str:
        return self.editor.toPlainText()

    def set_xml_body(self, xml: str):
        self.editor.setPlainText(xml)

    def _on_validate(self):
        xml_text = self.editor.toPlainText().strip()
        if not xml_text:
            QMessageBox.warning(self, "Validate XML", "Message body is empty.")
            return
        try:
            ET.fromstring(xml_text)
            QMessageBox.information(self, "Validate XML", "XML is well-formed.")
        except ET.ParseError as e:
            QMessageBox.critical(self, "Validate XML", f"XML parse error:\n{e}")

    def _on_format(self):
        xml_text = self.editor.toPlainText().strip()
        if not xml_text:
            return
        try:
            from xml.dom import minidom
            pretty = minidom.parseString(xml_text).toprettyxml(indent="  ")
            # Remove the XML declaration line
            lines = pretty.split("\n")
            if lines and lines[0].startswith("<?xml"):
                pretty = "\n".join(lines[1:])
            self.editor.setPlainText(pretty.strip())
        except Exception as e:
            QMessageBox.critical(self, "Format XML", f"Failed to format:\n{e}")

    def _on_send(self):
        xml_body = self.editor.toPlainText().strip()
        if not xml_body:
            QMessageBox.warning(self, "Send Message", "Message body is empty.")
            return
        subject = self.get_subject()
        timeout = float(self.timeout_spin.value())
        self.send_requested.emit(subject, xml_body, timeout)
