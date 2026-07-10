# snmpweb

Web-basierter SNMP-Tester/Browser: GET/WALK gegen SNMP v1/v2c/v3-Agenten,
plus schneller TCP-Port-Check per nmap. Backend FastAPI (Python, async
pysnmp), Frontend Vanilla JS.

## Lokal starten

```bash
cd backend
pip install -r requirements.txt
export SNMPWEB_USER=admin
export SNMPWEB_PASSWORD=changeme
uvicorn main:app --reload
```

Danach [http://localhost:8000](http://localhost:8000) öffnen. Der Browser
fragt beim ersten API-Call automatisch per HTTP-Basic-Auth nach den obigen
Zugangsdaten.

## Deploy per Docker (Ziel: deksmoni12, 192.0.2.82)

```bash
cp .env.example .env
# .env anpassen: SNMPWEB_PASSWORD setzen
docker compose up -d --build
```

Läuft danach auf Port `8082` (siehe `docker-compose.yml`).

## Hinweise

- **Port-Scan** nutzt standardmäßig einen TCP-Connect-Scan (`-sT`), der ohne
  zusätzliche Capabilities im Container läuft. Für UDP-Scans (z.B. um Port
  161/162 selbst zu prüfen) müsste der Container mit `NET_RAW`/`NET_ADMIN`
  laufen (auskommentiert in `docker-compose.yml`) — deutlich langsamer und
  unzuverlässiger als TCP, daher nicht der Default.
- **MIB-Auflösung**: Es sind nur die mit pysnmp gebündelten Basis-MIBs
  (SNMPv2-MIB, RFC1213-MIB, SNMP-FRAMEWORK-MIB, …) verfügbar. Herstellerspezifische
  OIDs werden numerisch angezeigt. Bei Bedarf können weitere kompilierte
  MIB-Module später in `backend/mibs/` ergänzt werden.
- Das Tool selbst ist nur per Basic-Auth geschützt (ein gemeinsames
  Passwort) — kein Ersatz für ein Firewalling auf ein internes Netz.
