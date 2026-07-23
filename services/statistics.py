"""
Aggregate statistics computed from stored packets for a given session.
"""
from sqlalchemy import func
from models import db, Packet


class StatisticsService:
    @staticmethod
    def summary(session_id: str) -> dict:
        base = db.session.query(Packet).filter(Packet.session_id == session_id)

        total_packets = base.count()
        avg_size = base.with_entities(func.avg(Packet.packet_size)).scalar() or 0
        total_bytes = base.with_entities(func.sum(Packet.packet_size)).scalar() or 0

        first_ts = base.with_entities(func.min(Packet.timestamp)).scalar()
        last_ts = base.with_entities(func.max(Packet.timestamp)).scalar()
        duration = (last_ts - first_ts).total_seconds() if first_ts and last_ts else 0
        pps = (total_packets / duration) if duration > 0 else 0

        return {
            "total_packets": total_packets,
            "average_packet_size": round(float(avg_size), 2),
            "total_bytes": int(total_bytes),
            "packets_per_second": round(pps, 2),
        }

    @staticmethod
    def protocol_distribution(session_id: str) -> list[dict]:
        rows = (
            db.session.query(Packet.protocol, func.count(Packet.id))
            .filter(Packet.session_id == session_id)
            .group_by(Packet.protocol)
            .order_by(func.count(Packet.id).desc())
            .all()
        )
        return [{"protocol": p or "UNKNOWN", "count": c} for p, c in rows]

    @staticmethod
    def top_source_ips(session_id: str, limit: int = 10) -> list[dict]:
        rows = (
            db.session.query(Packet.src_ip, func.count(Packet.id))
            .filter(Packet.session_id == session_id, Packet.src_ip.isnot(None))
            .group_by(Packet.src_ip)
            .order_by(func.count(Packet.id).desc())
            .limit(limit)
            .all()
        )
        return [{"ip": ip, "count": c} for ip, c in rows]

    @staticmethod
    def top_destination_ips(session_id: str, limit: int = 10) -> list[dict]:
        rows = (
            db.session.query(Packet.dst_ip, func.count(Packet.id))
            .filter(Packet.session_id == session_id, Packet.dst_ip.isnot(None))
            .group_by(Packet.dst_ip)
            .order_by(func.count(Packet.id).desc())
            .limit(limit)
            .all()
        )
        return [{"ip": ip, "count": c} for ip, c in rows]

    @staticmethod
    def top_ports(session_id: str, limit: int = 10) -> list[dict]:
        rows = (
            db.session.query(Packet.dst_port, func.count(Packet.id))
            .filter(Packet.session_id == session_id, Packet.dst_port.isnot(None))
            .group_by(Packet.dst_port)
            .order_by(func.count(Packet.id).desc())
            .limit(limit)
            .all()
        )
        return [{"port": p, "count": c} for p, c in rows]

    @staticmethod
    def packet_rate_timeseries(session_id: str) -> list[dict]:
        """Packets per second-bucket, for the line chart."""
        rows = (
            db.session.query(
                func.strftime("%Y-%m-%d %H:%M:%S", Packet.timestamp).label("bucket"),
                func.count(Packet.id),
            )
            .filter(Packet.session_id == session_id)
            .group_by("bucket")
            .order_by("bucket")
            .all()
        )
        return [{"time": b, "count": c} for b, c in rows]
