"""Upload, Kompilierung und Verwaltung benutzerdefinierter MIB-Module.

Hochgeladene ASN.1-MIB-Dateien werden per pysmi zu pysnmp-Modulen kompiliert.
Fehlende Basis-MIBs (SNMPv2-SMI, SNMPv2-TC, ...) werden bei Bedarf von
mibs.pysnmp.com nachgeladen (offizielles pysmi/lextudio MIB-Repository).
"""

import re
from pathlib import Path

from pysmi.codegen import PySnmpCodeGen
from pysmi.compiler import MibCompiler
from pysmi.parser import SmiV1CompatParser
from pysmi.reader import FileReader, HttpReader
from pysmi.searcher import StubSearcher
from pysmi.writer import PyFileWriter
from pysnmp.smi import builder

# Module ohne eigene OID-Objekte (ASN.1-Basistypen, interne Stub-Module) -
# im Baum nicht relevant, werden beim Bauen ausgefiltert.
_NON_BROWSABLE_MODULES = {"ASN1", "ASN1-ENUMERATION", "ASN1-REFINEMENT"}

# Klassennamen aus SNMPv2-SMI, geprueft in dieser Reihenfolge, um einem
# Objekt seine Baum-"kind" zuzuordnen.
_KIND_BY_SMI_CLASS = (
    ("ModuleIdentity", "module-identity"),
    ("NotificationType", "notification"),
    ("MibTable", "table"),
    ("MibTableRow", "row"),
    ("MibTableColumn", "leaf"),
    ("MibScalar", "leaf"),
)

MIB_REPOSITORY = "https://mibs.pysnmp.com/asn1/@mib@"

MIBS_DIR = Path(__file__).resolve().parent / "mibs"
SOURCE_DIR = MIBS_DIR / "source"
COMPILED_DIR = MIBS_DIR / "compiled"
SOURCE_DIR.mkdir(parents=True, exist_ok=True)
COMPILED_DIR.mkdir(parents=True, exist_ok=True)

_MODULE_NAME_RE = re.compile(
    r"^\s*([A-Za-z][A-Za-z0-9-]*)\s+DEFINITIONS\s*(?:IMPLICIT TAGS\s*|EXPLICIT TAGS\s*)?::=",
    re.MULTILINE,
)
_SAFE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*$")


class MibError(Exception):
    pass


def _extract_module_name(text: str) -> str:
    match = _MODULE_NAME_RE.search(text)
    if not match:
        raise MibError(
            "Kein MIB-Modulname gefunden (erwarte z.B. 'MEIN-MIB DEFINITIONS ::= BEGIN')"
        )
    return match.group(1)


def upload_mib(content: bytes) -> str:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    module_name = _extract_module_name(text)
    dest = SOURCE_DIR / f"{module_name}.mib"
    dest.write_text(text, encoding="utf-8")

    # Re-Upload/Re-Kompilierung: alte kompilierte Datei vorher entfernen.
    # pysmi schreibt per os.rename(tmp, dest); unter Windows schlaegt das
    # fehl, wenn dest schon existiert (anders als unter Linux/POSIX).
    (COMPILED_DIR / f"{module_name}.py").unlink(missing_ok=True)

    compiler = MibCompiler(
        SmiV1CompatParser(), PySnmpCodeGen(), PyFileWriter(str(COMPILED_DIR))
    )
    compiler.add_sources(FileReader(str(SOURCE_DIR)))
    compiler.add_sources(HttpReader(MIB_REPOSITORY))
    compiler.add_searchers(StubSearcher(*PySnmpCodeGen.baseMibs))

    results = compiler.compile(module_name, noDeps=False)
    status = results.get(module_name)

    if status not in ("compiled", "untouched"):
        dest.unlink(missing_ok=True)
        detail = ", ".join(f"{k}={v}" for k, v in results.items())
        raise MibError(f"Kompilierung fehlgeschlagen ({detail})")

    return module_name


def list_mibs() -> list[dict]:
    mibs = []
    for f in sorted(SOURCE_DIR.glob("*.mib")):
        name = f.stem
        compiled = (COMPILED_DIR / f"{name}.py").exists()
        mibs.append({"name": name, "compiled": compiled})
    return mibs


def compiled_module_names() -> list[str]:
    return [p.stem for p in COMPILED_DIR.glob("*.py")]


