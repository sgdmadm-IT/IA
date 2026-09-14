# Rapport de conversion : PR_SKODA_REP_TCH

Source : `PR_SKODA_REP_TCH.dtsx`

## Fichiers PDI generes

- `PR_SKODA_REP_TCH_RECUPERATION_ARTICLES.ktr`
- `PR_SKODA_REP_TCH_RECUPERATION_ARTICLES_1.ktr`
- `PR_SKODA_REP_TCH_RECUPERATION_COMMANDE_ICAR.ktr`
- `PR_SKODA_REP_TCH.kjb`

## Composants du package

- **Copie du fichier à intégrer dans le répertoire attendu par I'COM SKODA** — `Microsoft.FileSystemTask`
- **RECUPERATION ARTICLES** — `Microsoft.Pipeline` *(desactive)*
- **RECUPERATION ARTICLES 1** — `Microsoft.Pipeline`
- **RECUPERATION COMMANDE ICAR** — `Microsoft.Pipeline` *(desactive)*
- **Suppression du fichier Acknow PR Initial SKODA** — `Microsoft.FileSystemTask`
- **Test présence du fichier SKODA REP TCH** — `Microsoft.ScriptTask`
- **Tâche d'exécution de requêtes SQL** — `Microsoft.ExecuteSQLTask`

## Points a verifier / non convertis

- [Colonne dérivée.TYPE_COMMANDE] expression SSIS d'origine : "A"
- [Colonne dérivée.CMDE USINE ICAR] expression SSIS d'origine : LEFT(TRIM(BUYER),3) + RIGHT(TRIM([CMDE ICAR]),7)
- [Colonne dérivée.NUMERO BL] expression SSIS d'origine : LEFT(TRIM(BUYER),3) + RIGHT(TRIM([CMDE ICAR]),7)
- [Multidiffusion] Multicast SSIS -> Dummy (relier chaque sortie ; option 'copier les donnees' sur les hops sortants)
- [Colonne dérivée.TYPE_COMMANDE] expression SSIS d'origine : "A"
- [Colonne dérivée.CMDE USINE ICAR] expression SSIS d'origine : LEFT(TRIM(BUYER),3) + RIGHT(TRIM([CMDE ICAR]),7)
- [Colonne dérivée.NUMERO BL] expression SSIS d'origine : LEFT(TRIM(BUYER),3) + RIGHT(TRIM([CMDE ICAR]),7)
- [Multidiffusion] Multicast SSIS -> Dummy (relier chaque sortie ; option 'copier les donnees' sur les hops sortants)
- [Recherche] Lookup non converti (etape Dummy). Requete de reference : select * from [dbo].[Table_Num_Cmde_PR_ICAR]
- [Unir tout] Union All SSIS -> Dummy (les flux entrants sont fusionnes ; verifier la correspondance des champs)
- [Source ADO NET] connexion BD 'ICAR SGDM' (ORACLE) : Oracle : verifier hote/service ou alias TNS et le mot de passe.
- [Table_Num_Cmde_PR_ICAR] connexion BD '10.20.210.165.INFOCENTRE SGDM' (MSSQLNATIVE) : SQL Server : authentification integree (SSPI) -> renseigner un compte ou activer l'auth. integree dans Spoon.
- [Test présence du fichier SKODA REP TCH] Script Task (VisualBasic) non porte (logique .NET a reimplementer si necessaire) -> Dummy
- [Tâche d'exécution de requêtes SQL] entree SQL sur la connexion '10.20.210.165.INFOCENTRE SGDM' : renseigner les identifiants dans Spoon
- contrainte Test présence du fichier SKODA REP TCH -> Tâche d'exécution de requêtes SQL : expression SSIS '@[User::Test_Fichier_Rep_TCH]==TRUE' non traduite (hop inconditionnel), a valider

> Genere automatiquement par ssis2pdi. Ouvrir chaque fichier dans Spoon et faire un Apercu avant mise en production.
