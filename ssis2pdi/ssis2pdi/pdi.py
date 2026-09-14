"""Construction du XML Kettle (transformations .ktr et jobs .kjb)."""
import xml.etree.ElementTree as ET

DATE0 = "2026/01/01 00:00:00.000"


def E(tag, content=None):
    """Construit un element ET.
    content : str/nombre (texte), None (vide), ou liste de (tag, content) /
    Element (enfants ordonnes, tags repetables autorises)."""
    e = ET.Element(tag)
    if content is None:
        return e
    if isinstance(content, (str, int, float)):
        e.text = str(content)
        return e
    for child in content:
        if isinstance(child, ET.Element):
            e.append(child)
        else:
            ct, cc = child
            e.append(E(ct, cc))
    return e


def _gui(x, y):
    return E("GUI", [("xloc", x), ("yloc", y), ("draw", "Y")])


def _remotesteps():
    return E("remotesteps", [("input", None), ("output", None)])


def _partition():
    return E("partitioning", [("method", "none"), ("schema_name", None)])


def to_string(elem):
    ET.indent(elem, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + \
        ET.tostring(elem, encoding="unicode")


# --------------------------------------------------------------------------
# Transformation (.ktr)
# --------------------------------------------------------------------------
def build_transformation(name, description, steps, hops, params=None, notes=None,
                         connections=None):
    """steps : liste d'Element <step>. hops : liste de (from, to).
    connections : liste d'Element <connection> (bases de donnees)."""
    info = E("info", [
        ("name", name),
        ("description", description or ""),
        ("extended_description", None),
        ("trans_version", None),
        ("trans_type", "Normal"),
        ("directory", "/"),
        ("parameters", [("parameter", [
            ("name", p["name"]),
            ("default_value", p.get("default", "")),
            ("description", p.get("desc", "")),
        ]) for p in (params or [])]),
        ("log", None),
        ("maxdate", [("connection", None), ("table", None), ("field", None),
                     ("offset", "0.0"), ("maxdiff", "0.0")]),
        ("size_rowset", "10000"),
        ("sleep_time_empty", "50"),
        ("sleep_time_full", "50"),
        ("unique_connections", "N"),
        ("feedback_shown", "Y"),
        ("feedback_size", "50000"),
        ("using_thread_priorities", "Y"),
        ("shared_objects_file", None),
        ("capture_step_performance", "N"),
        ("dependencies", None),
        ("partitionschemas", None),
        ("slaveservers", None),
        ("clusterschemas", None),
        ("created_user", "-"), ("created_date", DATE0),
        ("modified_user", "-"), ("modified_date", DATE0),
    ])

    order = E("order", [("hop", [("from", f), ("to", t), ("enabled", "Y")])
                        for f, t in hops])

    trans = E("transformation", [info])
    trans.append(E("notepads", [_notepad(n, i) for i, n in enumerate(notes or [])]))
    for conn in (connections or []):
        trans.append(conn)
    trans.append(order)
    for s in steps:
        trans.append(s)
    trans.append(E("step_error_handling"))
    trans.append(E("slave-step-copy-partition-distribution"))
    trans.append(E("slave_transformation", "N"))
    return trans


def _notepad(text, i):
    return E("notepad", [
        ("note", text), ("xloc", 20), ("yloc", 20 + i * 90),
        ("width", 420), ("heigth", 70),
        ("fontname", "Segoe UI"), ("fontsize", 9),
        ("fontbold", "N"), ("fontitalic", "N"),
        ("fontcolorred", 14), ("fontcolorgreen", 58), ("fontcolorblue", 90),
        ("backgroundcolorred", 201), ("backgroundcolorgreen", 232),
        ("backgroundcolorblue", 251),
        ("bordercolorred", 14), ("bordercolorgreen", 58), ("bordercolorblue", 90),
        ("drawshadow", "Y"),
    ])


# --------------------------------------------------------------------------
# Steps de transformation
# --------------------------------------------------------------------------
def step_wrap(name, step_type, body, x, y, description=""):
    content = [
        ("name", name), ("type", step_type), ("description", description),
        ("distribute", "Y"), ("custom_distribution", None), ("copies", "1"),
    ]
    e = E("step", content)
    e.append(_partition())
    for child in body:
        if isinstance(child, ET.Element):
            e.append(child)
        else:
            ct, cc = child
            e.append(E(ct, cc))
    e.append(E("cluster_schema"))
    e.append(_remotesteps())
    e.append(_gui(x, y))
    return e


def step_dummy(name, x, y, description=""):
    return step_wrap(name, "Dummy", [], x, y, description)


# --------------------------------------------------------------------------
# Job (.kjb)
# --------------------------------------------------------------------------
def build_job(name, description, entries, hops, params=None, connections=None):
    content = [
        ("name", name),
        ("description", description or ""),
        ("extended_description", None),
        ("job_version", None),
        ("directory", "/"),
        ("created_user", "-"), ("created_date", DATE0),
        ("modified_user", "-"), ("modified_date", DATE0),
        ("parameters", [("parameter", [
            ("name", p["name"]),
            ("default_value", p.get("default", "")),
            ("description", p.get("desc", "")),
        ]) for p in (params or [])]),
        ("slaveservers", None),
    ]
    job = E("job", content)
    for conn in (connections or []):
        job.append(conn)
    job.append(E("job-log-table", [
        ("connection", None), ("schema", None), ("table", None),
        ("size_limit_lines", None), ("interval", None), ("timeout_days", None)]))
    je = E("jobentries")
    for ent in entries:
        je.append(ent)
    job.append(je)
    job.append(E("hops", [_job_hop(h) for h in hops]))
    job.append(E("notepads"))
    job.append(E("attributes"))
    return job


def _job_hop(h):
    f, t, enabled, unconditional, evaluation = h
    return E("hop", [
        ("from", f), ("to", t), ("from_nr", 0), ("to_nr", 0),
        ("enabled", "Y" if enabled else "N"),
        ("evaluation", "Y" if evaluation else "N"),
        ("unconditional", "Y" if unconditional else "N")])


def entry_wrap(name, entry_type, body, x, y, description=""):
    content = [("name", name), ("description", description), ("type", entry_type)]
    e = E("entry", content)
    for child in body:
        if isinstance(child, ET.Element):
            e.append(child)
        else:
            ct, cc = child
            e.append(E(ct, cc))
    e.append(E("parallel", "N"))
    e.append(E("draw", "Y"))
    e.append(E("nr", 0))
    e.append(E("xloc", x))
    e.append(E("yloc", y))
    return e


def entry_start(x=64, y=64):
    return entry_wrap("START", "SPECIAL", [
        ("start", "Y"), ("dummy", "N"), ("repeat", "N"),
        ("schedulerType", 0), ("intervalSeconds", 0), ("intervalMinutes", 60),
        ("hour", 12), ("minutes", 0), ("weekDay", 1), ("DayOfMonth", 1),
    ], x, y)


def entry_trans(name, ktr_filename, x, y, description=""):
    return entry_wrap(name, "TRANS", [
        ("specification_method", "filename"),
        ("trans_object_id", None),
        ("filename", "${Internal.Entry.Current.Directory}/" + ktr_filename),
        ("transname", None), ("directory", None),
        ("arg_from_previous", "N"), ("params_from_previous", "N"),
        ("exec_per_row", "N"), ("clear_rows", "N"), ("clear_files", "N"),
        ("set_logfile", "N"), ("logfile", None), ("logext", None),
        ("add_date", "N"), ("add_time", "N"), ("loglevel", "Basic"),
        ("cluster", "N"), ("slave_server_name", None),
        ("set_append_logfile", "N"), ("wait_until_finished", "Y"),
        ("follow_abort_remote", "N"), ("create_parent_folder", "N"),
        ("run_configuration", None),
        ("parameters", [("pass_all_parameters", "Y")]),
    ], x, y, description)
