"""Thin wrapper around the nmap CLI for a quick reachability/port check."""

import re
from typing import Literal

import nmap

DEFAULT_PORTS = "22,23,80,161,162,443,502,8080"
_PORT_SPEC_RE = re.compile(r"^[0-9,\-]+$")


class PortScanError(Exception):
    pass


def scan_ports(
    host: str,
    ports: str = DEFAULT_PORTS,
    scan_type: Literal["tcp", "udp", "tcp+udp"] = "tcp",
    service_detection: bool = False,
    os_detection: bool = False,
    timing: Literal["T2", "T3", "T4", "T5"] = "T4",
) -> dict:
    ports = ports.strip() or DEFAULT_PORTS
    if not _PORT_SPEC_RE.match(ports):
        raise PortScanError("Port-Liste darf nur Ziffern, Kommas und Bindestriche enthalten")

    # -Pn: kein vorheriges Ping (viele Monitoring-Hosts blocken ICMP).
    # -sU (UDP) und -O (OS-Erkennung) brauchen Raw Sockets, also
    # NET_RAW/NET_ADMIN im Container (siehe docker-compose.yml, dort
    # standardmäßig auskommentiert) - ohne diese Caps liefert nmap hier
    # einen Fehler, den wir unten als PortScanError durchreichen.
    scan_flags = {"tcp": "-sT", "udp": "-sU", "tcp+udp": "-sT -sU"}[scan_type]
    arguments = f"-Pn {scan_flags} -{timing}"
    if service_detection:
        arguments += " -sV"
    if os_detection:
        arguments += " -O"

    scanner = nmap.PortScanner()
    try:
        scanner.scan(hosts=host, ports=ports, arguments=arguments)
    except nmap.PortScannerError as exc:
        raise PortScanError(str(exc)) from exc

    if host not in scanner.all_hosts():
        return {"ports": [], "os_guesses": []}

    host_result = scanner[host]
    results = []
    for protocol in ("tcp", "udp"):
        proto_ports = host_result.get(protocol, {})
        for port in sorted(proto_ports):
            info = proto_ports[port]
            results.append(
                {
                    "port": port,
                    "protocol": protocol,
                    "state": info.get("state"),
                    "service": info.get("name") or "",
                    "product": info.get("product") or None,
                    "version": info.get("version") or None,
                }
            )

    os_guesses = [
        {"name": match.get("name", ""), "accuracy": int(match.get("accuracy", 0))}
        for match in host_result.get("osmatch", [])
    ]

    return {"ports": results, "os_guesses": os_guesses}
