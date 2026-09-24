let rateChart = null;
let protoChart = null;
let topIpChart = null;
let pollTimer = null;

function getChartConstructor() {
  return typeof window.Chart === "function" ? window.Chart : null;
}

function initCharts() {
  const ChartCtor = getChartConstructor();
  const rateCanvas = document.getElementById("chart-rate");
  const protoCanvas = document.getElementById("chart-protocol");
  const topIpCanvas = document.getElementById("chart-topips");

  if (!rateCanvas || !protoCanvas || !topIpCanvas) {
    console.error("Dashboard chart canvas elements are missing.");
    return false;
  }

  // Prefer Chart.js, but keep the dashboard functional if the CDN is blocked.
  if (ChartCtor) {
    try {
      const gridColor = "rgba(255,255,255,0.05)";
      rateChart = new ChartCtor(rateCanvas, {
        type: "line",
        data: {
          labels: [],
          datasets: [{
            label: "Packets/sec",
            data: [],
            borderColor: "#00e5a0",
            backgroundColor: "rgba(0,229,160,0.15)",
            fill: true,
            tension: 0.3,
            pointRadius: 2,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: gridColor } },
            y: { grid: { color: gridColor }, beginAtZero: true },
          },
        },
      });

      protoChart = new ChartCtor(protoCanvas, {
        type: "pie",
        data: {
          labels: [],
          datasets: [{
            data: [],
            backgroundColor: ["#00e5a0", "#4d96ff", "#ffb703", "#ff4d6d", "#9d4edd", "#ff9f1c", "#06d6a0", "#118ab2"],
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          plugins: {
            legend: {
              position: "bottom",
              labels: { boxWidth: 10, font: { size: 10 } },
            },
          },
        },
      });

      topIpChart = new ChartCtor(topIpCanvas, {
        type: "bar",
        data: {
          labels: [],
          datasets: [{ label: "Packets", data: [], backgroundColor: "#4d96ff" }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          indexAxis: "y",
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: gridColor }, beginAtZero: true },
            y: { grid: { display: false } },
          },
        },
      });
      return true;
    } catch (error) {
      console.error("Chart.js initialization failed; using canvas fallback:", error);
      rateChart = protoChart = topIpChart = null;
    }
  } else {
    console.warn("Chart.js unavailable; using canvas fallback charts.");
  }

  return true;
}

function canvasSize(canvas) {
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(Math.floor(rect.width), 280);
  const height = 180;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  canvas.style.height = `${height}px`;
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { ctx, width, height };
}

