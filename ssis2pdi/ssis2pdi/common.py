"""Correspondances de types et traduction d'expressions SSIS -> PDI."""
import re

# --- Types du pipeline SSIS (attribut dataType, ex. "wstr", "i4") -> type PDI
PDI_TYPE = {
    "wstr": "String", "str": "String", "text": "String", "ntext": "String",
    "guid": "String",
    "i1": "Integer", "i2": "Integer", "i4": "Integer", "i8": "Integer",
    "ui1": "Integer", "ui2": "Integer", "ui4": "Integer", "ui8": "Integer",
    "r4": "Number", "r8": "Number", "float": "Number", "double": "Number",
    "cy": "BigNumber", "numeric": "BigNumber", "decimal": "BigNumber",
    "bool": "Boolean",
    "date": "Date", "dbdate": "Date", "dbtime": "Date", "dbtime2": "Date",
    "dbtimestamp": "Date", "dbtimestamp2": "Date", "dbtimestampoffset": "Date",
    "bytes": "Binary", "image": "Binary",
}

# --- Codes numériques de type utilisés dans les FlatFileColumn du dtsx
FLATFILE_CODE = {
    "129": "str", "130": "wstr",
    "16": "i1", "2": "i2", "3": "i4", "20": "i8",
    "17": "ui1", "18": "ui2", "19": "ui4", "21": "ui8",
    "4": "r4", "5": "r8", "6": "cy",
    "131": "numeric", "139": "numeric",
    "11": "bool",
    "7": "date", "133": "dbdate", "134": "dbtime", "135": "dbtimestamp",
    "141": "image", "128": "bytes",
}


def ssis_type_to_pdi(dtype):
    if dtype is None:
        return "String"
    dtype = str(dtype).strip()
    if dtype in FLATFILE_CODE:          # code numérique -> code texte
        dtype = FLATFILE_CODE[dtype]
    return PDI_TYPE.get(dtype.lower(), "String")


def unescape_dts(value):
    """Decode les sequences _x00XX_ des attributs dtsx (ex. _x003B_ -> ';')."""
    if value is None:
        return value

    def repl(m):
        try:
            return chr(int(m.group(1), 16))
        except ValueError:
            return m.group(0)

    return re.sub(r"_x([0-9A-Fa-f]{4})_", repl, value)


def sanitize_filename(name):
    name = re.sub(r"\s+", "_", (name or "").strip())
    name = re.sub(r"[^\w\-.]+", "_", name, flags=re.UNICODE)
    return name.strip("._") or "package"


# --------------------------------------------------------------------------
# Traduction d'expressions "Derived Column" SSIS -> formule libformula (PDI)
# --------------------------------------------------------------------------
_CAST_RE = re.compile(r"\(\s*DT_[A-Z0-9_]+(?:\s*,\s*\d+)*\s*\)")

# nom de fonction SSIS -> nom libformula
_FUNC_MAP = {
    "REPLACE": "SUBSTITUTE",
    "SUBSTRING": "MID",
    "GETDATE": "NOW",
    "UPPER": "UPPER",
    "LOWER": "LOWER",
    "TRIM": "TRIM",
    "LTRIM": "TRIM",
    "RTRIM": "TRIM",
    "LEN": "LEN",
    "LEFT": "LEFT",
    "RIGHT": "RIGHT",
    "ABS": "ABS",
    "ROUND": "ROUND",
}
# fonctions dont on n'a pas d'equivalent direct -> a valider manuellement
_KNOWN = set(_FUNC_MAP.values()) | {
    "IF", "AND", "OR", "NOT", "ISBLANK", "FIXED", "CONCATENATE", "MOD",
}


def _commas_to_semicolons(expr):
    """Remplace les virgules de separation d'arguments par ';' en respectant
    les chaines entre guillemets."""
    out, in_str, prev = [], False, ""
    for ch in expr:
        if ch == '"' and prev != "\\":
            in_str = not in_str
            out.append(ch)
        elif ch == "," and not in_str:
            out.append(";")
        else:
            out.append(ch)
        prev = ch
    return "".join(out)


def is_string_literal(expr):
    return re.fullmatch(r'\s*"(?:[^"\\]|\\.)*"\s*', expr or "") is not None


def is_number_literal(expr):
    return re.fullmatch(r"\s*-?\d+(?:\.\d+)?\s*", expr or "") is not None


def translate_expression(expr):
    """Retourne (formule_libformula, notes[list]). Best-effort : conserve
    toujours l'expression d'origine pour revue humaine."""
    notes = []
    original = expr or ""
    work = original

    if _CAST_RE.search(work):
        notes.append(
            "cast(s) SSIS supprime(s) : la precision/le format peut differer, a verifier"
        )
        work = _CAST_RE.sub("", work)

    # noms de fonctions
    def repl_func(m):
        fn = m.group(1)
        up = fn.upper()
        if up in _FUNC_MAP:
            return _FUNC_MAP[up] + "("
        if up not in _KNOWN:
            notes.append(f"fonction '{fn}' sans equivalent direct, a valider")
        return fn + "("

    work = re.sub(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", repl_func, work)
    work = _commas_to_semicolons(work)
    work = work.strip()
    return work, notes
