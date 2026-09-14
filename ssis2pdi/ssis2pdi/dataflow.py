"""Conversion d'un Data Flow SSIS (Microsoft.Pipeline) en transformation PDI."""
import os
import re

from . import pdi
from .common import ssis_type_to_pdi, translate_expression, is_string_literal

_BRACKET = re.compile(r"\[([^\]]+)\]")


def _last_bracket(s):
    """Renvoie le contenu du dernier [...] (ex. ...Columns[FOURNISSEUR] -> FOURNISSEUR)."""
    matches = _BRACKET.findall(s or "")
    return matches[-1] if matches else (s or "")


def _default_output(comp):
    for out in comp.findall("./outputs/output"):
        if out.get("isErrorOut") == "true":
            continue
        if "erreur" in (out.get("name", "").lower()) or "error" in out.get("name", "").lower():
            continue
        return out
    outs = comp.findall("./outputs/output")
    return outs[0] if outs else None


def _prop(comp_or_col, name):
    for p in comp_or_col.findall("./properties/property"):
        if p.get("name") == name:
            return p.text
    return None


def _conn_for(comp, package):
    conn = comp.find("./connections/connection")
    if conn is None:
        return None
    cid = conn.get("connectionManagerID") or conn.get("connectionManagerRefId")
    return package.connections.get(cid)


# --------------------------------------------------------------------------
# Handlers : (comp, package, base_x) -> dict(steps, hops, input, output, notes)
# --------------------------------------------------------------------------
def _excel_path(conn_string):
    """Extrait le chemin du fichier d'une chaine de connexion Excel/Jet OLE DB."""
    if not conn_string:
        return ""
    m = re.search(r"Data Source\s*=\s*([^;]+)", conn_string, re.IGNORECASE)
    return (m.group(1) if m else conn_string).strip()


def h_excel_source(comp, package, x):
    name = comp.get("name")
    conn = _conn_for(comp, package)
    path = _excel_path(conn.conn_string) if conn else ""
    sheet = (_prop(comp, "OpenRowset") or "Feuil1$").rstrip("$")
    ext = os.path.splitext(path)[1].lower()
    sheet_type = "POI" if ext == ".xlsx" else "JXL"

    fields = []
    for c in _default_output(comp).findall("./outputColumns/outputColumn"):
        pdi_t = ssis_type_to_pdi(c.get("dataType"))
        fields.append(("field", [
            ("name", c.get("name")), ("type", pdi_t),
            ("length", c.get("length", "-1") if pdi_t == "String" else "-1"),
            ("precision", "-1"), ("trim_type", "both" if pdi_t == "String" else "none"),
            ("repeat", "N"), ("format", None), ("currency", None),
            ("decimal", None), ("group", None)]))

    body = [
        ("header", "Y"), ("noempty", "Y"), ("stoponempty", "N"),
        ("filefield", None), ("sheetfield", None), ("sheetrowsfield", None),
        ("rownumfield", None), ("sheetfield_len", 0), ("filefield_len", 0),
        ("limit", 0), ("encoding", None),
        ("add_to_result_filenames", "Y"), ("accept_filenames", "N"),
        ("accept_field", None), ("accept_stepname", None),
        ("file", [("name", path), ("filemask", None), ("exclude_filemask", None),
                  ("file_required", "N"), ("include_subfolders", "N")]),
        ("fields", fields),
        ("sheets", [("sheet", [("name", sheet), ("startrow", 0), ("startcol", 0)])]),
        ("strict_types", "N"), ("error_ignored", "N"), ("error_line_skipped", "N"),
        ("spreadsheet_type", sheet_type),
    ]
    step = pdi.step_wrap(name, "ExcelInput", body, x, 144,
                         "Source Excel SSIS -> " + (path or "?"))
    return {"steps": [step], "hops": [], "input": None, "output": name, "notes": []}