def delete_mib(name: str) -> None:
    if not _SAFE_NAME_RE.match(name):
        raise MibError("Ungültiger MIB-Name")

    removed = False

    source = SOURCE_DIR / f"{name}.mib"
    if source.exists():
        source.unlink()
        removed = True

    compiled = COMPILED_DIR / f"{name}.py"
    if compiled.exists():
        compiled.unlink()
        removed = True

    pycache = COMPILED_DIR / "__pycache__"
    if pycache.exists():
        for f in pycache.glob(f"{name}.*"):
            f.unlink()

    if not removed:
        raise MibError(f"MIB {name} nicht gefunden")


def _safe_call(obj, method_name: str):
    method = getattr(obj, method_name, None)
    if method is None:
        return None
    try:
        return method()
    except Exception:
        return None


def _syntax_name(obj) -> str | None:
    syntax = _safe_call(obj, "getSyntax")
    return None if syntax is None else type(syntax).__name__


def _classify(obj, smi_symbols: dict) -> str:
    for cls_name, kind in _KIND_BY_SMI_CLASS:
        cls = smi_symbols.get(cls_name)
        if cls is not None and isinstance(obj, cls):
            return kind
    return "node"


def _describe_object(sym_name: str, obj, module_name: str, oid_tuple: tuple, smi_symbols: dict) -> dict:
    return {
        "oid_tuple": oid_tuple,
        "oid": ".".join(str(x) for x in oid_tuple),
        "name": sym_name,
        "module": module_name,
        "kind": _classify(obj, smi_symbols),
        "origin": None,
        "syntax": _syntax_name(obj),
        "access": _safe_call(obj, "getMaxAccess"),
        "status": _safe_call(obj, "getStatus"),
        "description": _safe_call(obj, "getDescription"),
        "children": [],
    }


def _nest_by_oid(nodes: list[dict]) -> list[dict]:
    # Klassischer "Baum aus sortierten Pfaden"-Aufbau: nach OID-Tupel sortiert
    # liegen alle Nachfahren eines Knotens direkt danach, bevor das naechste
    # Geschwister-Element folgt. Ein Stack haelt die aktuelle Vorfahren-Kette.
    nodes_sorted = sorted(nodes, key=lambda n: n["oid_tuple"])
    roots: list[dict] = []
    stack: list[dict] = []
    for node in nodes_sorted:
        while stack and not (
            len(stack[-1]["oid_tuple"]) < len(node["oid_tuple"])
            and node["oid_tuple"][: len(stack[-1]["oid_tuple"])] == stack[-1]["oid_tuple"]
        ):
            stack.pop()
        (stack[-1]["children"] if stack else roots).append(node)
        stack.append(node)
    return roots


def _strip_oid_tuple(node: dict) -> dict:
    node.pop("oid_tuple", None)
    for child in node["children"]:
        _strip_oid_tuple(child)
    return node


def build_module_tree() -> list[dict]:
    """Baut den Baum aller geladenen MIB-Module (Standard + eigene Uploads)
    fuer den MIB-Browser im Frontend."""
    mib_builder = builder.MibBuilder()
    # Ohne loadTexts=True liest pysmi/pysnmp DESCRIPTION/STATUS-Klauseln gar
    # nicht erst ein (Performance-Default) - fuer den Browser brauchen wir sie.
    mib_builder.loadTexts = True
    mib_builder.load_modules()

    custom_names = set(compiled_module_names())
    if custom_names:
        mib_builder.add_mib_sources(builder.DirMibSource(str(COMPILED_DIR)))
        mib_builder.load_modules(*custom_names)

    smi_symbols = mib_builder.mibSymbols.get("SNMPv2-SMI", {})

    modules = []
    for module_name in sorted(mib_builder.mibSymbols):
        if module_name.startswith("__") or module_name in _NON_BROWSABLE_MODULES:
            continue

        nodes = []
        for sym_name, obj in mib_builder.mibSymbols[module_name].items():
            get_name = getattr(obj, "getName", None)
            if get_name is None:
                continue
            try:
                oid_tuple = tuple(int(x) for x in get_name())
            except Exception:
                continue
            if not oid_tuple:
                continue
            nodes.append(_describe_object(sym_name, obj, module_name, oid_tuple, smi_symbols))

        if not nodes:
            continue

        modules.append(
            {
                "name": module_name,
                "oid": "",
                "module": module_name,
                "kind": "module",
                "origin": "custom" if module_name in custom_names else "standard",
                "syntax": None,
                "access": None,
                "status": None,
                "description": None,
                "children": _nest_by_oid(nodes),
            }
        )

    return [_strip_oid_tuple(m) for m in modules]
