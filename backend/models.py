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
    scan_type: Literal["tcp", "udp", "tcp+udp"] = "tcp"
    service_detection: bool = False
    os_detection: bool = False
    timing: Literal["T2", "T3", "T4", "T5"] = "T4"


class PortResultOut(BaseModel):
    port: int
    protocol: str
    state: str
    service: str
    product: Optional[str] = None
    version: Optional[str] = None


class OsGuessOut(BaseModel):
    name: str
    accuracy: int


class PortScanResultOut(BaseModel):
    ports: list[PortResultOut]
    os_guesses: list[OsGuessOut] = Field(default_factory=list)


class MibOut(BaseModel):
    name: str
    compiled: bool


class MibTreeNode(BaseModel):
    name: str
    oid: str = ""
    module: Optional[str] = None
    kind: str
    origin: Optional[str] = None
    syntax: Optional[str] = None
    access: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    children: list["MibTreeNode"] = Field(default_factory=list)


MibTreeNode.model_rebuild()


class AuditEntryOut(BaseModel):
    ts: str
    username: str
    action: str
    host: Optional[str] = None
    target: Optional[str] = None
    success: bool
    detail: str = ""
