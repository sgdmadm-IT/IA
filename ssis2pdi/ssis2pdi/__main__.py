"""Point d'entree CLI : python -m ssis2pdi <projet|dossier|fichier.dtsx> -o <sortie>."""
import argparse
import os
import sys
import traceback

from . import __version__
from .parser import parse_dtsx, find_packages
from .common import sanitize_filename
from .dataflow import build_dataflow
from .controlflow import build_job
from . import pdi


def convert_package(path, out_dir):
    pkg = parse_dtsx(path)
    # dossier/base de nom bases sur le NOM DE FICHIER (unique), pas l'ObjectName
    stem = os.path.splitext(os.path.basename(path))[0]
    pkg_dir = os.path.join(out_dir, sanitize_filename(stem))
    os.makedirs(pkg_dir, exist_ok=True)
    written, notes = [], []

    pipelines = [e for e in pkg.executables if e.exec_type == "Microsoft.Pipeline"]
    single = len(pipelines) == 1
    ktr_names = {}
    for pl in pipelines:
        base = stem if single else f"{stem}_{pl.name}"
        fname = sanitize_filename(base) + ".ktr"
        ktr_names[pl.refid] = fname
        try:
            trans, dnotes = build_dataflow(pl, pkg, os.path.splitext(fname)[0])
            with open(os.path.join(pkg_dir, fname), "w", encoding="utf-8") as fh:
                fh.write(pdi.to_string(trans))
            written.append(fname)
            notes.extend(dnotes)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"ERREUR sur le Data Flow '{pl.name}' : {exc}")

    try:
        job, jnotes = build_job(pkg, ktr_names)
        jname = sanitize_filename(stem) + ".kjb"
        with open(os.path.join(pkg_dir, jname), "w", encoding="utf-8") as fh:
            fh.write(pdi.to_string(job))
        written.append(jname)
        notes.extend(jnotes)
    except Exception as exc:  # noqa: BLE001
        notes.append(f"ERREUR sur le job : {exc}")

    _write_report(pkg_dir, pkg, written, notes)
    return pkg, written, notes, stem


def _write_report(pkg_dir, pkg, written, notes):
    lines = [f"# Rapport de conversion : {pkg.name}", "",
             f"Source : `{os.path.basename(pkg.path)}`", "",
             "## Fichiers PDI generes", ""]
    lines += [f"- `{w}`" for w in written] or ["- (aucun)"]
    lines += ["", "## Composants du package", ""]
    for ex in pkg.executables:
        flag = " *(desactive)*" if ex.disabled else ""
        lines.append(f"- **{ex.name}** — `{ex.exec_type}`{flag}")
    lines += ["", "## Points a verifier / non convertis", ""]
    if notes:
        lines += [f"- {n}" for n in notes]
    else:
        lines.append("- Aucun point signale (a valider tout de meme dans Spoon).")
    lines += ["", "> Genere automatiquement par ssis2pdi. "
              "Ouvrir chaque fichier dans Spoon et faire un Apercu avant mise en production.", ""]
    with open(os.path.join(pkg_dir, "_RAPPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="ssis2pdi",
        description="Convertit des packages SSIS (.dtsx / .dtproj) en "
                    "transformations et jobs Pentaho Data Integration (.ktr/.kjb).")
    ap.add_argument("input", help="fichier .dtsx, fichier .dtproj ou dossier")
    ap.add_argument("-o", "--out", default="pdi_out", help="dossier de sortie")
    ap.add_argument("--version", action="version", version=f"ssis2pdi {__version__}")
    args = ap.parse_args(argv)

    packages, missing = find_packages(args.input)
    if missing:
        print("Packages declares dans le projet mais introuvables (a fournir) :",
              file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
    if not packages:
        print("Aucun fichier .dtsx trouve.", file=sys.stderr)
        return 1

    os.makedirs(args.out, exist_ok=True)
    summary = ["# Synthese de conversion SSIS -> PDI", "",
               f"{len(packages)} package(s) traite(s).", "",
               "| Fichier source | Package (ObjectName) | Fichiers generes | Points a verifier |",
               "|----------------|----------------------|------------------|-------------------|"]
    total_notes = 0
    for p in packages:
        try:
            pkg, written, notes, stem = convert_package(p, args.out)
            total_notes += len(notes)
            summary.append(f"| {stem}.dtsx | {pkg.name} | {len(written)} | {len(notes)} |")
            print(f"OK  {stem}  ({len(written)} fichiers, {len(notes)} notes)")
        except Exception as exc:  # noqa: BLE001
            summary.append(f"| {os.path.basename(p)} | ERREUR | {exc} |")
            print(f"ERREUR  {p} : {exc}", file=sys.stderr)
            traceback.print_exc()

    if missing:
        summary += ["", "## Packages manquants (declares dans le .dtproj, fichiers absents)", ""]
        summary += [f"- `{m}`" for m in missing]
    summary += ["", f"Total des points a verifier : **{total_notes}**.", ""]
    with open(os.path.join(args.out, "SYNTHESE.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary))
    print(f"\nSortie : {os.path.abspath(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
