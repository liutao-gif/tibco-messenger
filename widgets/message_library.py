"""Message template library panel."""

import json
import os
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QInputDialog, QMessageBox, QGroupBox,
)
from PyQt6.QtCore import pyqtSignal, Qt
from models import MessageTemplate

TEMPLATES_FILE = os.path.expanduser("~/.tibco-messenger/messages.json")


class MessageLibrary(QGroupBox):
    template_selected = pyqtSignal(object)  # MessageTemplate
    template_deleted = pyqtSignal(str)  # template name

    def __init__(self, parent=None):
        super().__init__("Message Library", parent)
        self._templates: list[MessageTemplate] = []
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Button bar
        btn_row = QHBoxLayout()

        btn_new = QPushButton("New")
        btn_new.clicked.connect(self._on_new)
        btn_row.addWidget(btn_new)

        btn_rename = QPushButton("Rename")
        btn_rename.clicked.connect(self._on_rename)
        btn_row.addWidget(btn_rename)

        btn_delete = QPushButton("Delete")
        btn_delete.clicked.connect(self._on_delete)
        btn_row.addWidget(btn_delete)

        layout.addLayout(btn_row)

        # List
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_double_click)
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget, 1)

    def _on_new(self):
        name, ok = QInputDialog.getText(self, "New Template", "Template name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        # Check duplicate
        for t in self._templates:
            if t.name == name:
                QMessageBox.warning(self, "Duplicate", f"Template '{name}' already exists.")
                return

        template = MessageTemplate(name=name)
        self._templates.append(template)
        self._refresh_list()
        self._save()
        self.list_widget.setCurrentRow(len(self._templates) - 1)

    def _on_rename(self):
        item = self.list_widget.currentItem()
        if item is None:
            return
        old_name = item.text()
        name, ok = QInputDialog.getText(self, "Rename Template", "New name:", text=old_name)
        if not ok or not name.strip() or name.strip() == old_name:
            return
        name = name.strip()
        for t in self._templates:
            if t.name == old_name:
                t.name = name
                t.updated_at = datetime.now().isoformat()
                break
        self._refresh_list()
        self._save()

    def _on_delete(self):
        item = self.list_widget.currentItem()
        if item is None:
            return
        name = item.text()
        reply = QMessageBox.question(
            self, "Delete Template",
            f"Delete template '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._templates = [t for t in self._templates if t.name != name]
        self._refresh_list()
        self._save()
        self.template_deleted.emit(name)

    def _on_double_click(self, item: QListWidgetItem):
        name = item.text()
        for t in self._templates:
            if t.name == name:
                self.template_selected.emit(t)
                return

    def save_current(self, name: str, xml_body: str, subject_key: str):
        """Save or update the current editor content as a template."""
        for t in self._templates:
            if t.name == name:
                t.xml_body = xml_body
                t.target_subject_key = subject_key
                t.updated_at = datetime.now().isoformat()
                self._save()
                return
        # New template
        t = MessageTemplate(
            name=name, xml_body=xml_body,
            target_subject_key=subject_key,
        )
        self._templates.append(t)
        self._refresh_list()
        self._save()

    def get_template(self, name: str) -> Optional[MessageTemplate]:
        for t in self._templates:
            if t.name == name:
                return t
        return None

    def _refresh_list(self):
        self.list_widget.clear()
        for t in self._templates:
            item = QListWidgetItem(t.name)
            item.setToolTip(
                f"Subject: {t.target_subject_key or '(default)'}\n"
                f"Updated: {t.updated_at[:19]}\n"
                f"Size: {len(t.xml_body)} chars"
            )
            self.list_widget.addItem(item)

    def _save(self):
        os.makedirs(os.path.dirname(TEMPLATES_FILE), exist_ok=True)
        data = []
        for t in self._templates:
            data.append({
                "name": t.name,
                "xml_body": t.xml_body,
                "target_subject_key": t.target_subject_key,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            })
        with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self):
        if not os.path.exists(TEMPLATES_FILE):
            return
        try:
            with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._templates = [
                MessageTemplate(
                    name=d["name"],
                    xml_body=d.get("xml_body", ""),
                    target_subject_key=d.get("target_subject_key", ""),
                    created_at=d.get("created_at", datetime.now().isoformat()),
                    updated_at=d.get("updated_at", datetime.now().isoformat()),
                )
                for d in data
            ]
            self._refresh_list()
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load templates:\n{e}")
