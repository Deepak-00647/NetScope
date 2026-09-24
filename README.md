# ShadowPacketGuard – Real-Time Network Packet Analysis and Threat Detection Platform

**ShadowPacketGuard** is a Python-based real-time network packet analysis and threat detection platform.
It captures live traffic with Scapy, classifies packets, stores session data,
tracks security alerts, and renders a Flask-powered dashboard for monitoring,
analysis, and report generation.

This is a defensive/monitoring tool for networks you own or are authorized
to monitor. Capturing traffic on a network without authorization may be illegal
in your jurisdiction.

## Requirements

- Windows 10/11, Linux, or macOS
- Python 3.12+
- Npcap on Windows for packet capture
- Administrator or root privileges for raw capture

## Setup

```bash
# From the project folder
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

## Database and Admin Account

The SQLite database and tables are created automatically on first run.
The first account registered through `/register` becomes the admin user.

You can also create an admin from the CLI:

```bash
flask --app app.py create-admin --username <username> --email <email> --password <password>
```

## Running the Application

Start the app from a terminal or VS Code window running as Administrator
(Windows) or with `sudo` (Linux/macOS):

```bash
python app.py
```

Then browse to `http://127.0.0.1:5000`.

## Using ShadowPacketGuard

1. Register or log in.
2. On the Dashboard, choose a network interface and press Start.
3. Watch live packet statistics, protocol distribution, source IPs, destination ports, and alert activity.
4. Review packet details under Packets.
5. Generate PDF traffic and threat reports from the Reports section.

## Project Structure

```text
ShadowPacketGuard/
  app.py
  config.py
  requirements.txt
  models/
  routes/
  services/
  templates/
  static/
  database/
  reports/
  logs/
```

## Features

- Flask authentication and roles
- Live packet capture
- Packet inspection and protocol detection
- Threat detection heuristics
- Real-time dashboard analytics and alerting
- PDF traffic/threat report generation
- Search and filters by IP, port, protocol, date, and packet size
- Statistics: totals, packets/sec, protocol distribution, top source/destination IPs,
  top ports, average packet size, and bandwidth
- Charts: packet-rate line chart, protocol pie chart, and top-source-IP bar chart
- Threat detection: port scanning, SYN/ICMP/UDP floods, abnormal packet rate,
  large packet bursts, and suspicious ports — each with severity and cooldown
  handling to reduce alert spam
- PDF reports via ReportLab with recommendations based on detected activity
- Security: CSRF protection (Flask-WTF), password hashing (Werkzeug),
  parameterized database access (SQLAlchemy ORM), server-side input validation,
  structured logging with rotation, and localhost-only binding

## Detection Threshold Tuning

All detection thresholds live in `config.py` under `Config` (for example,
`PORT_SCAN_UNIQUE_PORTS_THRESHOLD`, `SYN_FLOOD_THRESHOLD`, and
`ABNORMAL_RATE_PPS_THRESHOLD`). Adjust them to match the normal traffic volume
of the network being monitored before relying on alerts.

## Troubleshooting

- **Permission denied / no interfaces listed:** run as Administrator/root and,
  on Windows, confirm Npcap is installed correctly.
- **No packets appearing:** verify that the selected interface actually carries
  traffic (Wi-Fi, Ethernet, or the intended virtual adapter).
- **Capture stops unexpectedly:** check `logs/packet_capture.log` for the
  underlying Scapy/OS error.

## Future Improvements

- Role-based UI restrictions for administration pages
- Export packets and alerts to CSV
- Configurable alert thresholds from the UI
- WebSocket-based push updates instead of polling
- GeoIP enrichment for source/destination IPs
- Packet payload hex/ASCII viewer with redaction of sensitive fields
