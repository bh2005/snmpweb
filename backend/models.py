from typing import Literal, Optional

from pydantic import BaseModel, Field


class SnmpTargetIn(BaseModel):
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


class SnmpGetRequest(SnmpTargetIn):
    oids: list[str] = Field(min_length=1)


class SnmpWalkRequest(SnmpTargetIn):
    oid: str


class VarBindOut(BaseModel):
    oid: str
    name: str
    type: str
    value: str


class PortScanRequest(BaseModel):
    host: str
    ports: Optional[str] = None


class PortResultOut(BaseModel):
    port: int
    protocol: str
    state: str
    service: str


class MibOut(BaseModel):
    name: str
    compiled: bool


class AuditEntryOut(BaseModel):
    ts: str
    username: str
    action: str
    host: Optional[str] = None
    target: Optional[str] = None
    success: bool
    detail: str = ""
