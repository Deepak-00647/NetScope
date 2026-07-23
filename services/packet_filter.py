"""
Builds SQLAlchemy filter conditions for the packet search/filter UI.
Keeps query construction out of the routes layer.
"""
from datetime import datetime
from models import Packet


class PacketFilter:
    @staticmethod
    def apply(query, args: dict):
        ip = args.get("ip")
        if ip:
            query = query.filter((Packet.src_ip == ip) | (Packet.dst_ip == ip))

        port = args.get("port")
        if port:
            try:
                port = int(port)
                query = query.filter((Packet.src_port == port) | (Packet.dst_port == port))
            except ValueError:
                pass

        protocol = args.get("protocol")
        if protocol and protocol.upper() != "ALL":
            query = query.filter(Packet.protocol == protocol.upper())

        date_str = args.get("date")
        if date_str:
            try:
                day = datetime.strptime(date_str, "%Y-%m-%d").date()
                query = query.filter(db_date_match(Packet.timestamp, day))
            except ValueError:
                pass

        min_size = args.get("min_size")
        if min_size:
            try:
                query = query.filter(Packet.packet_size >= int(min_size))
            except ValueError:
                pass

        max_size = args.get("max_size")
        if max_size:
            try:
                query = query.filter(Packet.packet_size <= int(max_size))
            except ValueError:
                pass

        session_id = args.get("session_id")
        if session_id:
            query = query.filter(Packet.session_id == session_id)

        return query


def db_date_match(column, day):
    from sqlalchemy import func
    return func.date(column) == day.isoformat()
