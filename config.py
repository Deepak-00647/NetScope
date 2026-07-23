"""
Application configuration.
Loads settings from environment variables with safe local defaults.
"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core / Security ---
    SECRET_KEY = os.environ.get("NETSCOPE_SECRET_KEY", os.urandom(32).hex())
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "NETSCOPE_DB_URI",
        f"sqlite:///{os.path.join(BASE_DIR, 'database', 'netscope.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}

    # --- Paths ---
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    REPORT_DIR = os.path.join(BASE_DIR, "reports")

    # --- Capture ---
    # Safety valve so a runaway capture can't fill the DB/disk on a busy interface.
    MAX_PACKETS_PER_SESSION = int(os.environ.get("NETSCOPE_MAX_PACKETS", 200000))
    CAPTURE_BATCH_FLUSH_SIZE = 50  # packets buffered before a DB write

    # --- Threat detection thresholds (tunable) ---
    PORT_SCAN_UNIQUE_PORTS_THRESHOLD = 15   # distinct dst ports from one src within window
    PORT_SCAN_WINDOW_SECONDS = 10
    SYN_FLOOD_THRESHOLD = 100                # SYNs from one src within window
    SYN_FLOOD_WINDOW_SECONDS = 10
    ICMP_FLOOD_THRESHOLD = 50
    ICMP_FLOOD_WINDOW_SECONDS = 10
    UDP_FLOOD_THRESHOLD = 200
    UDP_FLOOD_WINDOW_SECONDS = 10
    ABNORMAL_RATE_PPS_THRESHOLD = 500        # overall packets/sec
    LARGE_BURST_PACKET_COUNT = 300           # packets in a 2s window from one src
    LARGE_BURST_WINDOW_SECONDS = 2
    SUSPICIOUS_PORTS = {23, 2323, 3389, 445, 135, 1433, 3306, 6379, 9200, 27017}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
