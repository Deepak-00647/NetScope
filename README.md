# NetScope

NetScope is a Python-based network packet analyzer and monitoring dashboard.
It captures live traffic with Scapy, classifies packets, stores session data,
tracks alerts, and renders a Flask-powered dashboard for monitoring and
report generation.

This is a defensive/monitoring tool for networks you own or are authorized
to monitor. Capturing traffic on a network without authorization may be
illegal in your jurisdiction.

## Requirements

- Windows 10/11, Linux, or macOS
- Python 3.12+
- Npcap on Windows for packet capture
- Administrator or root privileges for raw capture

## Setup

```bash
# From the NetScope/ folder
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
flask --app app.py create-admin <username> <email>
```

## Running the Application

Start the app from a terminal or VS Code window running as Administrator
(Windows) or with `sudo` (Linux/macOS):

```bash
python app.py
```

Then browse to `http://127.0.0.1:5000`.

## Using NetScope

1. Register or log in.
2. On the Dashboard, choose a network interface and press Start.
3. Watch live packet statistics, protocol distribution, and alert activity.
4. Review packet details under Packets.
5. Generate PDF reports from the Reports section.

## Project Structure

```text
NetScope/
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
- Dashboard analytics and alerting
- PDF report generation
- Search & filters by IP, port, protocol, date, packet size.
- Statistics: totals, packets/sec, protocol distribution, top source/dest
  IPs, top ports, average size, bandwidth.
- Charts: packet-rate line chart, protocol pie chart, top-IP bar chart.
- Threat detection: port scanning, SYN/ICMP/UDP floods, abnormal packet
  rate, large packet bursts, suspicious ports — each with severity and a
  cooldown to avoid alert spam.
- PDF reports via ReportLab with recommendations based on what was found.
- Security: CSRF protection (Flask-WTF), password hashing (Werkzeug),
  parameterized queries (SQLAlchemy ORM — no raw SQL string building),
  server-side input validation, structured logging with rotation,
  localhost-only binding.

## 8. Tuning Detection Thresholds

All thresholds live in `config.py` under `Config` (e.g.
`PORT_SCAN_UNIQUE_PORTS_THRESHOLD`, `SYN_FLOOD_THRESHOLD`,
`ABNORMAL_RATE_PPS_THRESHOLD`). Adjust them to match your network's normal
traffic volume before relying on alerts.

## 9. Troubleshooting

- **"Permission denied" / no interfaces listed**: run as Administrator/root;
  on Windows, confirm Npcap is installed.
- **No packets appearing**: verify you selected the interface that actually
  carries traffic (Wi-Fi vs Ethernet vs a virtual adapter).
- **Capture stops unexpectedly**: check `logs/packet_capture.log` for the
  underlying Scapy/OS error.

## 10. Future Improvements

- Role-based UI restrictions (admin-only interface/user management page)
- Export packets/alerts to CSV
- Configurable alert thresholds from the UI instead of `config.py`
- WebSocket-based push updates instead of polling
- GeoIP enrichment for source/destination IPs
- Packet payload hex/ASCII viewer with redaction of sensitive fields
>>>>>>> edd5af0 (Initial NetScope commit)
