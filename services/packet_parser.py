"""
Parses raw Scapy packets into a normalized dict matching the Packet model.
Isolated from capture logic so it can be unit-tested without a live NIC.
"""
from datetime import datetime, timezone

try:
    from scapy.all import IP, IPv6, TCP, UDP, ICMP, ARP, Ether
except ImportError:  # scapy may be unavailable at import time in some envs
    IP = IPv6 = TCP = UDP = ICMP = ARP = Ether = None

WELL_KNOWN_PORTS = {
    20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "TELNET", 25: "SMTP",
    53: "DNS", 67: "DHCP", 68: "DHCP", 80: "HTTP", 110: "POP3",
    143: "IMAP", 443: "HTTPS", 3389: "RDP",
}


class PacketParser:
    """Turns a raw sniffed packet into structured metadata."""

    @staticmethod
    def _capture_timestamp(raw_packet, captured_at=None):
        """Return the live capture time in UTC.

        Npcap/Scapy timestamps can be represented differently across Windows
        capture backends. The capture engine therefore supplies the timestamp
        taken immediately when the packet callback fires. The Scapy timestamp
        remains the fallback for parser-only/test usage.
        """
        if captured_at is not None:
            if captured_at.tzinfo is None:
                return captured_at.replace(tzinfo=timezone.utc)
            return captured_at.astimezone(timezone.utc)

        try:
            return datetime.fromtimestamp(float(raw_packet.time), tz=timezone.utc)
        except (AttributeError, TypeError, ValueError, OSError):
            return datetime.now(timezone.utc)

    def parse(self, raw_packet, interface: str, captured_at=None) -> dict | None:
        try:
            record = {
                "timestamp": self._capture_timestamp(raw_packet, captured_at),
                "interface": interface,
                "protocol": "UNKNOWN",
                "src_ip": None,
                "dst_ip": None,
                "src_mac": None,
                "dst_mac": None,
                "src_port": None,
                "dst_port": None,
                "packet_size": len(raw_packet),
                "ttl": None,
                "tcp_flags": None,
                "payload_length": 0,
            }

            if Ether and raw_packet.haslayer(Ether):
                eth = raw_packet[Ether]
                record["src_mac"] = eth.src
                record["dst_mac"] = eth.dst

            if ARP and raw_packet.haslayer(ARP):
                arp = raw_packet[ARP]
                record["protocol"] = "ARP"
                record["src_ip"] = arp.psrc
                record["dst_ip"] = arp.pdst
                return record

            ip_layer = None
            if IP and raw_packet.haslayer(IP):
                ip_layer = raw_packet[IP]
                record["src_ip"] = ip_layer.src
                record["dst_ip"] = ip_layer.dst
                record["ttl"] = ip_layer.ttl
            elif IPv6 and raw_packet.haslayer(IPv6):
                ip_layer = raw_packet[IPv6]
                record["src_ip"] = ip_layer.src
                record["dst_ip"] = ip_layer.dst
                record["ttl"] = getattr(ip_layer, "hlim", None)

            if ip_layer is None:
                return record  # non-IP, non-ARP (e.g. STP) — keep size/mac only

            if TCP and raw_packet.haslayer(TCP):
                tcp = raw_packet[TCP]
                record["src_port"] = int(tcp.sport)
                record["dst_port"] = int(tcp.dport)
                record["tcp_flags"] = str(tcp.flags)
                record["payload_length"] = len(bytes(tcp.payload))

                payload = bytes(tcp.payload)
                if payload:
                    record["protocol"] = self._classify_payload(payload, tcp.sport, tcp.dport)
                else:
                    record["protocol"] = self._classify_port(tcp.sport, tcp.dport, "TCP")

            elif UDP and raw_packet.haslayer(UDP):
                udp = raw_packet[UDP]
                record["src_port"] = int(udp.sport)
                record["dst_port"] = int(udp.dport)
                record["payload_length"] = len(bytes(udp.payload))
                record["protocol"] = self._classify_port(udp.sport, udp.dport, "UDP")

            elif ICMP and raw_packet.haslayer(ICMP):
                record["protocol"] = "ICMP"
                record["payload_length"] = len(bytes(raw_packet[ICMP].payload))

            else:
                record["protocol"] = "IP"

            return record
        except Exception:
            return None

    @staticmethod
    def _classify_payload(payload: bytes, sport: int, dport: int) -> str:
        text = payload[:512].decode("latin-1", errors="ignore")
        if any(text.startswith(method) for method in (
            "GET ", "POST ", "PUT ", "PATCH ", "DELETE ", "HEAD ", "OPTIONS ", "TRACE ", "CONNECT ",
        )):
            return "HTTP"
        if text.startswith("HTTP/"):
            return "HTTP"
        if text.startswith("PRI * HTTP/2"):
            return "HTTP"

        return PacketParser._classify_port(sport, dport, "TCP")

    @staticmethod
    def _classify_port(sport: int, dport: int, transport: str) -> str:
        for p in (sport, dport):
            if p in WELL_KNOWN_PORTS:
                return WELL_KNOWN_PORTS[p]
        return transport
