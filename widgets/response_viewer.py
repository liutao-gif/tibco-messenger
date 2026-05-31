"""Response viewer panel."""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QGroupBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor, QColor, QSyntaxHighlighter, QTextCharFormat


class ResponseXmlHighlighter(QSyntaxHighlighter):
    """XML syntax highlighter for response viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []

        import re
        tag_fmt = QTextCharFormat()
        tag_fmt.setForeground(QColor(137, 180, 250))
        tag_fmt.setFontWeight(QFont.Weight.Bold)
        self._rules.append((re.compile(r"</?[a-zA-Z0-9_\.\-:]+"), tag_fmt))
        self._rules.append((re.compile(r"/?>"), tag_fmt))

        attr_fmt = QTextCharFormat()
        attr_fmt.setForeground(QColor(250, 179, 135))
        self._rules.append((re.compile(r'[a-zA-Z_][a-zA-Z0-9_\.\-]*='), attr_fmt))

        val_fmt = QTextCharFormat()
        val_fmt.setForeground(QColor(166, 227, 161))
        self._rules.append((re.compile(r'"[^"]*"'), val_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class ResponseViewer(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Response Viewer", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Info bar
        info_row = QHBoxLayout()

        self.time_label = QLabel("Last send: --")
        info_row.addWidget(self.time_label)

        self.elapsed_label = QLabel("Elapsed: --")
        info_row.addWidget(self.elapsed_label)

        self.size_label = QLabel("Size: --")
        info_row.addWidget(self.size_label)

        self.status_label = QLabel("")
        info_row.addWidget(self.status_label, 1)

        btn_copy = QPushButton("Copy")
        btn_copy.clicked.connect(self._on_copy)
        info_row.addWidget(btn_copy)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self._on_clear)
        info_row.addWidget(btn_clear)

        layout.addLayout(info_row)

        # Viewer
        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setFont(QFont("Menlo", 12))
        self.viewer.setPlaceholderText("Response will appear here after sending a SendRequest...")
        self.viewer.setObjectName("response_viewer")
        self._highlighter = ResponseXmlHighlighter(self.viewer.document())
        layout.addWidget(self.viewer, 1)

    def show_response(self, xml: Optional[str], elapsed_ms: float, message_size: int):
        """Display a response."""
        from datetime import datetime
        self.time_label.setText(f"Received: {datetime.now().strftime('%H:%M:%S')}")
        self.elapsed_label.setText(f"Elapsed: {elapsed_ms:.0f} ms")
        self.size_label.setText(f"Size: {message_size} B" if message_size < 1024 else f"Size: {message_size / 1024:.1f} KB")

        if xml is None:
            self.status_label.setText("Timeout / No response")
            self.status_label.setObjectName("status_error")
            self.status_label.setStyleSheet("")
            self.viewer.clear()
        else:
            self.status_label.setText("OK")
            self.status_label.setObjectName("status_ok")
            self.status_label.setStyleSheet("")
            # Pretty-print if it looks like XML
            display = self._pretty_xml(xml)
            self.viewer.setPlainText(display)

    def show_error(self, error: str):
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("color: #e04040;")
        self.viewer.setPlainText(f"[ERROR] {error}")
        self.elapsed_label.setText("Elapsed: --")
        self.size_label.setText("Size: --")

    def show_sent(self, xml_size: int):
        from datetime import datetime
        self.time_label.setText(f"Sent: {datetime.now().strftime('%H:%M:%S')}")
        self.elapsed_label.setText("Elapsed: --")
        self.size_label.setText(f"Size: {xml_size} B" if xml_size < 1024 else f"Size: {xml_size / 1024:.1f} KB")
        self.status_label.setText("Sent (no reply)")
        self.status_label.setStyleSheet("color: #888;")
        self.viewer.clear()

    def _pretty_xml(self, xml: str) -> str:
        try:
            from xml.dom import minidom
            pretty = minidom.parseString(xml).toprettyxml(indent="  ")
            lines = pretty.split("\n")
            if lines and lines[0].startswith("<?xml"):
                pretty = "\n".join(lines[1:])
            return pretty.strip()
        except Exception:
            return xml

    def _on_copy(self):
        self.viewer.selectAll()
        self.viewer.copy()
        cursor = self.viewer.textCursor()
        cursor.clearSelection()
        self.viewer.setTextCursor(cursor)

    def _on_clear(self):
        self.viewer.clear()
        self.time_label.setText("Last send: --")
        self.elapsed_label.setText("Elapsed: --")
        self.size_label.setText("Size: --")
        self.status_label.setText("")
