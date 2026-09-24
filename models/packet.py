from datetime import datetime, timezone
from . import db


class Packet(db.Model):
    __tablename__ = "packets"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), index=True, nullable=False)
    # Stored as UTC. SQLite does not retain timezone metadata, so the API
    # explicitly marks timestamps as UTC before the browser converts them to
    # the user's local timezone.
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    interface = db.Column(db.String(64))
    protocol = db.Column(db.String(20), index=True)
    src_ip = db.Column(db.String(45), index=True)
    dst_ip = db.Column(db.String(45), index=True)
    src_mac = db.Column(db.String(17))
    dst_mac = db.Column(db.String(17))
    src_port = db.Column(db.Integer, index=True)
    dst_port = db.Column(db.Integer, index=True)
    packet_size = db.Column(db.Integer)
    ttl = db.Column(db.Integer)
    tcp_flags = db.Column(db.String(20))
    payload_length = db.Column(db.Integer)

    def to_dict(self) -> dict:
        timestamp = self.timestamp
        if timestamp is not None and timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return {
            "id": self.id,
            "timestamp": timestamp.isoformat().replace("+00:00", "Z") if timestamp else None,
            "interface": self.interface,
            "protocol": self.protocol,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_mac": self.src_mac,
            "dst_mac": self.dst_mac,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "packet_size": self.packet_size,
            "ttl": self.ttl,
            "tcp_flags": self.tcp_flags,
            "payload_length": self.payload_length,
        }
