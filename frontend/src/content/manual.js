export const manual = `
# snmpweb — Handbuch

Web-basierter SNMP-Tester/Browser: GET/WALK gegen SNMP v1/v2c/v3-Agenten,
MIB-Upload, ein durchsuchbarer MIB-Browser, ein schneller TCP/UDP-Port-Check
per nmap, sowie ein Audit-Log aller Abfragen.

## Anmeldung und Rollen

Zwei Rollen:

| Rolle | Rechte |
|-------|--------|
| **viewer** | GET/WALK, Port-Scan, MIBs ansehen, MIB-Browser |
| **admin** | zusätzlich MIB-Upload/-Löschen und Audit-Log |

## Ziel-Panel (Sidebar)

Fest oben in der Sidebar, gilt für SNMP Query, Port-Scan und MIB-Browser:

- **Host**: Ziel-IP/-Hostname (merkt sich zuletzt genutzte Werte als Vorschlag)
- **Port**: Standard 161
- **Version**: v1, v2c (mit Community-String) oder v3 (Username + Auth-/Priv-Protokoll und -Passwort)

## SNMP Query

- **GET**: fragt genau eine OID ab
- **WALK**: läuft den Teilbaum unterhalb der OID ab (bis zu 2000 Zeilen)
- **Live**: fragt die OID per GET wiederholt ab (2/5/10/30 Sekunden) — nützlich für Zähler
- **Tabellenansicht**: erscheint automatisch, wenn ein WALK mehrere
  Tabellenspalten liefert (z.B. \`ifTable\`) — schaltet zwischen flacher Liste
  und einer Index×Spalte-Ansicht um
- **CSV exportieren**: lädt die aktuelle Ergebnistabelle als CSV-Datei herunter

## Port-Scan

TCP/UDP-Check per nmap gegen den Ziel-Host:

- **Scan-Typ**: TCP-Connect (Standard, ohne besondere Rechte), UDP oder beides
  (UDP/TCP+UDP brauchen \`NET_RAW\`/\`NET_ADMIN\` im Container, standardmäßig aus)
- **Timing**: T2 (unauffällig) bis T5 (aggressiv)
- **Service-Version (-sV)**: erkennt Dienst/Version pro offenem Port
- **OS-Erkennung (-O)**: schätzt das Betriebssystem (braucht ebenfalls Raw Sockets)

## MIBs (nur admin)

Eigene ASN.1-MIB-Dateien hochladen; werden per pysmi kompiliert. Fehlende
Standard-Abhängigkeiten lädt snmpweb bei Bedarf von \`mibs.pysnmp.com\` nach.
Hochgeladene MIBs lassen sich einzeln wieder löschen.

## MIB-Browser

Baum aller geladenen MIB-Module: die bei pysnmp mitgelieferten Standard-Module
sowie alle selbst hochgeladenen. Das Suchfeld filtert nach Name oder OID und
klappt Treffer automatisch auf. Ein Klick auf ein Objekt zeigt rechts die
Details (Syntax, Zugriff, Status, Beschreibung) und trägt die OID direkt in
die eingebettete SNMP-Query darunter ein — Baum durchsuchen, Objekt auswählen,
GET/WALK klicken.

## Audit-Log (nur admin)

Protokolliert jede GET/WALK/Portscan/MIB-Aktion mit Zeitstempel, Benutzer,
Ziel und Erfolg/Fehler.
`
