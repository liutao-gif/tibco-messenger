"""Application theme / stylesheet."""

DARK_STYLE = """
/* === Global === */
QMainWindow, QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-size: 13px;
}

/* === GroupBox === */
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    color: #89b4fa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}

/* === LineEdit, SpinBox, ComboBox === */
QLineEdit, QSpinBox, QComboBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #89b4fa;
}
QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}

/* === PushButton === */
QPushButton {
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 16px;
    background-color: #313244;
    color: #cdd6f4;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton#btn_send {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    font-weight: bold;
    padding: 8px 28px;
    font-size: 14px;
}
QPushButton#btn_send:hover {
    background-color: #74c7ec;
}
QPushButton#btn_send:pressed {
    background-color: #89dceb;
}

/* === QListWidget === */
QListWidget {
    border: 1px solid #45475a;
    border-radius: 6px;
    background-color: #181825;
    color: #cdd6f4;
    padding: 4px;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}
QListWidget::item:hover:!selected {
    background-color: #313244;
}

/* === QTextEdit (editor + viewer) === */
QTextEdit {
    border: 1px solid #45475a;
    border-radius: 6px;
    background-color: #181825;
    color: #cdd6f4;
    padding: 8px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}
QTextEdit:focus {
    border: 1px solid #89b4fa;
}

/* === ScrollBar === */
QScrollBar:vertical {
    background: #1e1e2e;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #1e1e2e;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #585b70;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* === Splitter === */
QSplitter::handle {
    background-color: #313244;
    width: 2px;
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #89b4fa;
}

/* === StatusBar === */
QStatusBar {
    background: #181825;
    color: #a6adc8;
    border-top: 1px solid #313244;
    padding: 4px 8px;
    font-size: 12px;
}

/* === QLabel === */
QLabel {
    color: #cdd6f4;
    background: transparent;
}

/* === Line Numbers === */
QTextEdit#line_numbers {
    background-color: #181825;
    color: #585b70;
    border: none;
    padding: 8px 4px;
}

/* === Response Viewer === */
QTextEdit#response_viewer {
    background-color: #11111b;
    color: #cdd6f4;
}

/* === Status labels === */
QLabel#status_ok {
    color: #a6e3a1;
    font-weight: bold;
}
QLabel#status_error {
    color: #f38ba8;
    font-weight: bold;
}
QLabel#status_info {
    color: #a6adc8;
}
"""

LIGHT_STYLE = """
QMainWindow, QDialog {
    background-color: #eff1f5;
    color: #4c4f69;
}
QWidget {
    background-color: #eff1f5;
    color: #4c4f69;
    font-size: 13px;
}

QGroupBox {
    border: 1px solid #ccd0da;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    color: #1e66f5;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}

QLineEdit, QSpinBox, QComboBox {
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 6px 10px;
    background-color: #ffffff;
    color: #4c4f69;
    selection-background-color: #1e66f5;
    selection-color: #ffffff;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #1e66f5;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #4c4f69;
    border: 1px solid #ccd0da;
    selection-background-color: #1e66f5;
    selection-color: #ffffff;
}

QPushButton {
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 6px 16px;
    background-color: #e6e9ef;
    color: #4c4f69;
}
QPushButton:hover {
    background-color: #ccd0da;
}
QPushButton:pressed {
    background-color: #bcc0cc;
}
QPushButton#btn_send {
    background-color: #1e66f5;
    color: #ffffff;
    border: none;
    font-weight: bold;
    padding: 8px 28px;
    font-size: 14px;
}
QPushButton#btn_send:hover {
    background-color: #2a7af5;
}

QListWidget {
    border: 1px solid #ccd0da;
    border-radius: 6px;
    background-color: #ffffff;
    color: #4c4f69;
    padding: 4px;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #1e66f5;
    color: #ffffff;
}

QTextEdit {
    border: 1px solid #ccd0da;
    border-radius: 6px;
    background-color: #ffffff;
    color: #4c4f69;
    padding: 8px;
}
QTextEdit:focus {
    border: 1px solid #1e66f5;
}

QScrollBar:vertical {
    background: #eff1f5;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #ccd0da;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #bcc0cc;
}

QSplitter::handle {
    background-color: #ccd0da;
    width: 2px;
    height: 2px;
}

QStatusBar {
    background: #e6e9ef;
    color: #6c6f85;
    border-top: 1px solid #ccd0da;
    padding: 4px 8px;
    font-size: 12px;
}
"""

APP_STYLESHEET = DARK_STYLE
