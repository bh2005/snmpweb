# Changelog

Format angelehnt an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

## [Unreleased]

### Added
- SNMP GET/WALK gegen v1/v2c/v3-Agenten (FastAPI-Backend, async pysnmp)
- TCP-Port-Scan per nmap (Standard: `-sT`, ohne Extra-Capabilities lauffähig)
- Basic-Auth mit mehreren Benutzern und Rollen (`admin`/`viewer`) über `users.yaml`
- MIB-Upload/-Verwaltung: eigene ASN.1-MIB-Dateien hochladen, per pysmi
  kompilieren (Basis-MIBs werden bei Bedarf von mibs.pysnmp.com nachgeladen),
  auflisten und löschen (nur `admin`)
- Audit-Log aller GET/WALK/Portscan-Aufrufe in SQLite, einsehbar über die
  Oberfläche (nur `admin`)
- Vanilla-JS-Frontend mit rollenabhängig ein-/ausgeblendeten Bereichen
- Docker-/docker-compose-Setup mit persistenten Volumes für `users.yaml`,
  Audit-DB und MIBs
- MIB-Browser (`GET /api/mibs/tree`): zeigt alle geladenen MIB-Module (33
  bei pysnmp mitgelieferte Basis-Module plus eigene Uploads) als auf-
  klappbaren Baum mit OID, Syntax, Zugriff, Status und Beschreibung je
  Objekt; Klick auf ein Objekt übernimmt dessen OID in das GET/WALK-Feld
- Frontend komplett auf Vue 3 (Pinia + Vite + Tailwind) umgestellt, ersetzt
  das bisherige Vanilla-JS-Frontend; eigene Panels für Query, PortScan,
  MIB-Browser, MIB-Verwaltung, Audit-Log, Hilfe und Handbuch sowie eine
  Login-View
- Port-Scan erweitert: UDP- und kombinierte TCP+UDP-Scans (`-sU`), optionale
  Service- (`-sV`) und OS-Erkennung (`-O`), wählbares nmap-Timing-Template
  (`T2`–`T5`); Ergebnis liefert zusätzlich erkanntes Produkt/Version je Port
  sowie OS-Treffer mit Treffergenauigkeit

### Changed
- `backend/Dockerfile` auf Multi-Stage-Build umgestellt: eigene
  `node:20-alpine`-Stage baut das Vite-Frontend, die Python-Stage kopiert
  nur noch das fertige `frontend/dist`

### Fixed
- Eigener Timeout-Guard für SNMP WALK: eine pysnmp-Version-7-Regression lässt
  `walk_cmd` bei einem echten Request-Timeout (Gerät nicht erreichbar,
  falsche Community) unbegrenzt hängen, statt einen Fehler zurückzugeben
- MIB-Re-Upload/-Rekompilierung schlug unter Windows fehl, weil pysmis
  Datei-Writer per `os.rename()` auf eine bereits existierende Zieldatei
  schreibt (unter Linux unauffällig, da POSIX-`rename` überschreibt) — alte
  kompilierte Datei wird vor dem Kompilieren jetzt explizit entfernt
- MIB-Download von mibs.pysnmp.com scheiterte hinter TLS-Inspection-Proxies
  an der Zertifikatsprüfung, weil `requests`/`urllib3` ihr eigenes
  `certifi`-Bündel nutzen und `update-ca-certificates` ignorieren —
  `REQUESTS_CA_BUNDLE` zeigt jetzt auf den System-Trust-Store
- Docker-Build scheiterte hinter TLS-Inspection-Proxies komplett (`npm
  install`/`pip install` mit SSL-Fehlern), da weder der Node- noch der
  Python-Build-Stage die K+S-Root/Zwischen-CA kannten — `backend/certs/`
  enthält jetzt die K+S-CA-Zertifikate, beide Stages binden sie per
  `update-ca-certificates` ein (zusätzlich `NODE_EXTRA_CA_CERTS`,
  `SSL_CERT_FILE`, `PIP_CERT`)
