"""XML config file reader/writer — compatible with the project's config.xml format."""

import os
import xml.etree.ElementTree as ET
from models import ConnectionConfig


def load_config(filepath: str) -> ConnectionConfig:
    """Load connection config from a config.xml file."""
    tree = ET.parse(filepath)
    root = tree.getroot()

    config = ConnectionConfig()

    def get_text(tag: str) -> str:
        el = root.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    config.service = get_text("Service")
    config.network = get_text("Network")
    config.target_subject = get_text("TargetSubject")
    config.field_name = get_text("FieldName") or "DATA"
    config.own_subject = get_text("OwnSubject")
    config.timeout = get_text("TimeOut") or "20"
    config.encoding_string = get_text("EncodingString") or "UTF-8"
    config.mode = get_text("Mode") or "TEST"

    # DaemonList
    daemon_list_node = root.find("DaemonList")
    config.daemon_list = []
    if daemon_list_node is not None:
        for child in daemon_list_node:
            if child.text and child.text.strip():
                config.daemon_list.append(child.text.strip())
    config.daemon = config.daemon_list[0] if config.daemon_list else ""

    # TargetSubjectList (named targets)
    tsl_node = root.find("TargetSubjectList")
    config.target_subject_list = {}
    if tsl_node is not None:
        for ts_node in tsl_node.findall("TargetSubject"):
            name_el = ts_node.find("Name")
            subject_el = ts_node.find("Subject")
            if name_el is not None and subject_el is not None:
                config.target_subject_list[name_el.text.strip()] = subject_el.text.strip()

    # ListenSubjectList
    lsl_node = root.find("ListenSubjectList")
    config.listen_subject_list = []
    if lsl_node is not None:
        for child in lsl_node:
            if child.text and child.text.strip():
                config.listen_subject_list.append(child.text.strip())

    return config


def save_config(filepath: str, config: ConnectionConfig) -> None:
    """Save connection config to a config.xml file."""
    root = ET.Element("ConnectionInfo")

    def add_element(parent, tag, text):
        el = ET.SubElement(parent, tag)
        el.text = text

    add_element(root, "Service", config.service)
    add_element(root, "Network", config.network)
    add_element(root, "EncodingString", config.encoding_string)
    add_element(root, "TargetSubject", config.target_subject)
    add_element(root, "FieldName", config.field_name)
    add_element(root, "TimeOut", config.timeout)
    add_element(root, "OwnSubject", config.own_subject)
    add_element(root, "Mode", config.mode)

    # DaemonList
    dl_node = ET.SubElement(root, "DaemonList")
    for d in config.daemon_list:
        add_element(dl_node, "Daemon", d)

    # TargetSubjectList
    if config.target_subject_list:
        tsl_node = ET.SubElement(root, "TargetSubjectList")
        for name, subject in config.target_subject_list.items():
            ts_node = ET.SubElement(tsl_node, "TargetSubject")
            add_element(ts_node, "Name", name)
            add_element(ts_node, "Subject", subject)

    # ListenSubjectList
    if config.listen_subject_list:
        lsl_node = ET.SubElement(root, "ListenSubjectList")
        for s in config.listen_subject_list:
            add_element(lsl_node, "Subject", s)

    # Pretty-print
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)
