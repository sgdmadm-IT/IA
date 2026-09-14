# Rapport de conversion : PR_GEELY_FR

Source : `PR_GEELY_FR.dtsx`

## Fichiers PDI generes

- `PR_GEELY_FR.ktr`
- `PR_GEELY_FR.kjb`

## Composants du package

- **BYD** — `Microsoft.Pipeline`
- **Copie du fichier à intégrer dans le répertoire attendu par I'COM SEAT** — `Microsoft.FileSystemTask`
- **Suppression du fichier Acknow PR Initial SEAT** — `Microsoft.FileSystemTask`
- **Test présence du fichier SEAT** — `Microsoft.ScriptTask` *(desactive)*

## Points a verifier / non convertis

- [Colonne dérivée 2.DEVISE] expression SSIS d'origine : "EUR"
- [Colonne dérivée 2.TYPE_COMMANDE] expression SSIS d'origine : "A"
- [Colonne dérivée 2.PA_UNITAIRE] cast(s) SSIS supprime(s) : la precision/le format peut differer, a verifier
- [Colonne dérivée 2.PA_UNITAIRE] expression SSIS d'origine : REPLACE((DT_WSTR,9)((DT_NUMERIC,7,2)((DT_DECIMAL,2)[Copie de montant unitaire])),",",".")
- [Test présence du fichier SEAT] Script Task (VisualBasic) non porte (logique .NET a reimplementer si necessaire) -> Dummy
- contrainte Test présence du fichier SEAT -> BYD : expression SSIS '@[User::Test_Fichier_BYD]==TRUE' non traduite (hop inconditionnel), a valider

> Genere automatiquement par ssis2pdi. Ouvrir chaque fichier dans Spoon et faire un Apercu avant mise en production.
