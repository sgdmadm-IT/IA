# Rapport de conversion : PR_HYUNDAI_MIAMI

Source : `PR_HYUNDAI_MIAMI.dtsx`

## Fichiers PDI generes

- `PR_HYUNDAI_MIAMI_RECUPERATION_COMMANDE_ICAR.ktr`
- `PR_HYUNDAI_MIAMI_Table_Facture_HYU_MIAMI.ktr`
- `PR_HYUNDAI_MIAMI_Table_Facture_HYU_MIAMI_1.ktr`
- `PR_HYUNDAI_MIAMI.kjb`

## Composants du package

- **Copie du fichier à intégrer dans le répertoire attendu par I'COM HYUNDAI** — `Microsoft.FileSystemTask`
- **RECUPERATION COMMANDE ICAR** — `Microsoft.Pipeline` *(desactive)*
- **Suppression du fichier Acknow PR Initial HYUNDAI** — `Microsoft.FileSystemTask`
- **Table_Facture_HYU_MIAMI** — `Microsoft.Pipeline` *(desactive)*
- **Table_Facture_HYU_MIAMI 1** — `Microsoft.Pipeline`
- **Test présence du fichier HYUNDAI MIAMI** — `Microsoft.ScriptTask`
- **Tâche d'exécution de requêtes SQL** — `Microsoft.ExecuteSQLTask`

## Points a verifier / non convertis

- [Source ADO NET] connexion BD 'ICAR SGDM' (ORACLE) : Oracle : verifier hote/service ou alias TNS et le mot de passe.
- [Table_Num_Cmde_PR_ICAR] connexion BD '10.20.210.165.INFOCENTRE SGDM' (MSSQLNATIVE) : SQL Server : authentification integree (SSPI) -> renseigner un compte ou activer l'auth. integree dans Spoon.
- [Table_Facture_HYU_MIAMI] connexion BD '10.20.210.165.INFOCENTRE SGDM' (MSSQLNATIVE) : SQL Server : authentification integree (SSPI) -> renseigner un compte ou activer l'auth. integree dans Spoon.
- [Colonne dérivée.DEVISE] expression SSIS d'origine : "USD"
- [Colonne dérivée.Colonne dérivée 1] expression SSIS d'origine : SUBSTRING([Unit Price],1,5) + "." + RIGHT([Unit Price],2)
- [Recherche] Lookup non converti (etape Dummy). Requete de reference : SELECT NUM_COMMANDE_ICAR, ANNEE, right(NUM_CONSTRUCTEUR,5) NUM_CONSTRUCTEUR, NUM_CONSTRUCTEUR NUM_CONSTRUCTEUR2 FROM Table_Num_Cmde_PR_ICAR
- [Unir tout] Union All SSIS -> Dummy (les flux entrants sont fusionnes ; verifier la correspondance des champs)
- [Test présence du fichier HYUNDAI MIAMI] Script Task (VisualBasic) non porte (logique .NET a reimplementer si necessaire) -> Dummy
- [Tâche d'exécution de requêtes SQL] entree SQL sur la connexion '10.20.210.165.INFOCENTRE SGDM' : renseigner les identifiants dans Spoon
- contrainte Test présence du fichier HYUNDAI MIAMI -> Tâche d'exécution de requêtes SQL : expression SSIS '@[User::Test_Fichier_HYU_MIA]==TRUE' non traduite (hop inconditionnel), a valider

> Genere automatiquement par ssis2pdi. Ouvrir chaque fichier dans Spoon et faire un Apercu avant mise en production.
