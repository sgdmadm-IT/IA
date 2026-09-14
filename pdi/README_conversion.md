# Conversion SSIS → PDI : `PR_GEELY_FR`

Conversion du package `PR_GEELY_FR.dtsx` (SSIS) vers Pentaho Data Integration (Kettle).

- `PR_GEELY_FR.ktr` — la transformation (l'ancien **Data Flow "BYD"**)
- `PR_GEELY_FR.kjb` — le job (l'ancien **Control Flow**)

## Correspondance des composants

### Job (`.kjb`) ← Control Flow SSIS

| SSIS | PDI | Remarque |
|------|-----|----------|
| `Test présence du fichier SEAT` (Script Task VB.NET) | `Test presence BYD.xls` (**File Exists**) | **Désactivée** dans le package → hop désactivé côté PDI (la transfo tourne quand même) |
| Data Flow `BYD` | Job entry **Transformation** → `PR_GEELY_FR.ktr` | |
| `Copie … I'COM SEAT` (File System Task, MoveFile) | **Move Files** | déplace `byd.csv` → `…\SEAT\A INTEGRER\498.csv` |
| `Suppression … SEAT` (File System Task, DeleteFile) | **Delete Files** | supprime `…\Source\498.xls` |
| Precedence constraints | hops | |

### Transformation (`.ktr`) ← Data Flow "BYD"

| SSIS | PDI |
|------|-----|
| `Source BYD` (Excel Source, `BYD.xls`, feuille `Feuil1$`) | **Microsoft Excel Input** (`ExcelInput`, moteur JXL pour `.xls`) |
| `Conversion de données 1` (Data Conversion) | **Select Values** (renommage + typage) |
| `Colonne dérivée 2` (Derived Column) — `DEVISE`, `TYPE_COMMANDE` | **Add constants** |
| `Colonne dérivée 2` — `PA_UNITAIRE` | **Formula** |
| `BYD` (Flat File Destination, `byd.csv`) | **Text file output** |

### Format du fichier de sortie `byd.csv`
Délimiteur `;`, pas de qualificateur de texte, ligne d'en-tête, CRLF, encodage **Windows-1252**, écrasement.
Colonnes, dans l'ordre : `NUMERO_BL;DATE_BL;TYPE_COMMANDE;REFERENCE LIVREE;QTE_LIVREE;PX_ACHAT_UNITAIRE;DEVISE;NUM_COMMANDE`

### Mapping des champs (Excel → CSV)

| Excel | → sortie | Transformation |
|-------|----------|----------------|
| `FACTURE` | `NUMERO_BL` | typé entier |
| `date` | `DATE_BL` | chaîne(8) |
| — | `TYPE_COMMANDE` | constante `"A"` |
| `Référence` | `REFERENCE LIVREE` (renommé `REFERENCE_LIVREE`) | |
| `quantité` | `QTE_LIVREE` | typé entier |
| `montant unitaire` | `PX_ACHAT_UNITAIRE` | `SUBSTITUTE(FIXED([montant_unitaire];2;TRUE());",";".")` = SSIS `REPLACE(…,",",".")` |
| — | `DEVISE` | constante `"EUR"` |
| `COMMANDE` | `NUM_COMMANDE` | typé entier |
| `FOURNISSEUR` | *(non écrit)* | comme dans le package d'origine |

## Points à valider dans Spoon (à ne pas négliger)

1. **Ouvrir chaque fichier dans Spoon** et faire *Aperçu* sur `Source BYD` puis sur `byd.csv`. Le format XML est correct mais les chemins/valeurs sont à confirmer sur des données réelles.
2. **`.xls` ancien format** : le step utilise le moteur `JXL`. Si les fichiers sont en réalité `.xlsx`, passer à `POI`/`SAX_POI`.
3. **Colonne `date`** : Excel stocke souvent les dates en numérique (numéro de série). SSIS la stringifiait telle quelle (r8 → chaîne). Vérifier que `DATE_BL` sort au bon format (sinon ajouter un formatage de date).
4. **`PX_ACHAT_UNITAIRE`** : `FIXED` peut être sensible à la locale. Alternative sûre si besoin : *Select values* format `0.00` + *Replace in string* `,`→`.`.
5. **Incohérences héritées du modèle SEAT** (présentes dans le `.dtsx` d'origine, reproduites à l'identique) :
   - lit `BYD.xls` / écrit `byd.csv`, mais **déplace vers le dossier SEAT** (`498.csv`) et **supprime `498.xls`**.
   - À corriger si le comportement attendu est 100 % BYD.
6. **Chemins UNC / lecteurs `C:`** : externalisés en paramètres (`${SOURCE_XLS}`, `${DEST_CSV_DIR}`, etc.) — à adapter à l'environnement d'exécution du serveur PDI (Linux/Windows).
7. **Script Task VB.NET désactivé** : non porté (il était inactif). S'il doit être réactivé, sa logique de test de présence est déjà couverte par le step *File Exists* fourni.
