from datetime import datetime, timezone
from . import db


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), index=True)
    generated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    packet_count = db.Column(db.Integer, default=0)
    alert_count = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "packet_count": self.packet_count,
            "alert_count": self.alert_count,
        }
