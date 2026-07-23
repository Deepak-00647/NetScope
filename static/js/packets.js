let currentPage = 1;

function buildQuery() {
  const params = new URLSearchParams();
  const ip = document.getElementById("f-ip").value.trim();
  const port = document.getElementById("f-port").value.trim();
  const protocol = document.getElementById("f-protocol").value;
  const date = document.getElementById("f-date").value;
  const minSize = document.getElementById("f-minsize").value;
  if (ip) params.set("ip", ip);
  if (port) params.set("port", port);
  if (protocol && protocol !== "ALL") params.set("protocol", protocol);
  if (date) params.set("date", date);
  if (minSize) params.set("min_size", minSize);
  params.set("page", currentPage);
  params.set("per_page", 50);
  return params.toString();
}

async function loadPackets() {
  const data = await nsFetch("/api/packets?" + buildQuery());
  const tbody = document.getElementById("packet-table-body");
  tbody.innerHTML = data.packets.map(p => `
    <tr>
      <td>${p.timestamp ? new Date(p.timestamp).toLocaleTimeString() : ""}</td>
      <td>${p.protocol || ""}</td>
      <td>${p.src_ip || ""}</td>
      <td>${p.src_port ?? ""}</td>
      <td>${p.dst_ip || ""}</td>
      <td>${p.dst_port ?? ""}</td>
      <td>${p.packet_size ?? ""}</td>
      <td>${p.ttl ?? ""}</td>
      <td>${p.tcp_flags || ""}</td>
    </tr>`).join("") || `<tr><td colspan="9" class="text-center text-secondary">No packets found</td></tr>`;

  renderPagination(data.total, data.per_page);
}

function renderPagination(total, perPage) {
  const totalPages = Math.max(Math.ceil(total / perPage), 1);
  const nav = document.getElementById("packet-pagination");
  let html = "";
  for (let p = 1; p <= totalPages && p <= 10; p++) {
    html += `<li class="page-item ${p === currentPage ? "active" : ""}"><a class="page-link" href="#" data-page="${p}">${p}</a></li>`;
  }
  nav.innerHTML = html;
  nav.querySelectorAll("a[data-page]").forEach(a => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      currentPage = parseInt(a.dataset.page, 10);
      loadPackets();
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadPackets();
  document.getElementById("btn-search").addEventListener("click", () => { currentPage = 1; loadPackets(); });
  setInterval(loadPackets, 5000);
});
