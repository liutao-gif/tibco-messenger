"""Main application window."""

import re
import time
import threading

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QStatusBar, QMessageBox, QLabel, QPushButton, QInputDialog,
    QTabWidget, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models import ConnectionConfig
from widgets.connection_panel import ConnectionPanel
from widgets.message_editor import MessageEditor
from widgets.response_viewer import ResponseViewer
from widgets.message_library import MessageLibrary


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tibco Messenger")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        self._rv_client = None

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(8)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("status_info")
        self.status_bar.addWidget(self.status_label)

        self._init_tibco()

        # Connection panel at top (compact)
        self.connection_panel = ConnectionPanel()
        self.connection_panel.config_changed.connect(self._on_config_changed)
        root_layout.addWidget(self.connection_panel)

        # Main area: library | editor+response
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(1)

        # Left sidebar: message library
        self.message_library = MessageLibrary()
        self.message_library.template_selected.connect(self._on_template_selected)
        self.message_library.setMinimumWidth(200)
        self.message_library.setMaximumWidth(280)
        main_splitter.addWidget(self.message_library)

        # Right: Single Send tab + Batch Send tab
        from widgets.batch_panel import BatchPanel

        self.tab_widget = QTabWidget()

        # Tab 1: Single Send (editor + response)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.setHandleWidth(1)

        self.message_editor = MessageEditor()
        self.message_editor.send_requested.connect(self._on_send)
        self.message_editor.save_template_requested.connect(self._on_save_template)
        right_splitter.addWidget(self.message_editor)

        self.response_viewer = ResponseViewer()
        right_splitter.addWidget(self.response_viewer)

        right_splitter.setSizes([480, 260])

        self.tab_widget.addTab(right_splitter, "Single Send")

        # Tab 2: Batch Send
        self.batch_panel = BatchPanel()
        self.batch_panel.send_all_requested.connect(self._on_batch_send)
        self.tab_widget.addTab(self.batch_panel, "Batch Send")

        main_splitter.addWidget(self.tab_widget)
        main_splitter.setSizes([240, 940])

        root_layout.addWidget(main_splitter, 1)

        # Emit initial config
        self.connection_panel.config_changed.emit(self.connection_panel.get_config())

    def _init_tibco(self):
        from tibco_rv import is_available, get_load_error
        if is_available():
            from tibco_rv import TibcoRV
            self._rv_client = TibcoRV()
            self.status_label.setText("Ready")
        else:
            self._rv_client = None
            self.status_label.setText(f"Offline — {get_load_error()}")

    def _on_config_changed(self, config: ConnectionConfig):
        # Build subject keys — fallback to target_subject if list is empty
        subject_keys = dict(config.target_subject_list) if config.target_subject_list else {}
        if config.target_subject and not subject_keys:
            subject_keys["default"] = config.target_subject
        self.message_editor.set_subject_keys(subject_keys)
        self.batch_panel.set_subject_keys(subject_keys)
        if config.target_subject:
            self.message_editor.set_subject(config.target_subject)

    def _on_template_selected(self, template):
        self.message_editor.set_xml_body(template.xml_body)
        if template.target_subject_key:
            self.message_editor.set_subject(template.target_subject_key)

    def _on_save_template(self):
        name, ok = QInputDialog.getText(self, "Save Template", "Template name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        self.message_library.save_current(
            name=name,
            xml_body=self.message_editor.get_xml_body(),
            subject_key=self.message_editor.get_subject(),
        )
        self.status_label.setText(f"Template '{name}' saved.")

    def _on_batch_send(self, messages: list, mode: str, timeout: float):
        """Send all messages in a batch — group by thread_id, run groups in parallel."""
        if not messages:
            return

        config = self.connection_panel.get_config()

        # Group messages by thread_id
        groups: dict[str, list] = {}
        for i, msg in enumerate(messages):
            tid = msg.thread_id or "1"
            groups.setdefault(tid, []).append((i, msg))

        def _send_group(thread_id: str, items: list):
            """Send all messages in one thread group sequentially."""
            client = None
            try:
                from tibco_rv import TibcoRV
                client = TibcoRV()
                client.open()
                client.create_transport(config.service, config.network, config.daemon)

                for idx, msg in items:
                    try:
                        xml_body = msg.xml_body.lstrip("﻿").strip()
                        xml_body = re.sub(r'^<\?xml[^?]*\?>\s*', '', xml_body)

                        t0 = time.perf_counter()
                        if mode == "SendRequest":
                            reply = client.send_request(
                                msg.subject, config.own_subject, config.field_name, xml_body, timeout
                            )
                            elapsed = (time.perf_counter() - t0) * 1000
                            if reply:
                                self.batch_panel.emit_result(idx, True, response=reply)
                            else:
                                self.batch_panel.emit_result(idx, False, error=f"Timeout ({elapsed:.0f}ms)")
                        else:
                            client.send(msg.subject, config.field_name, xml_body)
                            elapsed = (time.perf_counter() - t0) * 1000
                            self.batch_panel.emit_result(idx, True, response=f"[T{thread_id}] Sent in {elapsed:.0f}ms")
                    except Exception as e:
                        self.batch_panel.emit_result(idx, False, error=str(e))
            except Exception as e:
                for idx, msg in items:
                    self.batch_panel.emit_result(idx, False, error=f"Connect: {e}")
            finally:
                try:
                    if client:
                        client.close()
                except Exception:
                    pass

        threads = []
        for tid, items in groups.items():
            t = threading.Thread(target=_send_group, args=(tid, items), daemon=True)
            t.start()
            threads.append(t)

        # Wait for all threads to finish
        for t in threads:
            t.join()

    def _on_send(self, subject: str, xml_body: str, timeout: float):
        if not subject:
            QMessageBox.warning(self, "Send", "Please specify a target subject.")
            return

        from tibco_rv import is_available
        if not is_available():
            QMessageBox.warning(
                self, "Tibco RV Not Available",
                "Tibco RV is not installed on this Mac.\n\n"
                "You can edit and save messages, but cannot send them."
            )
            return

        import re
        xml_body = xml_body.lstrip("﻿").strip()
        xml_body = re.sub(r'^<\?xml[^?]*\?>\s*', '', xml_body)

        if not xml_body:
            QMessageBox.warning(self, "Send", "Message body is empty.")
            return

        first_bytes = xml_body.encode("utf-8")[:20]
        hex_str = " ".join(f"{b:02x}" for b in first_bytes)
        preview = xml_body[:50].replace("\n", "\\n")
        print(f"[Tibco Messenger] Sending {len(xml_body)} chars [{hex_str}] -> {preview}...")

        config = self.connection_panel.get_config()
        mode = self.message_editor.mode_combo.currentText()
        xml_size = len(xml_body.encode("utf-8"))

        try:
            if self._rv_client is None:
                from tibco_rv import TibcoRV
                self._rv_client = TibcoRV()

            self._rv_client.open()
            self._rv_client.create_transport(config.service, config.network, config.daemon)

            if mode == "Send":
                t0 = time.perf_counter()
                self._rv_client.send(subject, config.field_name, xml_body)
                elapsed = (time.perf_counter() - t0) * 1000
                self.response_viewer.show_sent(xml_size)
                self.status_label.setText(f"Sent {xml_size} B to {subject} in {elapsed:.0f} ms")
            else:
                t0 = time.perf_counter()
                reply = self._rv_client.send_request(
                    subject, config.own_subject, config.field_name, xml_body, timeout
                )
                elapsed = (time.perf_counter() - t0) * 1000
                reply_size = len(reply.encode("utf-8")) if reply else 0
                self.response_viewer.show_response(reply, elapsed, reply_size)
                if reply:
                    self.status_label.setText(f"Reply {reply_size} B from {subject} in {elapsed:.0f} ms")
                else:
                    self.status_label.setText(f"Timeout from {subject} ({elapsed:.0f} ms)")

            self._rv_client.close()
        except Exception as e:
            self.response_viewer.show_error(str(e))
            self.status_label.setText(f"Failed: {e}")
            try:
                if self._rv_client:
                    self._rv_client.close()
            except Exception:
                pass
