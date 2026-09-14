"""Conversion du Control Flow SSIS (executables + contraintes) en job PDI."""
import re

from . import pdi
from . import db
from .common import sanitize_filename


def _fs_resolve(fsd, package, path_attr, isvar_attr):
    val = fsd.get(path_attr)
    if not val:
        return ""
    if fsd.get(isvar_attr, "").lower() == "true":
        return "${" + val.strip("[]") + "}"
    conn = package.conn_by_dtsid.get(val.strip("{}"))
    return conn.conn_string if conn else val


def _entry_move_copy(ex, package, x, copy=False):
    fsd = ex.element.find("./ObjectData/FileSystemData")
    src = _fs_resolve(fsd, package, "TaskSourcePath", "IsSourcePathVariable")
    dst = _fs_resolve(fsd, package, "TaskDestinationPath", "IsDestinationPathVariable")
    etype = "COPY_FILES" if copy else "MOVE_FILES"
    body = [
        ("copy_empty_folders" if copy else "move_empty_folders", "Y"),
        ("arg_from_previous", "N"), ("include_subfolders", "N"),
        ("add_result_filesname", "N"), ("destination_is_a_file", "Y"),
        ("create_destination_folder", "N"), ("overwrite_files", "Y"),
        ("simulate", "N"),
        ("fields", [("field", [
            ("source_filefolder", src),
            ("destination_filefolder", dst),
            ("wildcard", None)])]),
    ]
    return pdi.entry_wrap(ex.name, etype, body, x, 64,
                          f"File System Task SSIS ({fsd.get('TaskOperationType')})")


def _entry_delete(ex, package, x, folder=False):
    fsd = ex.element.find("./ObjectData/FileSystemData")
    src = _fs_resolve(fsd, package, "TaskSourcePath", "IsSourcePathVariable")
    etype = "DELETE_FOLDERS" if folder else "DELETE_FILES"
    body = [
        ("arg_from_previous", "N"), ("include_subfolders", "N"),
        ("fields", [("field", [("name", src), ("filemask", None)])]),
    ]
    return pdi.entry_wrap(ex.name, etype, body, x, 64,
                          f"File System Task SSIS ({fsd.get('TaskOperationType')})")


def build_entry(ex, package, x, ktr_name=None, notes=None):
    """Construit l'entree de job pour un executable. Retourne un Element."""
    notes = notes if notes is not None else []
    t = ex.exec_type

    if t == "Microsoft.Pipeline":
        return pdi.entry_trans(ex.name, ktr_name, x, 64,
                               f"Data Flow SSIS '{ex.name}'")

    if t == "Microsoft.FileSystemTask":
        fsd = ex.element.find("./ObjectData/FileSystemData")
        op = (fsd.get("TaskOperationType") if fsd is not None else "") or ""
        if op == "CopyFile":
            return _entry_move_copy(ex, package, x, copy=True)
        if op in ("MoveFile", "RenameFile"):
            return _entry_move_copy(ex, package, x, copy=False)
        if op == "DeleteFile":
            return _entry_delete(ex, package, x, folder=False)
        if op in ("DeleteDirectory", "DeleteDirectoryContent"):
            return _entry_delete(ex, package, x, folder=True)
        notes.append(f"[{ex.name}] File System Task '{op}' non gere -> Dummy")
        return pdi.entry_wrap(ex.name, "DUMMY", [], x, 64,
                              f"NON CONVERTI : File System Task {op}")

    if t == "Microsoft.ExecuteSQLTask":
        std = ex.element.find("./ObjectData/SqlTaskData")
        sql = std.get("SqlStatementSource", "") if std is not None else ""
        conn = package.conn_by_dtsid.get((std.get("Connection", "") if std is not None else "").strip("{}"))
        cname = conn.name if conn else ""
        if conn:
            notes.append(f"[{ex.name}] entree SQL sur la connexion '{cname}' : "
                         "renseigner les identifiants dans Spoon")
        return pdi.entry_wrap(ex.name, "SQL", [
            ("sql", sql), ("useVariableSubstitution", "F"),
            ("sqlfromfile", "F"), ("sqlfilename", None),
            ("sendOneStatement", "F"), ("connection", cname),
        ], x, 64, "Execute SQL Task SSIS")

    if t == "Microsoft.SendMailTask":
        smd = ex.element.find("./ObjectData/SendMailTaskData")
        smtp_conn = package.conn_by_dtsid.get((smd.get("SMTPServer", "") if smd is not None else "").strip("{}"))
        server = ""
        if smtp_conn:
            m = re.search(r"SmtpServer=([^;]+)", smtp_conn.conn_string, re.IGNORECASE)
            server = m.group(1) if m else smtp_conn.conn_string
        g = smd.get if smd is not None else (lambda *_: "")
        notes.append(f"[{ex.name}] tache d'envoi de mail convertie (verifier le serveur SMTP)")
        return pdi.entry_wrap(ex.name, "MAIL", [
            ("server", server), ("port", "25"),
            ("destination", g("To", "")), ("destinationCc", g("CC", "")),
            ("destinationBCc", g("BCC", "")),
            ("replyto", g("From", "")), ("replyToName", None),
            ("subject", g("Subject", "")),
            ("include_date", "N"), ("contact_person", None),
            ("contact_phone", None), ("comment", g("MessageSource", "")),
            ("encoding", "UTF-8"), ("priority", "normal"),
            ("importance", "normal"), ("sensitivity", "normal"),
            ("useAuth", "N"), ("usexoauth2", "N"), ("useSecAuth", "N"),
        ], x, 64, "Send Mail Task SSIS")

    if t == "Microsoft.ScriptTask":
        lang = ""
        sp = ex.element.find("./ObjectData/ScriptProject")
        if sp is not None:
            lang = sp.get("Language", "")
        notes.append(f"[{ex.name}] Script Task ({lang}) non porte "
                     "(logique .NET a reimplementer si necessaire) -> Dummy")
        return pdi.entry_wrap(ex.name, "DUMMY", [], x, 64,
                              f"NON CONVERTI : Script Task {lang}")

    notes.append(f"[{ex.name}] tache '{t}' non geree -> Dummy")
    return pdi.entry_wrap(ex.name, "DUMMY", [], x, 64, f"NON CONVERTI : {t}")


