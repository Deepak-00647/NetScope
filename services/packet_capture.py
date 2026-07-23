"""
Live packet capture engine.

Runs Scapy's sniff() in a background thread so the Flask request/response
cycle is never blocked. Capture state (running/paused/stopped, packet count)
is exposed for the dashboard to poll.

NOTE: Raw packet capture requires elevated privileges — on Windows this means
running VS Code / the terminal "as Administrator" and having Npcap installed;
on Linux/macOS it typically means running with sudo or granting the Python
interpreter CAP_NET_RAW.
"""
import threading
import time
import uuid
from datetime import datetime, timezone

from services.utils import setup_logger


class CaptureSession:
    """Holds the live/last state of one capture run for the UI to read."""

    def __init__(self):
        self.session_id = None
        self.interface = None
        self.status = "stopped"   # stopped | running | paused
        self.packet_count = 0
        self.started_at = None
        self.error = None

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "interface": self.interface,
            "status": self.status,
            "packet_count": self.packet_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "error": self.error,
        }


class PacketCaptureEngine:
    def __init__(self, app, storage, parser, threat_detector, config):
        self.app = app
        self.storage = storage
        self.parser = parser
        self.threat_detector = threat_detector
        self.cfg = config
        self.logger = setup_logger("packet_capture", config["LOG_DIR"])

        self.session = CaptureSession()
        self._thread = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()  # set == paused

    # -- public API -------------------------------------------------
    def list_interfaces(self):
        try:
            from scapy.arch.windows import get_windows_if_list
            windows_ifaces = get_windows_if_list()
            if windows_ifaces:
                names = []
                for entry in windows_ifaces:
                    name = entry.get("name")
                    if name:
                        names.append(name)
                return list(dict.fromkeys(names))
        except Exception:
            pass

        try:
            from scapy.all import get_if_list
            return get_if_list()
        except Exception as exc:
            self.logger.error("Failed to list interfaces: %s", exc)
            return []

    def start(self, interface: str):
        if self.session.status == "running":
            return False, "Capture already running"

        self.session = CaptureSession()
        self.session.session_id = uuid.uuid4().hex[:16]
        self.session.interface = interface
        self.session.status = "running"
        self.session.started_at = datetime.now(timezone.utc)
        self._stop_event.clear()
        self._pause_event.clear()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.logger.info("Capture started on %s (session=%s)", interface, self.session.session_id)
        return True, self.session.session_id

    def pause(self):
        if self.session.status != "running":
            return False, "Capture is not running"
        self._pause_event.set()
        self.session.status = "paused"
        return True, "Paused"

    def resume(self):
        if self.session.status != "paused":
            return False, "Capture is not paused"
        self._pause_event.clear()
        self.session.status = "running"
        return True, "Resumed"

    def stop(self):
        if self.session.status == "stopped":
            return False, "Capture is not running"
        self._stop_event.set()
        self._pause_event.clear()
        self.session.status = "stopped"
        self.storage.flush()
        self.logger.info("Capture stopped (session=%s, packets=%d)",
                          self.session.session_id, self.session.packet_count)
        return True, "Stopped"

    def status(self):
        return self.session.to_dict()

    # -- internals ----------------------------------------------------
    def _run(self):
        try:
            from scapy.all import sniff
        except Exception as exc:
            self.session.status = "stopped"
            self.session.error = f"Scapy unavailable: {exc}"
            self.logger.error(self.session.error)
            return

        def _on_packet(pkt):
            if self._stop_event.is_set():
                return
            while self._pause_event.is_set() and not self._stop_event.is_set():
                time.sleep(0.2)
            if self._stop_event.is_set():
                return
            record = self.parser.parse(pkt, self.session.interface)
            if record is None:
                return
            stored = self.storage.add(self.session.session_id, record)
            self.session.packet_count += 1
            try:
                self.threat_detector.process(stored)
            except Exception as exc:
                self.logger.error("Threat detection error: %s", exc)

            if self.session.packet_count >= self.cfg["MAX_PACKETS_PER_SESSION"]:
                self._stop_event.set()

        try:
            sniff(
                iface=self.session.interface,
                prn=_on_packet,
                store=False,
                stop_filter=lambda p: self._stop_event.is_set(),
            )
        except PermissionError:
            self.session.error = (
                "Permission denied opening the interface. Run VS Code / terminal "
                "as Administrator (Windows) or with sudo (Linux/macOS)."
            )
            self.logger.error(self.session.error)
        except Exception as exc:
            self.session.error = str(exc)
            self.logger.error("Capture error: %s", exc)
        finally:
            self.storage.flush()
            if self.session.status != "stopped":
                self.session.status = "stopped"
