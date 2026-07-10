const $ = (id) => document.getElementById(id);
const statusEl = $("status");

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.classList.toggle("error", isError);
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

async function callApi(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch (_) {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

function renderRows(tableId, rows, columns) {
  const tbody = document.querySelector(`#${tableId} tbody`);
  tbody.innerHTML = "";
  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = columns.map((c) => `<td>${row[c] ?? ""}</td>`).join("");
    tbody.appendChild(tr);
  }
}

$("btn-get").addEventListener("click", async () => {
  const oid = $("oid").value.trim();
  if (!oid) return setStatus("Bitte eine OID angeben.", true);
  setStatus("GET läuft…");
  try {
    const rows = await callApi("/api/snmp/get", { ...currentTarget(), oids: [oid] });
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
    const rows = await callApi("/api/snmp/walk", { ...currentTarget(), oid });
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
    const rows = await callApi("/api/portscan", { host, ports: $("ports").value.trim() });
    renderRows("scan-result", rows, ["port", "protocol", "state", "service"]);
    setStatus(`${rows.length} Port(s) gefunden.`);
  } catch (e) {
    setStatus(e.message, true);
  }
});
