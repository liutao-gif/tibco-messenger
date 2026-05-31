"""Tibco Rendezvous messaging — uses tibrvsend for Send, Java helper for SendRequest."""

import os
import sys
import glob as _glob
import subprocess
from typing import Optional


def _app_dir() -> str:
    """Get the application directory, works in dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _find_tool(name: str) -> Optional[str]:
    """Find a Tibco CLI tool."""
    candidates = []
    for pattern in ["/opt/tibco/tibrv/*/bin", "/opt/tibco/tibrv/bin"]:
        for d in sorted(_glob.glob(pattern), reverse=True):
            p = os.path.join(d, name)
            if os.path.isfile(p) and os.access(p, os.X_OK):
                candidates.append(p)
    import shutil
    p = shutil.which(name)
    if p:
        candidates.append(p)
    return candidates[0] if candidates else None


def _find_bin_dir() -> Optional[str]:
    for pattern in ["/opt/tibco/tibrv/*/bin", "/opt/tibco/tibrv/bin"]:
        dirs = sorted(_glob.glob(pattern), reverse=True)
        if dirs:
            return dirs[0]
    return None


def _find_java_request() -> Optional[str]:
    """Find the TibcoRequest Java class."""
    class_file = os.path.join(_app_dir(), "TibcoRequest.class")
    if os.path.isfile(class_file):
        return class_file
    return None


_send_bin: Optional[str] = None
_java_class: Optional[str] = None
_load_error: Optional[str] = None


def _init_tools():
    global _send_bin, _java_class, _load_error
    if _send_bin is not None:
        return
    _send_bin = _find_tool("tibrvsend")
    if _send_bin is None:
        _load_error = "tibrvsend not found. Please install Tibco Rendezvous."
    _java_class = _find_java_request()


def is_available() -> bool:
    _init_tools()
    return _send_bin is not None


def is_request_reply_available() -> bool:
    _init_tools()
    return _java_class is not None


def get_load_error() -> Optional[str]:
    _init_tools()
    return _load_error


def _tibco_env() -> dict:
    env = os.environ.copy()
    env["LANG"] = "en_US.UTF-8"
    env["LC_ALL"] = "en_US.UTF-8"
    return env


def _build_args(service: str, network: str, daemon: str) -> list:
    args = []
    if service:
        args.extend(["-service", service])
    if network:
        args.extend(["-network", network])
    if daemon:
        args.extend(["-daemon", daemon])
    return args


class TibcoRV:
    """Tibco RV client — uses CLI tools for Send, Java helper for SendRequest."""

    def __init__(self):
        _init_tools()
        self._service = ""
        self._network = ""
        self._daemon = ""

    def open(self) -> None:
        if _send_bin is None:
            raise RuntimeError(_load_error or "Tibco RV tools not available")

    def close(self) -> None:
        pass

    def create_transport(self, service: str, network: str, daemon: str) -> None:
        self._service = service
        self._network = network
        self._daemon = daemon
        try:
            result = subprocess.run(
                [_send_bin, "-service", service, "-network", network, "-daemon", daemon,
                 "_TEST._CONNECTION", ""],
                capture_output=True, text=True, timeout=5, env=_tibco_env()
            )
            if result.returncode != 0:
                raise RuntimeError(f"Connection test failed: {result.stderr.strip()}")
        except FileNotFoundError:
            raise RuntimeError(f"tibrvsend not found at {_send_bin}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Connection test timed out")

    def test_connection(self, service: str, network: str, daemon: str) -> bool:
        try:
            self.create_transport(service, network, daemon)
            return True
        except Exception:
            return False

    def send(self, subject: str, field_name: str, xml_body: str) -> None:
        """Send a fire-and-forget message via tibrvsend."""
        if _send_bin is None:
            raise RuntimeError(_load_error or "tibrvsend not available")
        args = _build_args(self._service, self._network, self._daemon)
        args.append(subject)
        args.append(xml_body)
        result = subprocess.run(
            [_send_bin] + args,
            capture_output=True, text=True, timeout=30, env=_tibco_env()
        )
        if result.returncode != 0:
            raise RuntimeError(f"Send failed: {result.stderr.strip()}")

    def send_request(
        self, subject: str, reply_subject: str, field_name: str, xml_body: str, timeout: float
    ) -> Optional[str]:
        """Send a request and wait for reply using Java TibcoRequest helper."""
        if _java_class is None:
            raise RuntimeError(
                "TibcoRequest.class not found. Build it with: "
                "javac -cp /opt/tibco/tibrv/8.7/lib/tibrvj.jar TibcoRequest.java"
            )

        my_dir = os.path.dirname(_find_java_request())
        tibrv_jar = None
        for p in _glob.glob("/opt/tibco/tibrv/*/lib/tibrvj.jar"):
            tibrv_jar = p
            break

        if tibrv_jar is None:
            raise RuntimeError("tibrvj.jar not found in Tibco installation")

        # Use shell wrapper to bypass macOS SIP stripping DYLD_LIBRARY_PATH
        script = os.path.join(my_dir, "tibco_request.sh")

        args = [
            script,
            self._service,
            self._network,
            self._daemon,
            subject,
            str(timeout),
            xml_body,
        ]

        result = subprocess.run(
            args,
            capture_output=True, text=True, timeout=timeout + 10
        )

        if result.returncode == 0:
            return result.stdout.strip()
        elif result.returncode == 2:
            # Timeout
            return None
        else:
            raise RuntimeError(f"Java request failed: {result.stderr.strip()}")
