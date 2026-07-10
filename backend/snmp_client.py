"""Async SNMP GET/WALK client supporting v1, v2c and v3 (pysnmp >= 7)."""

import asyncio
from dataclasses import dataclass
from typing import Literal, Optional

from pysnmp.hlapi.v1arch.asyncio import (
    CommunityData,
    ObjectIdentity,
    ObjectType,
    SnmpDispatcher,
)
from pysnmp.hlapi.v1arch.asyncio import UdpTransportTarget as V1UdpTransportTarget
from pysnmp.hlapi.v1arch.asyncio import get_cmd as v1_get_cmd
from pysnmp.hlapi.v1arch.asyncio import walk_cmd as v1_walk_cmd
from pysnmp.hlapi.v3arch.asyncio import (
    ContextData,
    SnmpEngine,
    UsmUserData,
)
from pysnmp.hlapi.v3arch.asyncio import UdpTransportTarget as V3UdpTransportTarget
from pysnmp.hlapi.v3arch.asyncio import get_cmd as v3_get_cmd
from pysnmp.hlapi.v3arch.asyncio import walk_cmd as v3_walk_cmd
from pysnmp.hlapi.v3arch.asyncio import (
    usm3DESEDEPrivProtocol,
    usmAesCfb128Protocol,
    usmAesCfb192Protocol,
    usmAesCfb256Protocol,
    usmDESPrivProtocol,
    usmHMAC128SHA224AuthProtocol,
    usmHMAC192SHA256AuthProtocol,
    usmHMAC256SHA384AuthProtocol,
    usmHMAC384SHA512AuthProtocol,
    usmHMACMD5AuthProtocol,
    usmHMACSHAAuthProtocol,
    usmNoAuthProtocol,
    usmNoPrivProtocol,
)

MAX_WALK_ROWS = 2000

AUTH_PROTOCOLS = {
    "MD5": usmHMACMD5AuthProtocol,
    "SHA": usmHMACSHAAuthProtocol,
    "SHA224": usmHMAC128SHA224AuthProtocol,
    "SHA256": usmHMAC192SHA256AuthProtocol,
    "SHA384": usmHMAC256SHA384AuthProtocol,
    "SHA512": usmHMAC384SHA512AuthProtocol,
    "none": usmNoAuthProtocol,
}

PRIV_PROTOCOLS = {
    "DES": usmDESPrivProtocol,
    "3DES": usm3DESEDEPrivProtocol,
    "AES128": usmAesCfb128Protocol,
    "AES192": usmAesCfb192Protocol,
    "AES256": usmAesCfb256Protocol,
    "none": usmNoPrivProtocol,
}


class SnmpError(Exception):
    pass


@dataclass
class SnmpTarget:
    host: str
    port: int = 161
    version: Literal["v1", "v2c", "v3"] = "v2c"
    timeout: float = 2.0
    retries: int = 1
    community: Optional[str] = None
    username: Optional[str] = None
    auth_protocol: Optional[str] = None
    auth_password: Optional[str] = None
    priv_protocol: Optional[str] = None
    priv_password: Optional[str] = None


def _varbind_to_dict(varbind) -> dict:
    oid, value = varbind
    return {
        "oid": str(oid.getOid()),
        "name": oid.prettyPrint(),
        "type": type(value).__name__,
        "value": value.prettyPrint(),
    }


def _step_timeout(target: SnmpTarget) -> float:
    return target.timeout * (target.retries + 1) + 1.0


async def _next_step(agen, step_timeout: float):
    # pysnmp's next_cmd/walk_cmd callback dereferences the (None) response PDU
    # before checking errorIndication on a real timeout, so the awaited future
    # never resolves and the generator hangs forever instead of raising.
    # Guard every step with our own timeout so an unreachable host/wrong
    # community can't hang the request indefinitely.
    try:
        return await asyncio.wait_for(agen.__anext__(), timeout=step_timeout)
    except asyncio.TimeoutError:
        raise SnmpError("Zeitüberschreitung - keine Antwort vom Gerät") from None


def _raise_on_error(errind, errstat, erridx, varbinds):
    if errind:
        raise SnmpError(str(errind))
    if errstat:
        idx = int(erridx) - 1 if erridx else 0
        at = varbinds[idx][0] if varbinds and idx < len(varbinds) else "?"
        raise SnmpError(f"{errstat.prettyPrint()} at {at}")