function drawFallbackLine(canvas, points) {
  const { ctx, width, height } = canvasSize(canvas);
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.lineWidth = 1;
  for (let y = 25; y < height; y += 35) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
  }
  if (!points.length) return;
  const values = points.map(p => Number(p.count) || 0);
  const max = Math.max(...values, 1);
  const left = 8, right = width - 8, top = 12, bottom = height - 15;
  ctx.strokeStyle = "#00e5a0";
  ctx.lineWidth = 2;
  ctx.beginPath();
  values.forEach((value, i) => {
    const x = values.length === 1 ? (left + right) / 2 : left + (i * (right - left) / (values.length - 1));
    const y = bottom - (value / max) * (bottom - top);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function drawFallbackPie(canvas, rows) {
  const { ctx, width, height } = canvasSize(canvas);
  ctx.clearRect(0, 0, width, height);
  if (!rows.length) return;
  const values = rows.map(r => Number(r.count) || 0);
  const total = values.reduce((a, b) => a + b, 0) || 1;
  const cx = width / 2, cy = 78, radius = 58;
  const colors = ["#00e5a0", "#4d96ff", "#ffb703", "#ff4d6d", "#9d4edd", "#ff9f1c", "#06d6a0", "#118ab2"];
  let angle = -Math.PI / 2;
  values.forEach((value, i) => {
    const next = angle + (value / total) * Math.PI * 2;
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, radius, angle, next); ctx.closePath();
    ctx.fillStyle = colors[i % colors.length]; ctx.fill();
    angle = next;
  });
  ctx.fillStyle = "#d7e2ec";
  ctx.font = "11px Segoe UI";
  rows.slice(0, 5).forEach((row, i) => {
    const y = 145 + i * 13;
    ctx.fillStyle = colors[i % colors.length]; ctx.fillRect(8, y - 8, 8, 8);
    ctx.fillStyle = "#d7e2ec"; ctx.fillText(`${row.protocol}: ${row.count}`, 21, y);
  });
}

function drawFallbackBars(canvas, rows) {
  const { ctx, width, height } = canvasSize(canvas);
  ctx.clearRect(0, 0, width, height);
  if (!rows.length) return;
  const max = Math.max(...rows.map(r => Number(r.count) || 0), 1);
  const visible = rows.slice(0, 7);
  const rowHeight = Math.min(24, (height - 10) / visible.length);
  ctx.font = "11px Segoe UI";
  visible.forEach((row, i) => {
    const y = 6 + i * rowHeight;
    const barWidth = ((Number(row.count) || 0) / max) * (width - 95);
    ctx.fillStyle = "#4d96ff"; ctx.fillRect(85, y + 2, barWidth, rowHeight - 6);
    ctx.fillStyle = "#d7e2ec"; ctx.fillText(String(row.ip).slice(0, 13), 3, y + rowHeight - 8);
    ctx.fillText(String(row.count), Math.min(88 + barWidth, width - 30), y + rowHeight - 8);
  });
}

function updateCharts(data) {
  const series = Array.isArray(data.packet_rate_timeseries) ? data.packet_rate_timeseries.slice(-30) : [];
  const protocols = Array.isArray(data.protocol_distribution) ? data.protocol_distribution : [];
  const sourceIps = Array.isArray(data.top_source_ips) ? data.top_source_ips : [];

  if (rateChart && protoChart && topIpChart) {
    rateChart.data.labels = series.map(p => String(p.time || "").split(" ")[1] || p.time || "");
    rateChart.data.datasets[0].data = series.map(p => Number(p.count) || 0);
    rateChart.update("none");

    protoChart.data.labels = protocols.map(p => p.protocol || "UNKNOWN");
    protoChart.data.datasets[0].data = protocols.map(p => Number(p.count) || 0);
    protoChart.update("none");

    topIpChart.data.labels = sourceIps.map(p => p.ip || "N/A");
    topIpChart.data.datasets[0].data = sourceIps.map(p => Number(p.count) || 0);
    topIpChart.update("none");
    return;
  }

  drawFallbackLine(document.getElementById("chart-rate"), series);
  drawFallbackPie(document.getElementById("chart-protocol"), protocols);
  drawFallbackBars(document.getElementById("chart-topips"), sourceIps);
}

function setStatusBadge(status) {
  const badge = document.getElementById("capture-status-badge");
  badge.textContent = status.toUpperCase();
  badge.className = "ns-status-badge status-" + status;
}

function updateButtons(status) {
  document.getElementById("btn-start").disabled = status !== "stopped";
  document.getElementById("btn-pause").disabled = status !== "running";
  document.getElementById("btn-resume").disabled = status !== "paused";
  document.getElementById("btn-stop").disabled = status === "stopped";
}

async function refreshStatus() {
  const data = await nsFetch("/api/capture/status");
  setStatusBadge(data.status);
  updateButtons(data.status);
  const meta = document.getElementById("capture-meta");
  meta.textContent = data.interface ? `Interface: ${data.interface} | Packets: ${Number(data.packet_count || 0).toLocaleString()}` : "";
  const errBox = document.getElementById("capture-error");
  if (data.error) { errBox.textContent = data.error; errBox.classList.remove("d-none"); }
  else { errBox.classList.add("d-none"); }
}

async function refreshStats() {
  const data = await nsFetch("/api/stats");
  const summary = data.summary || {};
  document.getElementById("stat-total").textContent = Number(summary.total_packets || 0).toLocaleString();
  document.getElementById("stat-pps").textContent = Number(summary.packets_per_second || 0).toFixed(2);
  document.getElementById("stat-avgsize").textContent = Number(summary.average_packet_size || 0).toFixed(2) + " B";
  document.getElementById("stat-bandwidth").textContent = humanBytes(Number(summary.bandwidth_bytes_per_second || 0)) + "/s";

  updateCharts(data);

  const portsBox = document.getElementById("top-ports-list");
  const ports = Array.isArray(data.top_ports) ? data.top_ports : [];
  portsBox.innerHTML = ports.map(p => `<div class="mini-row"><span>Port ${p.port}</span><span>${p.count}</span></div>`).join("") || '<div class="text-secondary">No data yet</div>';
}

async function refreshAlerts() {
  const data = await nsFetch("/api/alerts");
  const box = document.getElementById("recent-alerts");
  const recent = (Array.isArray(data.alerts) ? data.alerts : []).slice(0, 8);
  box.innerHTML = recent.map(a => `
    <div class="alert-row">
      <span><span class="badge badge-severity-${a.severity}">${a.severity}</span> ${a.alert_type} — ${a.source_ip || "N/A"}</span>
      <span class="text-secondary">${new Date(a.timestamp).toLocaleTimeString()}</span>
    </div>`).join("") || '<div class="text-secondary">No alerts yet</div>';
}

function humanBytes(n) {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(2)} ${units[i]}`;
}

async function pollAll() {
  try {
    await Promise.all([refreshStatus(), refreshStats(), refreshAlerts()]);
  } catch (e) { console.error("Dashboard refresh failed:", e); }
}

document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  pollAll();
  pollTimer = setInterval(pollAll, 1000);

  window.addEventListener("resize", () => {
    if (!rateChart) {
      const last = window.__netscope_last_stats;
      if (last) updateCharts(last);
    }
  });

  document.getElementById("btn-start").addEventListener("click", async () => {
    const iface = document.getElementById("interface-select").value;
    if (!iface) { alert("Select an interface first."); return; }
    await nsFetch("/api/capture/start", { method: "POST", body: JSON.stringify({ interface: iface }) });
    pollAll();
  });
  document.getElementById("btn-pause").addEventListener("click", async () => { await nsFetch("/api/capture/pause", { method: "POST" }); pollAll(); });
  document.getElementById("btn-resume").addEventListener("click", async () => { await nsFetch("/api/capture/resume", { method: "POST" }); pollAll(); });
  document.getElementById("btn-stop").addEventListener("click", async () => { await nsFetch("/api/capture/stop", { method: "POST" }); pollAll(); });
});
