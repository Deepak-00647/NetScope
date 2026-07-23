"""Persists alerts raised by the ThreatDetector."""
import threading
from models import db, Alert


class AlertManager:
    def __init__(self, app):
        self.app = app
        self._lock = threading.Lock()

    def raise_alert(self, session_id: str, alert_type: str, severity: str,
                     source_ip: str, description: str) -> None:
        with self._lock, self.app.app_context():
            alert = Alert(
                session_id=session_id,
                alert_type=alert_type,
                severity=severity,
                source_ip=source_ip,
                description=description,
            )
            db.session.add(alert)
            db.session.commit()
