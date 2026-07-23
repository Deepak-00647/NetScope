let rateChart, protoChart, topIpChart;
let pollTimer = null;
const chartsAvailable = typeof Chart !== "undefined";

function initCharts() {
  if (!chartsAvailable) {
    console.warn("Chart.js unavailable; continuing without chart rendering.");
    return false;
  }

  const gridColor = "rgba(255,255,255,0.05)";
  rateChart = new Chart(document.getElementById("chart-rate"), {
    type: "line",
    data: { labels: [], datasets: [{ label: "Packets/sec", data: [], borderColor: "#00e5a0", backgroundColor: "rgba(0,229,160,0.15)", fill: true, tension: 0.3 }] },
    options: { plugins: { legend: { display: false } }, scales: { x: { grid: { color: gridColor } }, y: { grid: { color: gridColor }, beginAtZero: true } } }
  });
  protoChart = new Chart(document.getElementById("chart-protocol"), {
    type: "pie",
    data: { labels: [], datasets: [{ data: [], backgroundColor: ["#00e5a0","#4d96ff","#ffb703","#ff4d6d","#9d4edd","#ff9f1c","#06d6a0","#118ab2"] }] },
    options: { plugins: { legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 10 } } } } }
  });
  topIpChart = new Chart(document.getElementById("chart-topips"), {
    type: "bar",
    data: { labels: [], datasets: [{ label: "Packets", data: [], backgroundColor: "#4d96ff" }] },
    options: { indexAxis: "y", plugins: { legend: { display: false } }, scales: { x: { grid: { color: gridColor } }, y: { grid: { display: false } } } }
  });
  return true;
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
  meta.textContent = data.interface ? `Interface: ${data.interface} | Packets: ${data.packet_count}` : "";
  const errBox = document.getElementById("capture-error");
  if (data.error) { errBox.textContent = data.error; errBox.classList.remove("d-none"); }
  else { errBox.classList.add("d-none"); }
}

async function refreshStats() {
  const data = await nsFetch("/api/stats");
  document.getElementById("stat-total").textContent = data.summary.total_packets.toLocaleString();
  document.getElementById("stat-pps").textContent = data.summary.packets_per_second;
  document.getElementById("stat-avgsize").textContent = data.summary.average_packet_size + " B";
  document.getElementById("stat-bandwidth").textContent = humanBytes(data.summary.total_bytes);

  const series = data.packet_rate_timeseries.slice(-30);
  if (chartsAvailable && rateChart && protoChart && topIpChart) {
    rateChart.data.labels = series.map(p => p.time.split(" ")[1] || p.time);
    rateChart.data.datasets[0].data = series.map(p => p.count);
    rateChart.update();

    protoChart.data.labels = data.protocol_distribution.map(p => p.protocol);
    protoChart.data.datasets[0].data = data.protocol_distribution.map(p => p.count);
    protoChart.update();

    topIpChart.data.labels = data.top_source_ips.map(p => p.ip);
    topIpChart.data.datasets[0].data = data.top_source_ips.map(p => p.count);
    topIpChart.update();
  }

  const portsBox = document.getElementById("top-ports-list");
  portsBox.innerHTML = data.top_ports.map(p => `<div class="mini-row"><span>Port ${p.port}</span><span>${p.count}</span></div>`).join("") || '<div class="text-secondary">No data yet</div>';
}

async function refreshAlerts() {
  const data = await nsFetch("/api/alerts");
  const box = document.getElementById("recent-alerts");
  const recent = data.alerts.slice(0, 8);
  box.innerHTML = recent.map(a => `
    <div class="alert-row">
      <span><span class="badge badge-severity-${a.severity}">${a.severity}</span> ${a.alert_type} — ${a.source_ip || "N/A"}</span>
      <span class="text-secondary">${new Date(a.timestamp).toLocaleTimeString()}</span>
    </div>`).join("") || '<div class="text-secondary">No alerts yet</div>';
}

function humanBytes(n) {
  const units = ["B","KB","MB","GB","TB"];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(2)} ${units[i]}`;
}

async function pollAll() {
  try {
    await Promise.all([refreshStatus(), refreshStats(), refreshAlerts()]);
  } catch (e) { console.error(e); }
}

document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  pollAll();
  pollTimer = setInterval(pollAll, 2000);

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
