export const helpTexts = {
  query: `
## SNMP Query

GET fragt genau eine OID ab, WALK läuft den Teilbaum unterhalb der OID ab.

### Ziel
Host/Port/Version/Community bzw. v3-Zugangsdaten kommen aus dem Ziel-Panel links.

### Live-Polling
Die **Live**-Checkbox fragt die aktuelle OID per GET im gewählten Intervall
immer wieder ab — praktisch für Zähler wie \`ifInOctets\`.

### Tabellenansicht
Erkennt snmpweb bei einem WALK mehrere Tabellenspalten (z.B. \`ifTable\`),
erscheint ein Umschalter zwischen flacher Liste und einer Index×Spalte-Tabelle.

### CSV exportieren
Lädt die aktuelle Ergebnistabelle als CSV-Datei herunter (Client-seitig, kein Server-Speichern).
`,

  portscan: `
## Port-Scan

Schneller TCP/UDP-Check gegen den Ziel-Host per nmap.

### Scan-Typ
- **TCP-Connect**: Standard, läuft ohne besondere Rechte im Container
- **UDP** / **TCP+UDP**: braucht Raw Sockets (\`NET_RAW\`/\`NET_ADMIN\`), im
  Container standardmäßig deaktiviert (siehe \`docker-compose.yml\`)

### Zusatzoptionen
- **Service-Version (-sV)**: versucht, Dienst und Version pro Port zu erkennen
- **OS-Erkennung (-O)**: versucht, das Betriebssystem zu erraten (braucht ebenfalls Raw Sockets)
- **Timing**: T2 (langsam/unauffällig) bis T5 (schnell/aggressiv)
`,

  mibs: `
## MIBs

Eigene ASN.1-MIB-Dateien hochladen und verwalten (nur **admin**).

Hochgeladene MIBs werden per pysmi kompiliert. Fehlende Standard-Abhängigkeiten
(SNMPv2-SMI/TC/CONF etc.) lädt snmpweb bei Bedarf automatisch von
\`mibs.pysnmp.com\` nach.
`,

  mibbrowser: `
## MIB-Browser

Baum aller geladenen MIB-Module — die bei pysnmp mitgelieferten Standard-Module
und alle selbst hochgeladenen.

### Suche
Das Suchfeld filtert nach Name oder OID und klappt Treffer automatisch auf.

### Objekt auswählen
Klick auf ein Objekt zeigt rechts die Details (Syntax, Zugriff, Status,
Beschreibung) und trägt die OID direkt ins SNMP-Query-Feld darunter ein —
Baum durchsuchen, auswählen, GET/WALK klicken.
`,

  audit: `
## Audit-Log

Protokoll aller GET/WALK/Portscan/MIB-Aktionen mit Zeitstempel, Benutzer,
Ziel und Erfolg/Fehler. Nur für **admin** sichtbar.
`,

  manual: `
## Handbuch

Das vollständige Handbuch findest du im Menüpunkt **Handbuch** links.
`,
}

export function getHelp(section) {
  return helpTexts[section] || '## Hilfe\n\nFür diesen Bereich gibt es noch keinen Hilfetext.'
}
