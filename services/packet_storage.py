"""
Buffers parsed packet dicts and flushes them to the database in batches.

Packets are still batched for throughput, but a background flush keeps the
stored data close to real time so dashboard statistics do not wait for a full
batch during low-volume traffic.
"""
import threading
import time

from models import db, Packet


class PacketStorage:
    def __init__(self, app, batch_size: int = 50, flush_interval: float = 0.5):
        self.app = app
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._buffer = []
        self._lock = threading.Lock()
        self._flush_stop = threading.Event()
        self._flush_thread = threading.Thread(
            target=self._flush_loop,
            name="netscope-db-flusher",
            daemon=True,
        )
        self._flush_thread.start()

    def add(self, session_id: str, record: dict) -> Packet | None:
        """Buffer a record and flush when the batch or timer requires it."""
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
                # Put the batch back so a transient DB error does not silently
                # discard captured packets.
                with self._lock:
                    self._buffer = batch + self._buffer
                raise
        return len(batch)

    def _flush_loop(self):
        """Flush small batches periodically for near-real-time dashboard data."""
        while not self._flush_stop.wait(self.flush_interval):
            try:
                self.flush()
            except Exception:
                # Capture thread/logging will report operational errors. Keep
                # the flusher alive so the next interval can retry.
                pass

    def stop(self):
        """Stop the background flusher and persist any remaining packets."""
        self._flush_stop.set()
        if self._flush_thread.is_alive():
            self._flush_thread.join(timeout=max(1.0, self.flush_interval * 2))
        self.flush()
