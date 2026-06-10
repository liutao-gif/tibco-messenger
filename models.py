"""Data models for Tibco Messenger."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ConnectionConfig:
    service: str = "7030"
    network: str = ""
    daemon: str = ""
    daemon_list: list[str] = field(default_factory=list)
    target_subject: str = ""
    target_subject_list: dict[str, str] = field(default_factory=dict)
    field_name: str = "DATA"
    own_subject: str = ""
    timeout: str = "20"
    encoding_string: str = "UTF-8"
    mode: str = "TEST"
    listen_subject_list: list[str] = field(default_factory=list)


@dataclass
class MessageTemplate:
    name: str = ""
    xml_body: str = ""
    target_subject_key: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BatchMessage:
    """A single message in a batch send."""
    subject: str = ""
    xml_body: str = ""
    response_text: str = ""
    thread_id: str = "1"

@dataclass
class SendResult:
    success: bool
    response: Optional[str] = None
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    message_size: int = 0
