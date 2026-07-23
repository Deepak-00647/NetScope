async function loadReports() {
  const data = await nsFetch("/api/reports/list");
  const tbody = document.getElementById("reports-table-body");
  tbody.innerHTML = data.reports.map(r => `
    <tr>
      <td>${r.filename}</td>
      <td>${r.created_at ? new Date(r.created_at).toLocaleString() : ""}</td>
      <td>${r.packet_count}</td>
      <td>${r.alert_count}</td>
      <td><a class="btn btn-sm btn-outline-light" href="/api/reports/download/${r.id}"><i class="fa-solid fa-download"></i> Download</a></td>
    </tr>`).join("") || `<tr><td colspan="5" class="text-center text-secondary">No reports yet</td></tr>`;
}

document.addEventListener("DOMContentLoaded", () => {
  loadReports();
  document.getElementById("btn-generate").addEventListener("click", async () => {
    const btn = document.getElementById("btn-generate");
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
    try {
      const res = await nsFetch("/api/reports/generate", { method: "POST", body: JSON.stringify({}) });
      if (!res.ok) alert(res.message || "Failed to generate report.");
      await loadReports();
    } catch (e) {
      alert("Failed to generate report: " + e.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-file-circle-plus"></i> Generate Report';
    }
  });
});
