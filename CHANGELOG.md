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