def h_flatfile_source(comp, package, x):
    name = comp.get("name")
    conn = _conn_for(comp, package)
    path = conn.conn_string if conn else ""
    sep = conn.delimiter if conn else ";"
    enc = conn.codepage if conn else ""
    fields = []
    for c in _default_output(comp).findall("./outputColumns/outputColumn"):
        pdi_t = ssis_type_to_pdi(c.get("dataType"))
        fields.append(("field", [
            ("name", c.get("name")), ("type", pdi_t),
            ("format", None), ("currency", None), ("decimal", None),
            ("group", None), ("length", c.get("length", "-1")),
            ("precision", "-1"), ("trim_type", "both")]))
    body = [
        ("separator", sep), ("enclosure", conn.qualifier if conn else ""),
        ("enclosure_breaks", "N"), ("escapechar", None), ("header", "Y"),
        ("nr_headerlines", 1), ("footer", "N"), ("noempty", "Y"),
        ("include", "N"), ("include_field", None), ("rownum", "N"),
        ("rownumByFile", "N"), ("rownum_field", None), ("format", "mixed"),
        ("encoding", enc), ("length", "Characters"),
        ("add_filename_result", "N"),
        ("file", [("name", path), ("filemask", None), ("exclude_filemask", None),
                  ("file_required", "N"), ("include_subfolders", "N"),
                  ("type", "CSV"), ("compression", "None")]),
        ("filters", None),
        ("fields", fields),
        ("limit", 0),
    ]
    step = pdi.step_wrap(name, "CsvInput", body, x, 144,
                         "Source fichier plat SSIS -> " + (path or "?"))
    return {"steps": [step], "hops": [], "input": None, "output": name, "notes": []}


def h_data_convert(comp, package, x):
    name = comp.get("name")
    meta = []
    for c in _default_output(comp).findall("./outputColumns/outputColumn"):
        src = _last_bracket(_prop(c, "SourceInputColumnLineageID") or "")
        out = c.get("name")
        pdi_t = ssis_type_to_pdi(c.get("dataType"))
        meta.append(("field", [
            ("name", src), ("rename", out), ("type", pdi_t),
            ("length", c.get("length", "-2") if pdi_t == "String" else "-2"),
            ("precision", "-2"), ("conversion_mask", None),
            ("date_format_lenient", "false"), ("date_format_locale", None),
            ("date_format_timezone", None), ("lenient_string_to_number", "false"),
            ("encoding", None), ("decimal_symbol", None),
            ("grouping_symbol", None), ("currency_symbol", None),
            ("storage_type", None)]))
    body = [("fields", [("select_unspecified", "N"), ("meta", meta)])]
    step = pdi.step_wrap(name, "SelectValues", body, x, 144,
                         "Conversion de donnees SSIS (typage/renommage)")
    return {"steps": [step], "hops": [], "input": name, "output": name, "notes": []}


def h_derived_column(comp, package, x):
    name = comp.get("name")
    formulas, notes = [], []
    for c in _default_output(comp).findall("./outputColumns/outputColumn"):
        out = c.get("name")
        expr = _prop(c, "FriendlyExpression") or _prop(c, "Expression") or ""
        f, ns = translate_expression(expr)
        notes.extend(f"[{name}.{out}] {n}" for n in ns)
        notes.append(f"[{name}.{out}] expression SSIS d'origine : {expr}")
        pdi_t = ssis_type_to_pdi(c.get("dataType"))
        formulas.append(("formula", [
            ("field_name", out), ("formula_string", f),
            ("value_type", pdi_t),
            ("value_length", c.get("length", "-1") if pdi_t == "String" else "-1"),
            ("value_precision", "-1"), ("replace_field", None)]))
    body = [("formula", formulas)]
    step = pdi.step_wrap(name, "Formula", body, x, 144,
                         "Colonne derivee SSIS -> Formula (verifier les expressions)")
    return {"steps": [step], "hops": [], "input": name, "output": name, "notes": notes}


