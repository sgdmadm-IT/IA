"""Connexions base de donnees : chaine SSIS (OLE DB / ADO.NET) -> DatabaseMeta PDI."""
import re

from . import pdi


def _kv(conn_string):
    out = {}
    for part in (conn_string or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out


def parse_db(conn):
    """Connection SSIS -> dict {name, type, server, database, port, user, ...}."""
    kv = _kv(conn.conn_string)
    data_source = kv.get("data source", "")
    creation = (conn.creation_name or "").lower()

    if "oracle" in creation or "oracle" in kv.get("provider", "").lower():
        # Data Source peut etre "hote/service" ou un alias TNS
        server, _, service = data_source.partition("/")
        return {
            "name": conn.name, "type": "ORACLE", "access": "Native",
            "server": server or data_source, "database": service or data_source,
            "port": "1521", "user": kv.get("user id", ""),
            "password": "", "integrated": False,
            "note": "Oracle : verifier hote/service ou alias TNS et le mot de passe.",
        }

    # par defaut : SQL Server (SQLNCLI / SQLOLEDB / MSOLEDBSQL)
    integrated = "sspi" in kv.get("integrated security", "").lower()
    return {
        "name": conn.name, "type": "MSSQLNATIVE", "access": "Native",
        "server": data_source, "database": kv.get("initial catalog", ""),
        "port": "1433", "user": kv.get("user id", "") or kv.get("uid", ""),
        "password": "", "integrated": integrated,
        "note": ("SQL Server : authentification integree (SSPI) -> renseigner un "
                 "compte ou activer l'auth. integree dans Spoon."
                 if integrated else "SQL Server : renseigner le mot de passe."),
    }


def build_connection_element(meta):
    """dict -> Element <connection> Kettle."""
    attrs = [("code", "PORT_NUMBER"), ("attribute", meta.get("port", ""))]
    attributes = [("attribute", [("code", "PORT_NUMBER"),
                                 ("attribute", meta.get("port", ""))])]
    if meta.get("integrated") and meta["type"].startswith("MSSQL"):
        attributes.append(("attribute", [("code", "MSSQLUseIntegratedSecurity"),
                                          ("attribute", "true")]))
    return pdi.E("connection", [
        ("name", meta["name"]),
        ("server", meta.get("server", "")),
        ("type", meta["type"]),
        ("access", meta.get("access", "Native")),
        ("database", meta.get("database", "")),
        ("port", meta.get("port", "")),
        ("username", meta.get("user", "")),
        ("password", meta.get("password", "")),
        ("servername", None),
        ("data_tablespace", None), ("index_tablespace", None),
        ("attributes", attributes),
    ])
