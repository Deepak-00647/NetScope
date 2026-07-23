from datetime import datetime, timezone
from . import db


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), index=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    alert_type = db.Column(db.String(64), index=True)     # e.g. PORT_SCAN, SYN_FLOOD
    severity = db.Column(db.String(20), index=True)        # Low, Medium, High, Critical
    source_ip = db.Column(db.String(45), index=True)
    description = db.Column(db.Text)
    acknowledged = db.Column(db.Boolean, default=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "source_ip": self.source_ip,
            "description": self.description,
            "acknowledged": self.acknowledged,
        }
