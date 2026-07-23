"""Report generation and download endpoints."""
import os
from flask import Blueprint, jsonify, request, current_app, send_from_directory
from flask_login import login_required, current_user

from models import db, Report, Alert, Packet

reports_bp = Blueprint("reports_api", __name__, url_prefix="/api/reports")


@reports_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    data = request.get_json(silent=True) or {}
    sid = data.get("session_id")
    if not sid:
        engine = current_app.extensions["netscope_capture_engine"]
        sid = engine.session.session_id
    if not sid:
        return jsonify({"ok": False, "message": "No capture session available to report on."}), 400

    generator = current_app.extensions["netscope_report_generator"]
    filepath = generator.generate(sid)
    filename = os.path.basename(filepath)

    packet_count = db.session.query(Packet).filter(Packet.session_id == sid).count()
    alert_count = db.session.query(Alert).filter(Alert.session_id == sid).count()

    report = Report(
        session_id=sid,
        generated_by=current_user.id,
        filename=filename,
        packet_count=packet_count,
        alert_count=alert_count,
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({"ok": True, "report": report.to_dict()})


@reports_bp.route("/list")
@login_required
def list_reports():
    rows = db.session.query(Report).order_by(Report.id.desc()).all()
    return jsonify({"reports": [r.to_dict() for r in rows]})


@reports_bp.route("/download/<int:report_id>")
@login_required
def download(report_id):
    report = db.get_or_404(Report, report_id)
    report_dir = current_app.config["REPORT_DIR"]
    return send_from_directory(report_dir, report.filename, as_attachment=True)
