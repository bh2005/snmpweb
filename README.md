# snmpweb

Web-basierter SNMP-Tester/Browser: GET/WALK gegen SNMP v1/v2c/v3-Agenten,
MIB-Upload (eigene MIBs werden per pysmi kompiliert), Audit-Log aller
Abfragen, plus schneller TCP-Port-Check per nmap. Backend FastAPI (Python,
async pysnmp), Frontend Vanilla JS.

## Benutzer einrichten

```bash
cp users.example.yaml users.yaml
# users.yaml anpassen: Passwörter setzen, weitere User/Rollen ergänzen
```

Rollen: `admin` (GET/WALK/Portscan + MIB-Upload/-Löschen + Audit-Log) und
`viewer` (nur GET/WALK/Portscan).

## Lokal starten

```bash
cd backend
pip install -r requirements.txt
cp ../users.example.yaml users.yaml
uvicorn main:app --reload
```

Danach [http://localhost:8000](http://localhost:8000) öffnen. Der Browser
fragt beim ersten API-Call automatisch per HTTP-Basic-Auth nach den
Zugangsdaten aus `users.yaml`.

## Deploy per Docker

```bash
cp .env.example .env
cp users.example.yaml users.yaml
# beide Dateien anpassen (Passwörter, ggf. Proxy für MIB-Uploads)
docker compose up -d --build
```

Läuft danach auf Port `8082` (siehe `docker-compose.yml`). `users.yaml`,
`data/` (Audit-Log) und `mibs/` (hochgeladene MIBs) werden als Volumes
gemountet und überleben damit Container-Neubauten.

## Hinweise

- **Port-Scan** nutzt standardmäßig einen TCP-Connect-Scan (`-sT`), der ohne
  zusätzliche Capabilities im Container läuft. Für UDP-Scans (z.B. um Port
  161/162 selbst zu prüfen) müsste der Container mit `NET_RAW`/`NET_ADMIN`
  laufen (auskommentiert in `docker-compose.yml`) — deutlich langsamer und
  unzuverlässiger als TCP, daher nicht der Default.
- **MIB-Auflösung**: Neben den mit pysnmp gebündelten Basis-MIBs
  (SNMPv2-MIB, RFC1213-MIB, …) können Admins eigene ASN.1-MIB-Dateien
  hochladen. Fehlende Standard-Abhängigkeiten (SNMPv2-SMI/TC/CONF etc.)
  werden bei Bedarf von `mibs.pysnmp.com` nachgeladen — dafür ggf.
  `HTTP_PROXY`/`HTTPS_PROXY` in `.env` setzen.
- **Audit-Log**: jede GET/WALK/Portscan-Abfrage wird mit Zeitstempel,
  Benutzer, Ziel und Erfolg/Fehler in einer lokalen SQLite-DB (`data/`)
  protokolliert, einsehbar über die Oberfläche (nur `admin`).
- Das Tool selbst ist nur per Basic-Auth geschützt — kein Ersatz für ein
  Firewalling auf ein internes Netz.
