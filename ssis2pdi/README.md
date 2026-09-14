# ssis2pdi — convertisseur SSIS → Pentaho Data Integration

Convertit des packages **SSIS** (`.dtsx`, projet `.dtproj`) en transformations et
jobs **Pentaho Data Integration / Kettle** (`.ktr` / `.kjb`).

- **Zéro dépendance** : Python 3.8+ (bibliothèque standard uniquement).
- Génère, pour chaque package : un job `.kjb`, une transformation `.ktr` par Data Flow,
  et un **rapport de conversion** listant tout ce qui doit être vérifié à la main.
- Conçu pour être **étendu** : ajouter un composant SSIS = ajouter une fonction dans un dictionnaire.

## Utilisation

```bash
# Un package
python -m ssis2pdi chemin/vers/PR_GEELY_FR.dtsx -o pdi_out

# Tout un projet (.dtproj) ou un dossier entier
python -m ssis2pdi chemin/vers/MonProjet.dtproj -o pdi_out
python -m ssis2pdi chemin/vers/dossier_dtsx/    -o pdi_out
```

Sortie dans `pdi_out/` :

```
pdi_out/
  SYNTHESE.md                 <- tableau récapitulatif (packages, nb de fichiers, nb de points à vérifier)
  <Package>/
    <Package>.kjb             <- le job (Control Flow)
    <Package>.ktr             <- la/les transformation(s) (Data Flow)
    _RAPPORT.md               <- correspondances + points à vérifier pour CE package
```

## Correspondances gérées

### Control Flow → Job (`.kjb`)

| SSIS | PDI |
|------|-----|
| `Microsoft.Pipeline` (Data Flow) | entrée **Transformation** + `.ktr` généré |
| `Microsoft.FileSystemTask` — MoveFile / RenameFile | **Move Files** |
| `Microsoft.FileSystemTask` — CopyFile | **Copy Files** |
| `Microsoft.FileSystemTask` — DeleteFile | **Delete Files** |
| `Microsoft.FileSystemTask` — DeleteDirectory | **Delete Folders** |
| `Microsoft.ExecuteSQLTask` | **SQL** (+ connexion BD) |
| `Microsoft.SendMailTask` | **Mail** |
| `Microsoft.ScriptTask` | **Dummy** + note (logique .NET à reporter) |
| Precedence constraints | hops (Success / Failure / Completion) |
| Tâche `Disabled="True"` | court-circuitée (hop désactivé, flux rerouté) |

### Data Flow → Transformation (`.ktr`)

| SSIS | PDI |
|------|-----|
| `Microsoft.ExcelSource` | **Microsoft Excel Input** (JXL pour `.xls`, POI pour `.xlsx`) |
| `Microsoft.FlatFileSource` | **CSV file input** |
| `Microsoft.OLEDBSource` / source ADO.NET (`ManagedComponentHost`) | **Table input** (+ connexion BD) |
| `Microsoft.DataConvert` | **Select values** (typage + renommage) |
| `Microsoft.DerivedColumn` | **Formula** (expressions traduites au mieux) |
| `Microsoft.Sort` | **Sort rows** |
| `Microsoft.Multicast` | **Dummy** (copie vers plusieurs sorties) |
| `Microsoft.UnionAll` | **Dummy** (fusion des flux entrants) |
| `Microsoft.FlatFileDestination` | **Select values** (mapping) + **Text file output** |
| `Microsoft.OLEDBDestination` | **Table output** (+ connexion BD) |
| `Microsoft.ConditionalSplit` | **Dummy** + note (conditions listées, routage à refaire) |
| `Microsoft.Lookup` | **Dummy** + note (requête de référence conservée) |
| autre composant | **Dummy** + note (à implémenter) |

Les chaînes de connexion (chemins UNC, `Data Source=` Jet/Excel), délimiteurs,
encodages (CodePage → charset) et qualificateurs de texte sont repris du package.

**Connexions base de données** : les connexions OLE DB (SQL Server) et ADO.NET
(Oracle) sont converties en `DatabaseMeta` PDI (type, serveur, base, port) et
référencées par les steps Table input/output et les entrées SQL. Les
**identifiants sont à renseigner dans Spoon** (auth. intégrée SSPI, mots de passe).

## Limites connues (toujours signalées dans `_RAPPORT.md`)

1. **Expressions Derived Column** : traduites vers libformula au mieux
   (`REPLACE`→`SUBSTITUTE`, `,`→`;`, casts `DT_*` retirés). Les formatages liés
   aux casts (précision, nombre de décimales) sont **à revérifier**.
2. **Script Tasks** (VB.NET/C#) : non portées → `Dummy` + note.
3. **Expressions de contraintes de précédence** : le hop est créé mais la
   condition n'est pas traduite (à recréer via un step/entrée de test).
4. **Lookup** et **Conditional Split** : générés en `Dummy` + note (la requête de
   référence / les conditions sont conservées dans le rapport). À recréer avec
   *Database lookup* / *Stream lookup* et *Filter rows* / *Switch-Case*.
5. **Connexions BD** : type/serveur/base convertis, mais identifiants et
   éventuels drivers (SQL Server natif, Oracle) à finaliser dans Spoon.
6. Autres composants (Aggregate, Pivot, Script Component…) → `Dummy` + note.
   Points d'extension prêts dans `dataflow.py` (dict `HANDLERS`) et
   `controlflow.py` (`build_entry`).

> ⚠️ Le XML généré est conforme au schéma Kettle et bien formé, mais **doit être
> ouvert dans Spoon** (aperçu source + sortie) avant toute mise en production.

## Architecture

```
ssis2pdi/
  __main__.py     CLI + orchestration (parcours projet, écriture fichiers/rapports)
  parser.py       lecture .dtsx/.dtproj -> modèle (connexions, variables, exécutables, contraintes)
  common.py       tables de types SSIS->PDI, traduction d'expressions, utilitaires
  pdi.py          construction du XML Kettle (transformation, job, steps, entrées)
  dataflow.py     handlers de composants Data Flow  (dict HANDLERS)
  controlflow.py  handlers de tâches Control Flow    (build_entry) + graphe des hops
```

### Ajouter un composant

```python
# dans dataflow.py
def h_mon_composant(comp, package, x):
    ...
    return {"steps": [step], "hops": [], "input": nom_step, "output": nom_step, "notes": []}

HANDLERS["Microsoft.MonComposant"] = h_mon_composant
```
