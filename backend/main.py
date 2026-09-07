import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

import audit
import mib_manager
from auth import User, require_admin, require_auth
from models import (
    AuditEntryOut,
    MibOut,
    MibTreeNode,
    PortScanRequest,
    PortScanResultOut,
    SnmpGetRequest,
    SnmpWalkRequest,
    VarBindOut,
)
from portscan import PortScanError, scan_ports
from snmp_client import SnmpError, SnmpTarget, snmp_get, snmp_walk


def _loop_exception_handler(loop, context):
    # pysnmp's next_cmd/walk_cmd timeout callback crashes internally on a real
    # request timeout (see snmp_client._next_step); our own timeout guard
    # already turns that into a clean SnmpError, so this specific orphaned-task
    # exception is expected and would otherwise spam the logs on every timeout.
    exc = context.get("exception")
    if isinstance(exc, AttributeError) and "getComponentByPosition" in str(exc):
        return
    loop.default_exception_handler(context)


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.get_event_loop().set_exception_handler(_loop_exception_handler)
    await audit.init_db()
    yield


app = FastAPI(title="snmpweb", lifespan=lifespan)


def _target_from_request(req) -> SnmpTarget:
    return SnmpTarget(
        host=req.host,
        port=req.port,
        version=req.version,
        timeout=req.timeout,
        retries=req.retries,
        community=req.community,
        username=req.username,
        auth_protocol=req.auth_protocol,
        auth_password=req.auth_password,
        priv_protocol=req.priv_protocol,
        priv_password=req.priv_password,
    )


@app.get("/api/whoami")
def api_whoami(user: User = Depends(require_auth)):
    return {"username": user.username, "role": user.role}


@app.post("/api/snmp/get", response_model=list[VarBindOut])
async def api_snmp_get(req: SnmpGetRequest, user: User = Depends(require_auth)):
    target = _target_from_request(req)
    target_desc = ",".join(req.oids)
    try:
        result = await snmp_get(target, req.oids)
    except SnmpError as exc:
        await audit.log_action(user.username, "get", req.host, target_desc, False, str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    await audit.log_action(user.username, "get", req.host, target_desc, True, f"{len(result)} Ergebnis(se)")
    return result


@app.post("/api/snmp/walk", response_model=list[VarBindOut])
async def api_snmp_walk(req: SnmpWalkRequest, user: User = Depends(require_auth)):
    target = _target_from_request(req)
    try:
        result = await snmp_walk(target, req.oid)
    except SnmpError as exc:
        await audit.log_action(user.username, "walk", req.host, req.oid, False, str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    await audit.log_action(user.username, "walk", req.host, req.oid, True, f"{len(result)} Ergebnis(se)")
    return result


@app.post("/api/portscan", response_model=PortScanResultOut)
async def api_portscan(req: PortScanRequest, user: User = Depends(require_auth)):
    try:
        result = await run_in_threadpool(
            scan_ports,
            req.host,
            req.ports or "",
            req.scan_type,
            req.service_detection,
            req.os_detection,
            req.timing,
        )
    except PortScanError as exc:
        await audit.log_action(user.username, "portscan", req.host, req.ports or "", False, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await audit.log_action(
        user.username, "portscan", req.host, req.ports or "", True, f"{len(result['ports'])} Port(s)"
    )
    return result


@app.get("/api/mibs", response_model=list[MibOut])
def api_list_mibs(_user: User = Depends(require_auth)):
    return mib_manager.list_mibs()


@app.post("/api/mibs", response_model=MibOut)
async def api_upload_mib(file: UploadFile = File(...), user: User = Depends(require_admin)):
    content = await file.read()
    try:
        name = await run_in_threadpool(mib_manager.upload_mib, content)
    except mib_manager.MibError as exc:
        await audit.log_action(user.username, "mib_upload", "", file.filename or "", False, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await audit.log_action(user.username, "mib_upload", "", name, True)
    return {"name": name, "compiled": True}


@app.get("/api/mibs/tree", response_model=list[MibTreeNode])
async def api_mibs_tree(_user: User = Depends(require_auth)):
    return await run_in_threadpool(mib_manager.build_module_tree)


@app.delete("/api/mibs/{name}")
async def api_delete_mib(name: str, user: User = Depends(require_admin)):
    try:
        await run_in_threadpool(mib_manager.delete_mib, name)
    except mib_manager.MibError as exc:
        await audit.log_action(user.username, "mib_delete", "", name, False, str(exc))
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await audit.log_action(user.username, "mib_delete", "", name, True)
    return {"status": "deleted"}


@app.get("/api/audit", response_model=list[AuditEntryOut])
async def api_audit(limit: int = 200, _user: User = Depends(require_admin)):
    return await audit.recent(limit)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
