"""JSON data endpoints powering the dashboard's AJAX/Chart.js views."""
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required

from models import db, Packet, Alert
from services.packet_filter import PacketFilter
from services.statistics import StatisticsService

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _session_id():
    """Resolve which session's data to show: explicit param, else the active
    capture engine's session, else the most recent session in the DB."""
    sid = request.args.get("session_id")
    if sid:
        return sid
    engine = current_app.extensions["netscope_capture_engine"]
    if engine.session.session_id:
        return engine.session.session_id
    last = db.session.query(Packet.session_id).order_by(Packet.id.desc()).first()
    return last[0] if last else None


@api_bp.route("/packets")
@login_required
def packets():
    sid = _session_id()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(int(request.args.get("per_page", 50)), 200)

    query = db.session.query(Packet)
    if sid:
        query = query.filter(Packet.session_id == sid)
    query = PacketFilter.apply(query, request.args)
    query = query.order_by(Packet.id.desc())

    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "session_id": sid,
        "page": page,
        "per_page": per_page,
        "total": total,
        "packets": [p.to_dict() for p in rows],
    })


@api_bp.route("/alerts")
@login_required
def alerts():
    sid = _session_id()
    query = db.session.query(Alert)
    if sid:
        query = query.filter(Alert.session_id == sid)
    severity = request.args.get("severity")
    if severity and severity.upper() != "ALL":
        query = query.filter(Alert.severity == severity.capitalize())
    rows = query.order_by(Alert.id.desc()).limit(500).all()
    return jsonify({"session_id": sid, "alerts": [a.to_dict() for a in rows]})


@api_bp.route("/stats")
@login_required
def stats():
    sid = _session_id()
    if not sid:
        return jsonify({
            "summary": {
                "total_packets": 0,
                "average_packet_size": 0,
                "total_bytes": 0,
                "packets_per_second": 0,
                "bandwidth_bytes_per_second": 0,
            },
            "protocol_distribution": [], "top_source_ips": [], "top_destination_ips": [],
            "top_ports": [], "packet_rate_timeseries": [], "session_id": None,
        })
    return jsonify({
        "session_id": sid,
        "summary": StatisticsService.summary(sid),
        "protocol_distribution": StatisticsService.protocol_distribution(sid),
        "top_source_ips": StatisticsService.top_source_ips(sid),
        "top_destination_ips": StatisticsService.top_destination_ips(sid),
        "top_ports": StatisticsService.top_ports(sid),
        "packet_rate_timeseries": StatisticsService.packet_rate_timeseries(sid),
    })
