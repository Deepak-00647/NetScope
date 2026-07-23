"""
Generates a PDF traffic/threat report for a capture session using ReportLab.
"""
import os
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

from models import db, Alert
from services.statistics import StatisticsService


class ReportGenerator:
    def __init__(self, report_dir: str):
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)

    def generate(self, session_id: str) -> str:
        stats = StatisticsService.summary(session_id)
        proto_dist = StatisticsService.protocol_distribution(session_id)
        top_src = StatisticsService.top_source_ips(session_id)
        top_dst = StatisticsService.top_destination_ips(session_id)
        top_ports = StatisticsService.top_ports(session_id)
        alerts = (
            db.session.query(Alert)
            .filter(Alert.session_id == session_id)
            .order_by(Alert.timestamp.desc())
            .all()
        )

        filename = f"netscope_report_{session_id}_{datetime.now(timezone.utc):%Y%m%d%H%M%S}.pdf"
        filepath = os.path.join(self.report_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#0d1b2a"))
        h2 = styles["Heading2"]
        normal = styles["BodyText"]

        story = []
        story.append(Paragraph("NetScope Traffic &amp; Threat Report", title_style))
        story.append(Paragraph(f"Session: {session_id}", normal))
        story.append(Paragraph(f"Generated: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}", normal))
        story.append(Spacer(1, 0.6 * cm))

        story.append(Paragraph("Traffic Summary", h2))
        summary_table = Table(
            [["Metric", "Value"]] + [
                ["Total Packets", stats["total_packets"]],
                ["Average Packet Size (bytes)", stats["average_packet_size"]],
                ["Total Bytes", stats["total_bytes"]],
                ["Packets / Second", stats["packets_per_second"]],
                ["Total Alerts", len(alerts)],
            ],
            colWidths=[9 * cm, 6 * cm],
        )
        summary_table.setStyle(self._table_style())
        story.append(summary_table)
        story.append(Spacer(1, 0.6 * cm))

        story.append(Paragraph("Protocol Distribution", h2))
        proto_rows = [["Protocol", "Packet Count"]] + [[p["protocol"], p["count"]] for p in proto_dist]
        proto_table = Table(proto_rows, colWidths=[9 * cm, 6 * cm])
        proto_table.setStyle(self._table_style())
        story.append(proto_table)
        story.append(Spacer(1, 0.6 * cm))

        story.append(Paragraph("Top Source IPs", h2))
        story.append(self._simple_table(["Source IP", "Count"], [[r["ip"], r["count"]] for r in top_src]))
        story.append(Spacer(1, 0.4 * cm))

        story.append(Paragraph("Top Destination IPs", h2))
        story.append(self._simple_table(["Destination IP", "Count"], [[r["ip"], r["count"]] for r in top_dst]))
        story.append(Spacer(1, 0.4 * cm))

        story.append(Paragraph("Top Ports", h2))
        story.append(self._simple_table(["Port", "Count"], [[r["port"], r["count"]] for r in top_ports]))

        story.append(PageBreak())
        story.append(Paragraph("Detected Threats / Alerts", h2))
        if alerts:
            alert_rows = [["Time (UTC)", "Type", "Severity", "Source IP", "Description"]]
            for a in alerts:
                alert_rows.append([
                    a.timestamp.strftime("%Y-%m-%d %H:%M:%S") if a.timestamp else "",
                    a.alert_type, a.severity, a.source_ip or "N/A",
                    Paragraph(a.description or "", normal),
                ])
            alert_table = Table(alert_rows, colWidths=[3.2 * cm, 2.8 * cm, 2 * cm, 3 * cm, 4.5 * cm])
            alert_table.setStyle(self._table_style())
            story.append(alert_table)
        else:
            story.append(Paragraph("No threats detected during this session.", normal))

        story.append(Spacer(1, 0.6 * cm))
        story.append(Paragraph("Recommendations", h2))
        for rec in self._recommendations(alerts):
            story.append(Paragraph(f"&bull; {rec}", normal))

        doc.build(story)
        return filepath

    @staticmethod
    def _recommendations(alerts) -> list[str]:
        if not alerts:
            return [
                "No anomalies observed in this capture window; continue routine monitoring.",
                "Periodically re-baseline normal traffic volume so future thresholds stay accurate.",
            ]
        types = {a.alert_type for a in alerts}
        recs = []
        if "PORT_SCAN" in types:
            recs.append("Investigate hosts flagged for port scanning; consider firewall rate-limiting.")
        if "SYN_FLOOD" in types:
            recs.append("Enable SYN cookies / rate limiting on exposed services to mitigate SYN floods.")
        if "ICMP_FLOOD" in types or "UDP_FLOOD" in types:
            recs.append("Apply ICMP/UDP rate limiting at the perimeter firewall.")
        if "SUSPICIOUS_PORT" in types:
            recs.append("Review access control lists for legacy/management ports contacted during capture.")
        recs.append("Correlate flagged source IPs against threat intelligence feeds before taking action.")
        return recs

    @staticmethod
    def _table_style() -> TableStyle:
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d1b2a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])

    def _simple_table(self, header, rows):
        data = [header] + (rows or [["-", "-"]])
        t = Table(data, colWidths=[9 * cm, 6 * cm])
        t.setStyle(self._table_style())
        return t
