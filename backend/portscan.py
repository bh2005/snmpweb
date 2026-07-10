"""Thin wrapper around the nmap CLI for a quick reachability/port check."""

import re

import nmap

DEFAULT_PORTS = "22,23,80,161,162,443,502,8080"
_PORT_SPEC_RE = re.compile(r"^[0-9,\-]+$")


class PortScanError(Exception):
    pass


def scan_ports(host: str, ports: str = DEFAULT_PORTS) -> list[dict]:
    ports = ports.strip() or DEFAULT_PORTS
    if not _PORT_SPEC_RE.match(ports):
        raise PortScanError("Port-Liste darf nur Ziffern, Kommas und Bindestriche enthalten")

    scanner = nmap.PortScanner()
    try:
        # -Pn: kein vorheriges Ping (viele Monitoring-Hosts blocken ICMP)
        # -sT: TCP-Connect-Scan, läuft ohne root/CAP_NET_RAW im Container
        scanner.scan(hosts=host, ports=ports, arguments="-Pn -sT -T4")
    except nmap.PortScannerError as exc:
        raise PortScanError(str(exc)) from exc

    if host not in scanner.all_hosts():
        return []

    results = []
    tcp_ports = scanner[host].get("tcp", {})
    for port in sorted(tcp_ports):
        info = tcp_ports[port]
        results.append(
            {
                "port": port,
                "protocol": "tcp",
                "state": info.get("state"),
                "service": info.get("name") or "",
            }
        )
    return results
