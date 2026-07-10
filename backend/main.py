import asyncio
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from models import (
    PortResultOut,
    PortScanRequest,
    SnmpGetRequest,
    SnmpWalkRequest,
    VarBindOut,
)
from portscan import PortScanError, scan_ports
from snmp_client import SnmpError, SnmpTarget, snmp_get, snmp_walk

APP_USER = os.environ.get("SNMPWEB_USER", "admin")
APP_PASSWORD = os.environ.get("SNMPWEB_PASSWORD")


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
    yield


app = FastAPI(title="snmpweb", lifespan=lifespan)
security = HTTPBasic()


def require_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    if not APP_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="SNMPWEB_PASSWORD ist nicht gesetzt (siehe .env)",
        )
    user_ok = secrets.compare_digest(credentials.username, APP_USER)
    pass_ok = secrets.compare_digest(credentials.password, APP_PASSWORD)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=401,
            detail="Falscher Benutzername oder Passwort",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


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


@app.post("/api/snmp/get", response_model=list[VarBindOut])
async def api_snmp_get(req: SnmpGetRequest, _user: str = Depends(require_auth)):
    target = _target_from_request(req)
    try:
        return await snmp_get(target, req.oids)
    except SnmpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/snmp/walk", response_model=list[VarBindOut])
async def api_snmp_walk(req: SnmpWalkRequest, _user: str = Depends(require_auth)):
    target = _target_from_request(req)
    try:
        return await snmp_walk(target, req.oid)
    except SnmpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/portscan", response_model=list[PortResultOut])
def api_portscan(req: PortScanRequest, _user: str = Depends(require_auth)):
    try:
        return scan_ports(req.host, req.ports or "")
    except PortScanError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