def _usm_user_data(target: SnmpTarget) -> UsmUserData:
    if not target.username:
        raise SnmpError("SNMPv3 benötigt einen Usernamen")

    if target.auth_protocol and target.auth_protocol != "none":
        auth_protocol = AUTH_PROTOCOLS.get(target.auth_protocol)
        if auth_protocol is None:
            raise SnmpError(f"Unbekanntes Auth-Protokoll: {target.auth_protocol}")
    else:
        auth_protocol = usmNoAuthProtocol

    if target.priv_protocol and target.priv_protocol != "none":
        priv_protocol = PRIV_PROTOCOLS.get(target.priv_protocol)
        if priv_protocol is None:
            raise SnmpError(f"Unbekanntes Priv-Protokoll: {target.priv_protocol}")
    else:
        priv_protocol = usmNoPrivProtocol

    return UsmUserData(
        target.username,
        authKey=target.auth_password or None,
        privKey=target.priv_password or None,
        authProtocol=auth_protocol,
        privProtocol=priv_protocol,
    )


async def snmp_get(target: SnmpTarget, oids: list[str]) -> list[dict]:
    var_binds = [ObjectType(ObjectIdentity(oid)) for oid in oids]

    if target.version in ("v1", "v2c"):
        dispatcher = SnmpDispatcher()
        try:
            transport = await V1UdpTransportTarget.create(
                (target.host, target.port), timeout=target.timeout, retries=target.retries
            )
            mp_model = 0 if target.version == "v1" else 1
            auth = CommunityData(target.community or "public", mpModel=mp_model)
            errind, errstat, erridx, varbinds = await v1_get_cmd(
                dispatcher, auth, transport, *var_binds
            )
            _raise_on_error(errind, errstat, erridx, varbinds)
            return [_varbind_to_dict(vb) for vb in varbinds]
        finally:
            dispatcher.close()

    engine = SnmpEngine()
    try:
        transport = await V3UdpTransportTarget.create(
            (target.host, target.port), timeout=target.timeout, retries=target.retries
        )
        auth = _usm_user_data(target)
        errind, errstat, erridx, varbinds = await v3_get_cmd(
            engine, auth, transport, ContextData(), *var_binds
        )
        _raise_on_error(errind, errstat, erridx, varbinds)
        return [_varbind_to_dict(vb) for vb in varbinds]
    finally:
        engine.close_dispatcher()


async def snmp_walk(target: SnmpTarget, oid: str) -> list[dict]:
    var_bind = ObjectType(ObjectIdentity(oid))
    rows: list[dict] = []

    if target.version in ("v1", "v2c"):
        dispatcher = SnmpDispatcher()
        try:
            transport = await V1UdpTransportTarget.create(
                (target.host, target.port), timeout=target.timeout, retries=target.retries
            )
            mp_model = 0 if target.version == "v1" else 1
            auth = CommunityData(target.community or "public", mpModel=mp_model)
            step_timeout = _step_timeout(target)
            agen = v1_walk_cmd(
                dispatcher, auth, transport, var_bind, lexicographicMode=False
            )
            while True:
                try:
                    errind, errstat, erridx, varbinds = await _next_step(agen, step_timeout)
                except StopAsyncIteration:
                    break
                _raise_on_error(errind, errstat, erridx, varbinds)
                rows.extend(_varbind_to_dict(vb) for vb in varbinds)
                if len(rows) >= MAX_WALK_ROWS:
                    break
            return rows
        finally:
            dispatcher.close()

    engine = SnmpEngine()
    try:
        transport = await V3UdpTransportTarget.create(
            (target.host, target.port), timeout=target.timeout, retries=target.retries
        )
        auth = _usm_user_data(target)
        step_timeout = _step_timeout(target)
        agen = v3_walk_cmd(
            engine, auth, transport, ContextData(), var_bind, lexicographicMode=False
        )
        while True:
            try:
                errind, errstat, erridx, varbinds = await _next_step(agen, step_timeout)
            except StopAsyncIteration:
                break
            _raise_on_error(errind, errstat, erridx, varbinds)
            rows.extend(_varbind_to_dict(vb) for vb in varbinds)
            if len(rows) >= MAX_WALK_ROWS:
                break
        return rows
    finally:
        engine.close_dispatcher()