def build_job(package, ktr_names):
    """package + {pipeline_refid: ktr_filename} -> (job_element, notes[list])."""
    notes = []
    entries = [pdi.entry_start()]
    entry_name = {}          # refid -> nom d'entree
    disabled = {}            # refid -> bool
    x = 240
    for ex in package.executables:
        ent = build_entry(ex, package, x, ktr_names.get(ex.refid), notes)
        entries.append(ent)
        entry_name[ex.refid] = ex.name
        disabled[ex.refid] = ex.disabled
        x += 176

    # graphe des contraintes
    succ = {}
    preds = {}
    edge_meta = {}
    for pc in package.precedences:
        succ.setdefault(pc.from_ref, []).append(pc.to_ref)
        preds.setdefault(pc.to_ref, []).append(pc.from_ref)
        edge_meta[(pc.from_ref, pc.to_ref)] = pc
        if pc.expression:
            notes.append(f"contrainte {entry_name.get(pc.from_ref, pc.from_ref)} -> "
                         f"{entry_name.get(pc.to_ref, pc.to_ref)} : expression SSIS "
                         f"'{pc.expression}' non traduite (hop inconditionnel), a valider")

    def targets(ref, seen=None):
        """successeurs actifs, en court-circuitant les taches desactivees."""
        seen = seen or set()
        out = []
        for s in succ.get(ref, []):
            if s in seen:
                continue
            seen.add(s)
            if disabled.get(s):
                out.extend(targets(s, seen))
            else:
                out.append(s)
        return out

    hops = []

    def hop_flags(pc):
        if pc is None:
            return (True, True, True)          # enabled, unconditional, eval
        if pc.value == "Completion":
            return (True, True, True)
        if pc.value == "Failure":
            return (True, False, False)
        return (True, False, True)             # Success

    for ex in package.executables:
        if disabled.get(ex.refid):
            continue
        for to in targets(ex.refid):
            pc = edge_meta.get((ex.refid, to))
            en, uncond, ev = hop_flags(pc)
            hops.append((ex.name, entry_name[to], en, uncond, ev))

    # racines actives (aucun predecesseur actif) reliees a START
    active = [ex for ex in package.executables if not disabled.get(ex.refid)]
    for ex in active:
        active_preds = [p for p in preds.get(ex.refid, []) if not disabled.get(p)]
        # court-circuit : un predecesseur desactive rend actif via ses propres preds
        def has_active_pred(ref, seen=None):
            seen = seen or set()
            for p in preds.get(ref, []):
                if p in seen:
                    continue
                seen.add(p)
                if disabled.get(p):
                    if has_active_pred(p, seen):
                        return True
                else:
                    return True
            return False
        if not has_active_pred(ex.refid):
            hops.append(("START", ex.name, True, True, True))

    # entrees desactivees : reliees a START via un hop desactive (documentation)
    for ex in package.executables:
        if disabled.get(ex.refid):
            hops.append(("START", ex.name, False, True, True))

    # connexions BD referencees par des taches Execute SQL
    db_conns = {}
    for ex in package.executables:
        if ex.exec_type == "Microsoft.ExecuteSQLTask":
            std = ex.element.find("./ObjectData/SqlTaskData")
            conn = package.conn_by_dtsid.get(
                (std.get("Connection", "") if std is not None else "").strip("{}"))
            if conn:
                meta = db.parse_db(conn)
                db_conns[meta["name"]] = meta
    connections = [db.build_connection_element(m) for m in db_conns.values()]

    params = [{"name": "BASE_DIR", "default": "",
               "desc": "Repertoire de base (a adapter a l'environnement)"}]
    job = pdi.build_job(package.name,
                        f"Control Flow SSIS du package {package.name}.",
                        entries, hops, params=params, connections=connections)
    return job, notes
