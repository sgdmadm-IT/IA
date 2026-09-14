# Rapport de conversion : PR_BYD_2

Source : `PR_BYD_2.dtsx`

## Fichiers PDI generes

- `PR_BYD_2.ktr`
- `PR_BYD_2.kjb`

## Composants du package

- **BYD** — `Microsoft.Pipeline`
- **Copie du fichier à intégrer dans le répertoire attendu par I'COM SEAT** — `Microsoft.FileSystemTask`
- **Suppression du fichier Acknow PR Initial SEAT** — `Microsoft.FileSystemTask`
- **Test présence du fichier SEAT** — `Microsoft.ScriptTask` *(desactive)*

## Points a verifier / non convertis

- [Colonne dérivée.DEVISE] expression SSIS d'origine : "EUR"
- [Colonne dérivée.TYPE_COMMANDE] expression SSIS d'origine : "A"
- [Test présence du fichier SEAT] Script Task (VisualBasic) non porte (logique .NET a reimplementer si necessaire) -> Dummy
- contrainte Test présence du fichier SEAT -> BYD : expression SSIS '@[User::Test_Fichier_BYD]==TRUE' non traduite (hop inconditionnel), a valider

> Genere automatiquement par ssis2pdi. Ouvrir chaque fichier dans Spoon et faire un Apercu avant mise en production.
