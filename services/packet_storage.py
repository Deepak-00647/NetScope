"""
Buffers parsed packet dicts and flushes them to the database in batches.
Batching avoids a DB write per packet, which would not keep up with real traffic.
"""
import threading
from models import db, Packet


class PacketStorage:
    def __init__(self, app, batch_size: int = 50):
        self.app = app
        self.batch_size = batch_size
        self._buffer = []
        self._lock = threading.Lock()

    def add(self, session_id: str, record: dict) -> Packet | None:
        """Buffer a record; flush automatically once batch_size is reached.
        Returns the constructed Packet object (uncommitted) for downstream use
        (e.g. threat detection) even before it hits the DB.
        """
        packet_obj_data = dict(record)
        packet_obj_data["session_id"] = session_id

        with self._lock:
            self._buffer.append(packet_obj_data)
            should_flush = len(self._buffer) >= self.batch_size

        if should_flush:
            self.flush()

        return packet_obj_data

    def flush(self) -> int:
        with self._lock:
            if not self._buffer:
                return 0
            batch = self._buffer
            self._buffer = []

        with self.app.app_context():
            try:
                db.session.bulk_insert_mappings(Packet, batch)
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
        return len(batch)
