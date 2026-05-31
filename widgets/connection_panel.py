"""Connection configuration panel — compact horizontal layout."""

import json
import os

from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QHBoxLayout, QVBoxLayout, QGroupBox, QFileDialog, QLabel,
    QMessageBox, QListWidget, QListWidgetItem, QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from models import ConnectionConfig


class StatusDot(QWidget):
    """A small colored circle indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(235, 100, 100)
        self.setFixedSize(10, 10)

    def set_ok(self, ok: bool):
        self._color = QColor(100, 210, 120) if ok else QColor(235, 100, 100)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(self._color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 8, 8)


class ConnectionPanel(QGroupBox):
    config_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__("Connection", parent)
        self._config = ConnectionConfig()
        self._expanded = False
        self._setup_ui()

    def _setup_ui(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setSpacing(6)

        # === Row 1: Compact quick-access bar ===
        bar = QHBoxLayout()
        bar.setSpacing(8)

        # Env preset
        bar.addWidget(QLabel("Env:"))
        self.env_combo = QComboBox()
        self.env_combo.setMinimumWidth(120)
        self.env_combo.addItem("Custom")
        self._add_env_presets()
        self.env_combo.currentTextChanged.connect(self._on_env_changed)
        bar.addWidget(self.env_combo)

        bar.addWidget(self._vsep())

        # Key fields in a row
        bar.addWidget(QLabel("Svc:"))
        self.field_service = QLineEdit(self._config.service)
        self.field_service.setPlaceholderText("7030")
        self.field_service.setFixedWidth(60)
        bar.addWidget(self.field_service)

        bar.addWidget(QLabel("Net:"))
        self.field_network = QLineEdit(self._config.network)
        self.field_network.setPlaceholderText("10.80.30.64")
        self.field_network.setMinimumWidth(110)
        bar.addWidget(self.field_network)

        bar.addWidget(QLabel("Daemon:"))
        self.field_daemon = QLineEdit(self._config.daemon)
        self.field_daemon.setPlaceholderText("tcp:host:7500")
        self.field_daemon.setMinimumWidth(150)
        bar.addWidget(self.field_daemon)

        bar.addWidget(self._vsep())

        # Status
        self.status_dot = StatusDot()
        bar.addWidget(self.status_dot)
        self.status_label = QLabel("Unknown")
        self.status_label.setObjectName("status_info")
        bar.addWidget(self.status_label)

        bar.addStretch()

        # Action buttons
        btn_test = QPushButton("Test")
        btn_test.setToolTip("Test Tibco connection")
        btn_test.clicked.connect(self._on_test)
        bar.addWidget(btn_test)

        btn_load = QPushButton("Load XML")
        btn_load.setToolTip("Load config.xml file")
        btn_load.clicked.connect(self._on_load)
        bar.addWidget(btn_load)

        btn_save = QPushButton("Save XML")
        btn_save.setToolTip("Save to config.xml file")
        btn_save.clicked.connect(self._on_save)
        bar.addWidget(btn_save)

        # Expand toggle
        self.btn_expand = QPushButton("▸ More")
        self.btn_expand.setToolTip("Show advanced settings")
        self.btn_expand.clicked.connect(self._toggle_expand)
        bar.addWidget(self.btn_expand)

        self._main_layout.addLayout(bar)

        # === Row 2: Expandable advanced settings ===
        self._advanced = QWidget()
        self._advanced.setVisible(False)
        adv_layout = QHBoxLayout(self._advanced)
        adv_layout.setContentsMargins(0, 0, 0, 0)
        adv_layout.setSpacing(16)

        # Left group: target subjects
        subj_group = QGroupBox("Subjects")
        subj_form = QFormLayout(subj_group)
        subj_form.setSpacing(4)

        self.field_target_subject = QLineEdit(self._config.target_subject)
        self.field_target_subject.setPlaceholderText("MES.TEST.OPI.MOD.NM")
        self.field_target_subject.setMinimumWidth(200)
        subj_form.addRow("Target:", self.field_target_subject)

        self.field_own_subject = QLineEdit(self._config.own_subject)
        self.field_own_subject.setPlaceholderText("MES.TEST.OPI.MOD.CM")
        self.field_own_subject.setMinimumWidth(200)
        subj_form.addRow("Own:", self.field_own_subject)
        adv_layout.addWidget(subj_group)

        # Middle group: protocol settings
        proto_group = QGroupBox("Protocol")
        proto_form = QFormLayout(proto_group)
        proto_form.setSpacing(4)

        self.field_timeout = QLineEdit(self._config.timeout)
        self.field_timeout.setFixedWidth(60)
        proto_form.addRow("Timeout (s):", self.field_timeout)

        self.field_encoding = QLineEdit(self._config.encoding_string)
        self.field_encoding.setFixedWidth(80)
        proto_form.addRow("Encoding:", self.field_encoding)

        self.field_field_name = QLineEdit(self._config.field_name)
        self.field_field_name.setFixedWidth(80)
        proto_form.addRow("Field:", self.field_field_name)

        self.field_mode = QLineEdit(self._config.mode)
        self.field_mode.setFixedWidth(80)
        proto_form.addRow("Mode:", self.field_mode)
        adv_layout.addWidget(proto_group)

        # Right: daemon list
        dm_group = QGroupBox("Daemon Failover")
        dm_layout = QVBoxLayout(dm_group)
        self.daemon_list_widget = QListWidget()
        self.daemon_list_widget.setMaximumHeight(80)
        dm_layout.addWidget(self.daemon_list_widget)
        adv_layout.addWidget(dm_group)

        adv_layout.addStretch()
        self._main_layout.addWidget(self._advanced)

    def _vsep(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setMaximumWidth(1)
        return sep

    def _toggle_expand(self):
        self._expanded = not self._expanded
        self._advanced.setVisible(self._expanded)
        self.btn_expand.setText("▾ Less" if self._expanded else "▸ More")

    def _add_env_presets(self):
        self._env_presets = {}
        presets_file = self._find_presets_file()
        if presets_file is None:
            return

        try:
            with open(presets_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        for entry in data:
            name = entry.get("name", "")
            if not name:
                continue
            c = ConnectionConfig(
                service=entry.get("service", ""),
                network=entry.get("network", ""),
                daemon=entry.get("daemon", ""),
                daemon_list=entry.get("daemon_list", [entry.get("daemon", "")]),
                target_subject=entry.get("target_subject", ""),
                own_subject=entry.get("own_subject", ""),
                timeout=entry.get("timeout", "20"),
                encoding_string=entry.get("encoding_string", "UTF-8"),
                mode=entry.get("mode", ""),
                target_subject_list=entry.get("target_subject_list", {}),
                listen_subject_list=entry.get("listen_subject_list", []),
            )
            self._env_presets[name] = c
            self.env_combo.addItem(name)

    @staticmethod
    def _find_presets_file():
        # Look next to this script, then in ~/.tibco-messenger/
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "presets.json"),
            os.path.expanduser("~/.tibco-messenger/presets.json"),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return os.path.normpath(p)
        return None

    def _on_env_changed(self, name: str):
        preset = self._env_presets.get(name)
        if preset is None:
            return
        self._config = preset
        self._sync_fields_from_config()

    def _sync_fields_from_config(self):
        self.field_service.setText(self._config.service)
        self.field_network.setText(self._config.network)
        self.field_daemon.setText(self._config.daemon)
        self.field_target_subject.setText(self._config.target_subject)
        self.field_own_subject.setText(self._config.own_subject)
        self.field_field_name.setText(self._config.field_name)
        self.field_timeout.setText(self._config.timeout)
        self.field_encoding.setText(self._config.encoding_string)
        self.field_mode.setText(self._config.mode)
        self.daemon_list_widget.clear()
        for d in self._config.daemon_list:
            self.daemon_list_widget.addItem(QListWidgetItem(d))
        self.config_changed.emit(self._config)

    def get_config(self) -> ConnectionConfig:
        c = ConnectionConfig()
        c.service = self.field_service.text().strip()
        c.network = self.field_network.text().strip()
        c.daemon = self.field_daemon.text().strip()
        c.target_subject = self.field_target_subject.text().strip()
        c.own_subject = self.field_own_subject.text().strip()
        c.field_name = self.field_field_name.text().strip()
        c.timeout = self.field_timeout.text().strip()
        c.encoding_string = self.field_encoding.text().strip()
        c.mode = self.field_mode.text().strip()
        daemon_text = self.field_daemon.text().strip()
        c.daemon_list = [d.strip() for d in daemon_text.split(",") if d.strip()]
        c.target_subject_list = self._config.target_subject_list
        c.listen_subject_list = self._config.listen_subject_list
        return c

    def set_config(self, config: ConnectionConfig):
        self._config = config
        self._sync_fields_from_config()

    def _on_test(self):
        from tibco_rv import is_available, get_load_error, TibcoRV
        if not is_available():
            QMessageBox.warning(self, "Tibco RV", f"Cannot test: {get_load_error()}")
            self.status_label.setText("No Tibco lib")
            self.status_dot.set_ok(False)
            return
        config = self.get_config()
        try:
            client = TibcoRV()
            client.open()
            client.create_transport(config.service, config.network, config.daemon)
            client.close()
            self.status_label.setText("Connected")
            self.status_dot.set_ok(True)
        except Exception as e:
            self.status_label.setText(str(e)[:40])
            self.status_dot.set_ok(False)

    def _on_load(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open config.xml", "", "XML Files (*.xml);;All Files (*)"
        )
        if not filepath:
            return
        from config_manager import load_config
        try:
            self.set_config(load_config(filepath))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load config:\n{e}")

    def _on_save(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save config.xml", "config.xml", "XML Files (*.xml);;All Files (*)"
        )
        if not filepath:
            return
        from config_manager import save_config
        try:
            save_config(filepath, self.get_config())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save config:\n{e}")
