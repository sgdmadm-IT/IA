"""Lecture d'un package SSIS (.dtsx) -> modele objet simple.

Strategie : on parse le XML puis on supprime tous les namespaces (DTS: ...)
pour manipuler des noms de balises/attributs simples.
"""
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from .common import unescape_dts


def _strip_ns(elem):
    """Supprime les prefixes de namespace des balises ET des attributs."""
    def local(tag):
        return tag.split("}", 1)[1] if "}" in tag else tag

    for e in elem.iter():
        e.tag = local(e.tag)
        new_attrib = {}
        for k, v in e.attrib.items():
            new_attrib[local(k)] = v
        e.attrib = new_attrib
    return elem


# --------------------------------------------------------------------------
@dataclass
class Column:
    name: str
    dtype: str = "wstr"
    length: str = "-1"


@dataclass
class Connection:
    refid: str = ""
    dtsid: str = ""
    creation_name: str = ""
    name: str = ""
    conn_string: str = ""
    fmt: str = ""
    delimiter: str = ";"
    codepage: str = ""
    qualifier: str = ""
    columns: list = field(default_factory=list)


@dataclass
class Executable:
    refid: str = ""
    exec_type: str = ""
    creation_name: str = ""
    name: str = ""
    disabled: bool = False
    element: object = None          # ET element brut


@dataclass
class Precedence:
    from_ref: str = ""
    to_ref: str = ""
    expression: str = ""
    eval_op: str = ""
    value: str = ""                 # Success / Failure / Completion


@dataclass
class Package:
    name: str = "package"
    path: str = ""
    connections: dict = field(default_factory=dict)   # refid -> Connection
    conn_by_dtsid: dict = field(default_factory=dict)  # dtsid -> Connection
    variables: dict = field(default_factory=dict)      # name -> value
    executables: list = field(default_factory=list)
    precedences: list = field(default_factory=list)


# --------------------------------------------------------------------------
def _codepage_to_encoding(cp):
    if not cp:
        return ""
    return {"1252": "Windows-1252", "65001": "UTF-8", "1200": "UTF-16LE",
            "850": "Cp850", "28591": "ISO-8859-1"}.get(str(cp), "")


def _parse_connection(cm):
    c = Connection(
        refid=cm.get("refId", ""),
        dtsid=cm.get("DTSID", "").strip("{}"),
        creation_name=cm.get("CreationName", ""),
        name=cm.get("ObjectName", ""),
    )
    inner = cm.find("./ObjectData/ConnectionManager")
    if inner is not None:
        c.conn_string = unescape_dts(inner.get("ConnectionString", ""))
        c.fmt = inner.get("Format", "")
        c.codepage = _codepage_to_encoding(inner.get("CodePage", ""))
        q = unescape_dts(inner.get("TextQualifier", ""))
        c.qualifier = "" if q in ("<none>", "", None) else q
        cols = inner.findall("./FlatFileColumns/FlatFileColumn")
        delim = None
        for fc in cols:
            d = unescape_dts(fc.get("ColumnDelimiter", ""))
            if d and d not in ("\r\n", "\n", "\r"):
                delim = d
            c.columns.append(Column(
                name=fc.get("ObjectName", ""),
                dtype=fc.get("DataType", "130"),
                length=fc.get("MaximumWidth", "-1"),
            ))
        if delim:
            c.delimiter = delim
    return c


def parse_dtsx(path):
    root = _strip_ns(ET.parse(path).getroot())
    pkg = Package(name=root.get("ObjectName") or os.path.splitext(os.path.basename(path))[0],
                  path=path)

    for cm in root.findall("./ConnectionManagers/ConnectionManager"):
        c = _parse_connection(cm)
        if c.refid:
            pkg.connections[c.refid] = c
        if c.dtsid:
            pkg.conn_by_dtsid[c.dtsid] = c

    for v in root.findall("./Variables/Variable"):
        ns = v.get("Namespace", "User")
        name = f"{ns}::{v.get('ObjectName', '')}"
        val = v.find("./VariableValue")
        pkg.variables[name] = val.text if val is not None else ""

    for ex in root.findall("./Executables/Executable"):
        pkg.executables.append(Executable(
            refid=ex.get("refId", ""),
            exec_type=ex.get("ExecutableType", ""),
            creation_name=ex.get("CreationName", ""),
            name=ex.get("ObjectName", ""),
            disabled=(ex.get("Disabled", "").lower() == "true"),
            element=ex,
        ))

    for pc in root.findall("./PrecedenceConstraints/PrecedenceConstraint"):
        pkg.precedences.append(Precedence(
            from_ref=pc.get("From", ""),
            to_ref=pc.get("To", ""),
            expression=pc.get("Expression", ""),
            eval_op=pc.get("EvalOp", ""),
            value={"0": "Success", "2": "Failure", "3": "Completion"}.get(
                pc.get("Value", "0"), "Success"),
        ))
    return pkg


def read_dtproj_manifest(path):
    """Retourne la liste ordonnee des noms de packages (*.dtsx) declares dans un .dtproj."""
    root = _strip_ns(ET.parse(path).getroot())
    names = [p.get("Name") for p in root.iter("Package") if p.get("Name")]
    if not names:  # repli : parcours texte si la structure differe
        import re as _re
        names = _re.findall(r'Package\s+SSIS:Name="([^"]+\.dtsx)"',
                            open(path, encoding="utf-8", errors="ignore").read())
    # dedoublonne en conservant l'ordre
    seen, ordered = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered


def find_packages(input_path):
    """Retourne (packages_trouves, packages_manquants).

    Accepte un fichier .dtsx, un projet .dtproj ou un dossier.
    Pour un .dtproj, la liste attendue vient du manifeste ; les .dtsx doivent
    se trouver dans le meme dossier."""
    if os.path.isfile(input_path):
        if input_path.lower().endswith(".dtsx"):
            return [input_path], []
        if input_path.lower().endswith(".dtproj"):
            base = os.path.dirname(os.path.abspath(input_path))
            found, missing = [], []
            for name in read_dtproj_manifest(input_path):
                cand = os.path.join(base, name)
                (found if os.path.isfile(cand) else missing).append(cand)
            # inclut aussi d'eventuels .dtsx presents mais non listes
            for f in sorted(os.listdir(base)):
                p = os.path.join(base, f)
                if f.lower().endswith(".dtsx") and p not in found:
                    found.append(p)
            return found, [os.path.basename(m) for m in missing]
        raise ValueError(f"Type de fichier non gere : {input_path}")
    result = []
    for dirpath, _dirs, files in os.walk(input_path):
        for f in files:
            if f.lower().endswith(".dtsx"):
                result.append(os.path.join(dirpath, f))
    return sorted(result), []
