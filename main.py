#!/usr/bin/env python3
"""Tibco Messenger — macOS desktop app for Tibco RV message testing.

Usage:
    python main.py
    python main.py --config path/to/config.xml
    python main.py --light      (light theme, default is dark)
"""

import sys
import argparse

from PyQt6.QtWidgets import QApplication
from theme import DARK_STYLE, LIGHT_STYLE


def main():
    parser = argparse.ArgumentParser(description="Tibco Messenger")
    parser.add_argument("--config", help="Path to config.xml to load on startup")
    parser.add_argument("--light", action="store_true", help="Use light theme (default: dark)")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Tibco Messenger")

    # Apply stylesheet
    if args.light:
        app.setStyleSheet(LIGHT_STYLE)
    else:
        app.setStyleSheet(DARK_STYLE)

    from app_window import MainWindow
    window = MainWindow()
    window.show()

    # Load config if provided
    if args.config:
        from config_manager import load_config
        try:
            config = load_config(args.config)
            window.connection_panel.set_config(config)
        except Exception as e:
            print(f"Warning: failed to load config: {e}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
