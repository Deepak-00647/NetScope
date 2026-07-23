"""Page routes: dashboard, packets browser, alerts view, reports view."""
from flask import Blueprint, render_template, current_app
from flask_login import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    engine = current_app.extensions["netscope_capture_engine"]
    interfaces = engine.list_interfaces()
    return render_template("dashboard.html", interfaces=interfaces)


@dashboard_bp.route("/packets")
@login_required
def packets():
    return render_template("packets.html")


@dashboard_bp.route("/alerts")
@login_required
def alerts():
    return render_template("alerts.html")


@dashboard_bp.route("/reports")
@login_required
def reports():
    return render_template("reports.html")