def h_flatfile_destination(comp, package, x):
    name = comp.get("name")
    conn = _conn_for(comp, package)
    inp = comp.find("./inputs/input")
    # mapping colonne de flux -> colonne du fichier (nom externe)
    ext_by_refid = {ec.get("refId"): ec.get("name")
                    for ec in inp.findall("./externalMetadataColumns/externalMetadataColumn")}
    ext_meta = {ec.get("name"): ec
                for ec in inp.findall("./externalMetadataColumns/externalMetadataColumn")}
    rename, mapped = [], {}
    for ic in inp.findall("./inputColumns/inputColumn"):
        stream = ic.get("cachedName") or _last_bracket(ic.get("lineageId", ""))
        ext = ext_by_refid.get(ic.get("externalMetadataColumnId")) \
            or _last_bracket(ic.get("externalMetadataColumnId", ""))
        rename.append(("field", [("name", stream), ("rename", ext)]))
        mapped[ext] = ic

    sel = pdi.step_wrap(name + " (mapping)", "SelectValues",
                        [("fields", rename)], x, 144,
                        "Mapping flux -> colonnes du fichier de sortie")

    # colonnes de sortie dans l'ordre du connection manager
    order = [c.name for c in conn.columns] if conn and conn.columns else list(mapped)
    for ext in mapped:
        if ext not in order:
            order.append(ext)
    conn_col = {c.name: c for c in (conn.columns if conn else [])}
    out_fields = []
    for col in order:
        if col not in mapped:
            continue
        c = conn_col.get(col)
        pdi_t = ssis_type_to_pdi(c.dtype if c else None)
        if pdi_t not in ("String", "Integer", "Number", "BigNumber"):
            pdi_t = "String"
        out_fields.append(("field", [
            ("name", col), ("type", pdi_t),
            ("format", "#" if pdi_t == "Integer" else None),
            ("currency", None), ("decimal", None), ("group", None),
            ("nullif", None), ("trim_type", "none"),
            ("length", (c.length if c else "-1")),
            ("precision", "0" if pdi_t == "Integer" else "-1")]))

    path = conn.conn_string if conn else ""
    base, ext = os.path.splitext(path)
    overwrite = (_prop(comp, "Overwrite") or "true").lower() == "true"
    body = [
        ("separator", conn.delimiter if conn else ";"),
        ("enclosure", conn.qualifier if conn else ""),
        ("enclosure_forced", "N"), ("enclosure_fix_disabled", "Y"),
        ("header", "Y"), ("footer", "N"), ("format", "CRLF"),
        ("compression", "None"), ("encoding", conn.codepage if conn else ""),
        ("endedLine", None), ("fileNameInField", "N"), ("fileNameField", None),
        ("create_parent_folder", "Y"),
        ("file", [("name", base), ("servlet_output", "N"),
                  ("do_not_open_new_file_init", "N"),
                  ("extention", ext.lstrip(".") or "csv"),
                  ("append", "N" if overwrite else "Y"), ("split", "N"),
                  ("haspartno", "N"), ("add_date", "N"), ("add_time", "N"),
                  ("SpecifyFormat", "N"), ("date_time_format", None),
                  ("add_to_result_filenames", "Y"), ("pad", "N"),
                  ("fast_dump", "N"), ("splitevery", 0)]),
        ("fields", out_fields),
    ]
    out = pdi.step_wrap(name, "TextFileOutput", body, x + 170, 144,
                        "Destination fichier plat SSIS -> " + (path or "?"))
    return {"steps": [sel, out], "hops": [(name + " (mapping)", name)],
            "input": name + " (mapping)", "output": None, "notes": []}


HANDLERS = {
    "Microsoft.ExcelSource": h_excel_source,
    "Microsoft.FlatFileSource": h_flatfile_source,
    "Microsoft.DataConvert": h_data_convert,
    "Microsoft.DerivedColumn": h_derived_column,
    "Microsoft.FlatFileDestination": h_flatfile_destination,
}


def h_unsupported(comp, package, x):
    cls = comp.get("componentClassID", "?")
    name = comp.get("name")
    step = pdi.step_dummy(name, x, 144,
                          f"NON CONVERTI : composant SSIS {cls} - a implementer manuellement")
    return {"steps": [step], "hops": [], "input": name, "output": name,
            "notes": [f"[{name}] composant non supporte : {cls} (etape Dummy generee)"]}


def build_dataflow(pipeline_exec, package, ktr_name):
    """Retourne (transformation_element, notes[list])."""
    pipeline = pipeline_exec.element.find("./ObjectData/pipeline")
    comps = pipeline.findall("./components/component")
    steps, hops, notes = [], [], []
    io = {}   # component refId -> (input_step, output_step)

    for i, comp in enumerate(comps):
        cls = comp.get("componentClassID")
        handler = HANDLERS.get(cls, h_unsupported)
        res = handler(comp, package, 150 + i * 200)
        steps.extend(res["steps"])
        hops.extend(res["hops"])
        notes.extend(res["notes"])
        io[comp.get("refId")] = (res["input"], res["output"])

    for path in pipeline.findall("./paths/path"):
        start = path.get("startId", "").split(".Outputs")[0]
        end = path.get("endId", "").split(".Inputs")[0]
        src = io.get(start, (None, None))[1]
        dst = io.get(end, (None, None))[0]
        if src and dst:
            hops.append((src, dst))

    params = [
        {"name": "SOURCE_DIR", "default": "",
         "desc": "Repertoire source (a adapter)"},
    ]
    trans = pdi.build_transformation(
        ktr_name, f"Data Flow SSIS '{pipeline_exec.name}' (package {package.name}).",
        steps, hops, params=params,
        notes=[f"Converti automatiquement depuis {os.path.basename(package.path)} "
               f"(Data Flow '{pipeline_exec.name}'). Verifier dans Spoon."])
    return trans, notes
