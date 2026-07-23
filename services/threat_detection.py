"""
Lightweight, real-time heuristic threat detection.

Rather than querying the DB per-packet (too slow for live traffic), this
module keeps small in-memory sliding-window structures per source IP and
evaluates each rule as packets arrive. This is a signature/heuristic based
detector, not a full IDS — it flags patterns worth a human's attention.
"""
import threading
from collections import defaultdict, deque
from datetime import datetime, timezone


class ThreatDetector:
    def __init__(self, config, on_alert):
        """
        config: the Flask app config object (thresholds live there)
        on_alert: callback(alert_type, severity, source_ip, description)
        """
        self.cfg = config
        self.on_alert = on_alert
        self._lock = threading.Lock()

        # src_ip -> deque[(timestamp, dst_port)]  for port-scan detection
        self._port_touches = defaultdict(deque)
        # src_ip -> deque[timestamp] for SYN flood
        self._syn_times = defaultdict(deque)
        # src_ip -> deque[timestamp] for ICMP flood
        self._icmp_times = defaultdict(deque)
        # src_ip -> deque[timestamp] for UDP flood
        self._udp_times = defaultdict(deque)
        # src_ip -> deque[timestamp] for large-burst detection
        self._burst_times = defaultdict(deque)
        # global deque[timestamp] for overall pps
        self._global_times = deque()
        # suppress duplicate alerts per (type, ip) within cooldown
        self._last_fired = {}
        self._cooldown_seconds = 30

    def process(self, record: dict) -> None:
        now = datetime.now(timezone.utc)
        src_ip = record.get("src_ip")
        protocol = record.get("protocol")
        dport = record.get("dst_port")
        flags = record.get("tcp_flags") or ""
        size = record.get("packet_size") or 0

        with self._lock:
            self._global_times.append(now)
            self._trim(self._global_times, now, 1)
            pps = len(self._global_times)
            if pps > self.cfg["ABNORMAL_RATE_PPS_THRESHOLD"]:
                self._fire("ABNORMAL_RATE", "High", src_ip or "N/A",
                            f"Overall traffic rate spiked to ~{pps} packets/sec")

            if not src_ip:
                return

            if dport and protocol in ("TCP", "UDP") or dport:
                dq = self._port_touches[src_ip]
                dq.append((now, dport))
                self._trim_pairs(dq, now, self.cfg["PORT_SCAN_WINDOW_SECONDS"])
                unique_ports = {p for _, p in dq}
                if len(unique_ports) >= self.cfg["PORT_SCAN_UNIQUE_PORTS_THRESHOLD"]:
                    self._fire("PORT_SCAN", "High", src_ip,
                                f"{src_ip} touched {len(unique_ports)} distinct ports "
                                f"within {self.cfg['PORT_SCAN_WINDOW_SECONDS']}s")

            if protocol == "TCP" and "S" in flags and "A" not in flags:
                dq = self._syn_times[src_ip]
                dq.append(now)
                self._trim(dq, now, self.cfg["SYN_FLOOD_WINDOW_SECONDS"])
                if len(dq) >= self.cfg["SYN_FLOOD_THRESHOLD"]:
                    self._fire("SYN_FLOOD", "Critical", src_ip,
                                f"{src_ip} sent {len(dq)} SYN packets within "
                                f"{self.cfg['SYN_FLOOD_WINDOW_SECONDS']}s")

            if protocol == "ICMP":
                dq = self._icmp_times[src_ip]
                dq.append(now)
                self._trim(dq, now, self.cfg["ICMP_FLOOD_WINDOW_SECONDS"])
                if len(dq) >= self.cfg["ICMP_FLOOD_THRESHOLD"]:
                    self._fire("ICMP_FLOOD", "High", src_ip,
                                f"{src_ip} sent {len(dq)} ICMP packets within "
                                f"{self.cfg['ICMP_FLOOD_WINDOW_SECONDS']}s")

            if protocol == "UDP":
                dq = self._udp_times[src_ip]
                dq.append(now)
                self._trim(dq, now, self.cfg["UDP_FLOOD_WINDOW_SECONDS"])
                if len(dq) >= self.cfg["UDP_FLOOD_THRESHOLD"]:
                    self._fire("UDP_FLOOD", "High", src_ip,
                                f"{src_ip} sent {len(dq)} UDP packets within "
                                f"{self.cfg['UDP_FLOOD_WINDOW_SECONDS']}s")

            dq = self._burst_times[src_ip]
            dq.append(now)
            self._trim(dq, now, self.cfg["LARGE_BURST_WINDOW_SECONDS"])
            if len(dq) >= self.cfg["LARGE_BURST_PACKET_COUNT"]:
                self._fire("PACKET_BURST", "Medium", src_ip,
                            f"{src_ip} generated a burst of {len(dq)} packets within "
                            f"{self.cfg['LARGE_BURST_WINDOW_SECONDS']}s")

            if dport in self.cfg["SUSPICIOUS_PORTS"]:
                self._fire("SUSPICIOUS_PORT", "Medium", src_ip,
                            f"{src_ip} contacted commonly-abused port {dport}")

    def _fire(self, alert_type, severity, source_ip, description):
        key = (alert_type, source_ip)
        now = datetime.now(timezone.utc)
        last = self._last_fired.get(key)
        if last and (now - last).total_seconds() < self._cooldown_seconds:
            return
        self._last_fired[key] = now
        self.on_alert(alert_type, severity, source_ip, description)

    @staticmethod
    def _trim(dq: deque, now, window_seconds: int):
        while dq and (now - dq[0]).total_seconds() > window_seconds:
            dq.popleft()

    @staticmethod
    def _trim_pairs(dq: deque, now, window_seconds: int):
        while dq and (now - dq[0][0]).total_seconds() > window_seconds:
            dq.popleft()
