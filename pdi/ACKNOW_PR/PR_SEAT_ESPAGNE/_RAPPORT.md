# Rapport de conversion : PR_GVF_SEAT

Source : `PR_SEAT_ESPAGNE.dtsx`

## Fichiers PDI generes

- `PR_SEAT_ESPAGNE_RAJOUT_DATE_CMDE.ktr`
- `PR_SEAT_ESPAGNE_RECUPERATION_ARTICLES.ktr`
- `PR_SEAT_ESPAGNE_RECUPERATION_DATE.ktr`
- `PR_SEAT_ESPAGNE.kjb`

## Composants du package

- **Copie du fichier à intégrer dans le répertoire attendu par I'COM SEAT** — `Microsoft.FileSystemTask`
- **ENVOI FICHIER POUR CONTROLE** — `Microsoft.SendMailTask` *(desactive)*
- **RAJOUT DATE CMDE** — `Microsoft.Pipeline`
- **RECUPERATION ARTICLES** — `Microsoft.Pipeline`
- **RECUPERATION DATE** — `Microsoft.Pipeline`
- **Suppression du fichier Acknow PR Initial SEAT** — `Microsoft.FileSystemTask`
- **Test présence du fichier SEAT** — `Microsoft.ScriptTask`
- **Tâche d'exécution de requêtes SQL** — `Microsoft.ExecuteSQLTask`

## Points a verifier / non convertis

- [Source OLE DB] connexion BD '10.20.210.161.INFOCENTRE SGDM' (MSSQLNATIVE) : SQL Server : authentification integree (SSPI) -> renseigner un compte ou activer l'auth. integree dans Spoon.
- [ACKNOW_PR_ESPAGNE_TEMP] connexion BD '10.20.210.161.INFOCENTRE SGDM' (MSSQLNATIVE) : SQL Server : authentification integree (SSPI) -> renseigner un compte ou activer l'auth. integree dans Spoon.
- [Colonne dérivée 1.TYPE_COMMANDE] expression SSIS d'origine : "A"
- [Colonne dérivée 1.DEVISE] expression SSIS d'origine : "EUR"
- [Colonne dérivée 1.NUM_FACTURE] expression SSIS d'origine : PREFIXE_NUM_FACTURE + SUFFIXE_NUM_FACTURE
- [LIGNE <> I3] ConditionalSplit non route automatiquement (etape Dummy). Conditions a implementer :
- [LIGNE <> I3]   - Ligne a prendre : [RECORD ID] != "3I"
- [AKCNOW_PR_DATE] connexion BD '10.20.210.161.INFOCENTRE SGDM' (MSSQLNATIVE) : SQL Server : authentification integree (SSPI) -> renseigner un compte ou activer l'auth. integree dans Spoon.
- [Fractionnement conditionnel] ConditionalSplit non route automatiquement (etape Dummy). Conditions a implementer :
- [Fractionnement conditionnel]   - Ligne à prendre : [RECORD ID] == "2I"
- [ENVOI FICHIER POUR CONTROLE] tache d'envoi de mail convertie (verifier le serveur SMTP)
- [Test présence du fichier SEAT] Script Task (VisualBasic) non porte (logique .NET a reimplementer si necessaire) -> Dummy
- [Tâche d'exécution de requêtes SQL] entree SQL sur la connexion '10.20.210.161.INFOCENTRE SGDM' : renseigner les identifiants dans Spoon
- contrainte Test présence du fichier SEAT -> Tâche d'exécution de requêtes SQL : expression SSIS '@[User::Test_Fichier_SEAT]==TRUE' non traduite (hop inconditionnel), a valider

> Genere automatiquement par ssis2pdi. Ouvrir chaque fichier dans Spoon et faire un Apercu avant mise en production.
