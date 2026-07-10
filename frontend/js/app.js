const $ = (id) => document.getElementById(id);
const statusEl = $("status");

let currentRole = null;

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.classList.toggle("error", isError);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[c]);
}

function currentTarget() {
  const version = $("version").value;
  const target = {
    host: $("host").value.trim(),
    port: Number($("port").value) || 161,
    version,
  };
  if (version === "v3") {
    target.username = $("v3-username").value;
    target.auth_protocol = $("v3-auth-protocol").value;
    target.auth_password = $("v3-auth-password").value;
    target.priv_protocol = $("v3-priv-protocol").value;
    target.priv_password = $("v3-priv-password").value;
  } else {
    target.community = $("community").value;
  }
  return target;
}

function toggleVersionFields() {
  const isV3 = $("version").value === "v3";
  $("v3-fields").classList.toggle("hidden", !isV3);
  $("v12-fields").classList.toggle("hidden", isV3);
}
$("version").addEventListener("change", toggleVersionFields);
toggleVersionFields();

async function callApi(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch (_) {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

function callJsonApi(path, body) {
  return callApi(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function renderRows(tableId, rows, columns) {
  const tbody = document.querySelector(`#${tableId} tbody`);
  tbody.innerHTML = "";
  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = columns.map((c) => `<td>${escapeHtml(row[c])}</td>`).join("");
    tbody.appendChild(tr);
  }
  return tbody;
}

$("btn-get").addEventListener("click", async () => {
  const oid = $("oid").value.trim();
  if (!oid) return setStatus("Bitte eine OID angeben.", true);
  setStatus("GET läuft…");
  try {
    const rows = await callJsonApi("/api/snmp/get", { ...currentTarget(), oids: [oid] });
    renderRows("snmp-result", rows, ["oid", "name", "type", "value"]);
    setStatus(`${rows.length} Ergebnis(se).`);
  } catch (e) {
    setStatus(e.message, true);
  }
});

$("btn-walk").addEventListener("click", async () => {
  const oid = $("oid").value.trim();
  if (!oid) return setStatus("Bitte eine OID angeben.", true);
  setStatus("WALK läuft…");
  try {
    const rows = await callJsonApi("/api/snmp/walk", { ...currentTarget(), oid });
    renderRows("snmp-result", rows, ["oid", "name", "type", "value"]);
    setStatus(`${rows.length} Ergebnis(se).`);
  } catch (e) {
    setStatus(e.message, true);
  }
});

$("btn-scan").addEventListener("click", async () => {
  const host = $("host").value.trim();
  if (!host) return setStatus("Bitte einen Host angeben.", true);
  setStatus("Scan läuft…");
  try {
    const rows = await callJsonApi("/api/portscan", { host, ports: $("ports").value.trim() });
    renderRows("scan-result", rows, ["port", "protocol", "state", "service"]);
    setStatus(`${rows.length} Port(s) gefunden.`);
  } catch (e) {
    setStatus(e.message, true);
  }
});

async function loadMibs() {
  const rows = await callApi("/api/mibs");
  const tbody = renderRows(
    "mib-result",
    rows.map((r) => ({ ...r, compiled: r.compiled ? "ja" : "nein" })),
    ["name", "compiled"]
  );
  if (currentRole === "admin") {
    [...tbody.rows].forEach((tr, i) => {
      const td = document.createElement("td");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Löschen";
      btn.addEventListener("click", () => deleteMib(rows[i].name));
      td.appendChild(btn);
      tr.appendChild(td);
    });
  }
}

async function deleteMib(name) {
  setStatus(`Lösche MIB ${name}…`);
  try {
    await callApi(`/api/mibs/${encodeURIComponent(name)}`, { method: "DELETE" });
    setStatus(`MIB ${name} gelöscht.`);
    await loadMibs();
  } catch (e) {
    setStatus(e.message, true);
  }
}

const mibUploadBtn = $("btn-mib-upload");
if (mibUploadBtn) {
  mibUploadBtn.addEventListener("click", async () => {
    const fileInput = $("mib-file");
    const file = fileInput.files[0];
    if (!file) return setStatus("Bitte eine MIB-Datei auswählen.", true);
    setStatus("MIB wird hochgeladen und kompiliert…");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const result = await callApi("/api/mibs", { method: "POST", body: formData });
      setStatus(`MIB ${result.name} kompiliert.`);
      fileInput.value = "";
      await loadMibs();
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

async function loadAudit() {
  const rows = await callApi("/api/audit?limit=200");
  renderRows(
    "audit-result",
    rows.map((r) => ({ ...r, success: r.success ? "ja" : "nein" })),
    ["ts", "username", "action", "host", "target", "success", "detail"]
  );
}

const auditRefreshBtn = $("btn-audit-refresh");
if (auditRefreshBtn) {
  auditRefreshBtn.addEventListener("click", () => loadAudit().catch((e) => setStatus(e.message, true)));
}

async function init() {
  try {
    const who = await callApi("/api/whoami");
    currentRole = who.role;
    $("whoami").textContent = `Angemeldet als ${who.username} (${who.role})`;

    if (who.role === "admin") {
      $("mib-upload-row").classList.remove("hidden");
      $("mib-upload-actions").classList.remove("hidden");
      $("mib-action-header").classList.remove("hidden");
      $("audit-panel").classList.remove("hidden");
      loadAudit().catch(() => {});
    }
    await loadMibs();
  } catch (e) {
    setStatus(e.message, true);
  }
}

init();
