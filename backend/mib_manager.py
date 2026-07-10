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
