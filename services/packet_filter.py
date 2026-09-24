"""
Builds SQLAlchemy filter conditions for the packet search/filter UI.
Keeps query construction out of the routes layer.
"""
from datetime import datetime, timedelta, timezone
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
                # Browser sends UTC offset in minutes (UTC - local). Convert
                # the user's local calendar day into a UTC half-open range.
                tz_offset = int(args.get("tz_offset", "0"))
                query = query.filter(db_local_date_match(Packet.timestamp, day, tz_offset))
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


def db_local_date_match(column, day, tz_offset_minutes=0):
    """Match a browser-local date against UTC timestamps stored by SQLite."""
    from sqlalchemy import and_

    local_start = datetime.combine(day, datetime.min.time())
    local_end = local_start + timedelta(days=1)
    utc_start = local_start + timedelta(minutes=tz_offset_minutes)
    utc_end = local_end + timedelta(minutes=tz_offset_minutes)

    return and_(
        column >= utc_start,
        column < utc_end,
    )


# Backward-compatible helper name for callers/tests that imported it directly.
def db_date_match(column, day):
    return db_local_date_match(column, day, 0)
