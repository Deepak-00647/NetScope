"""Capture control endpoints (start/pause/resume/stop/status)."""
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required

capture_bp = Blueprint("capture", __name__, url_prefix="/api/capture")


def _engine():
    return current_app.extensions["netscope_capture_engine"]


@capture_bp.route("/interfaces")
@login_required
def interfaces():
    return jsonify({"interfaces": _engine().list_interfaces()})


@capture_bp.route("/start", methods=["POST"])
@login_required
def start():
    data = request.get_json(silent=True) or {}
    interface = data.get("interface")
    if not interface:
        return jsonify({"ok": False, "message": "interface is required"}), 400
    ok, msg = _engine().start(interface)
    return jsonify({"ok": ok, "message": msg, "status": _engine().status()})


@capture_bp.route("/pause", methods=["POST"])
@login_required
def pause():
    ok, msg = _engine().pause()
    return jsonify({"ok": ok, "message": msg, "status": _engine().status()})


@capture_bp.route("/resume", methods=["POST"])
@login_required
def resume():
    ok, msg = _engine().resume()
    return jsonify({"ok": ok, "message": msg, "status": _engine().status()})


@capture_bp.route("/stop", methods=["POST"])
@login_required
def stop():
    ok, msg = _engine().stop()
    return jsonify({"ok": ok, "message": msg, "status": _engine().status()})


@capture_bp.route("/status")
@login_required
def status():
    return jsonify(_engine().status())
