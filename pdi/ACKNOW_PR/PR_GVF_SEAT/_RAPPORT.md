# Rapport de conversion : PR_GVF_SEAT

Source : `PR_GVF_SEAT.dtsx`

## Fichiers PDI generes

- `PR_GVF_SEAT_AUDI.ktr`
- `PR_GVF_SEAT_SEAT.ktr`
- `PR_GVF_SEAT_SKODA.ktr`
- `PR_GVF_SEAT.kjb`

## Composants du package

- **AUDI** — `Microsoft.Pipeline` *(desactive)*
- **Copie du fichier à intégrer dans le répertoire attendu par I'COM AUDI** — `Microsoft.FileSystemTask` *(desactive)*
- **Copie du fichier à intégrer dans le répertoire attendu par I'COM SEAT** — `Microsoft.FileSystemTask`
- **Copie du fichier à intégrer dans le répertoire attendu par I'COM SKODA** — `Microsoft.FileSystemTask` *(desactive)*
- **SEAT** — `Microsoft.Pipeline`
- **SKODA** — `Microsoft.Pipeline` *(desactive)*
- **Suppression du fichier Acknow PR Initial AUDI** — `Microsoft.FileSystemTask` *(desactive)*
- **Suppression du fichier Acknow PR Initial SEAT** — `Microsoft.FileSystemTask`
- **Suppression du fichier Acknow PR Initial SKODA** — `Microsoft.FileSystemTask` *(desactive)*
- **Test présence du fichier AUDI** — `Microsoft.ScriptTask` *(desactive)*
- **Test présence du fichier SEAT** — `Microsoft.ScriptTask`
- **Test présence du fichier SKODA** — `Microsoft.ScriptTask` *(desactive)*

## Points a verifier / non convertis

- [Colonne dérivée.REFERENCE LIVREE] expression SSIS d'origine : REPLACE(Article," ","")
- [Colonne dérivée.COMMANDE_FOURNISSEUR] expression SSIS d'origine : [Copie de Doc# vente]
- [Colonne dérivée.PX_ACHAT_UNITAIRE] cast(s) SSIS supprime(s) : la precision/le format peut differer, a verifier
- [Colonne dérivée.PX_ACHAT_UNITAIRE] expression SSIS d'origine : REPLACE((DT_WSTR,9)((DT_NUMERIC,7,2)((DT_DECIMAL,2)[Valeur unitaire])),",",".")
- [Colonne dérivée.REFERENCE COMMANDEE] expression SSIS d'origine : REPLACE(Article," ","")
- [SUPP TIRET ARTICLES.TYPE_COMMANDE] expression SSIS d'origine : "A"
- [SUPP TIRET ARTICLES.DEVISE] expression SSIS d'origine : "EUR"
- [SUPP TIRET ARTICLES.DATE_BL] expression SSIS d'origine : SUBSTRING([Copie de Créé le],7,2) + SUBSTRING([Copie de Créé le],5,2) + SUBSTRING([Copie de Créé le],1,4)
- [Colonne dérivée.REFERENCE LIVREE] expression SSIS d'origine : REPLACE(Article," ","")
- [Colonne dérivée.COMMANDE_FOURNISSEUR] expression SSIS d'origine : [Copie de Doc# vente]
- [Colonne dérivée.PX_ACHAT_UNITAIRE] cast(s) SSIS supprime(s) : la precision/le format peut differer, a verifier
- [Colonne dérivée.PX_ACHAT_UNITAIRE] expression SSIS d'origine : REPLACE((DT_WSTR,9)((DT_NUMERIC,7,2)((DT_DECIMAL,2)[Valeur unitaire])),",",".")
- [Colonne dérivée.REFERENCE COMMANDEE] expression SSIS d'origine : REPLACE(Article," ","")
- [SUPP TIRET ARTICLES.TYPE_COMMANDE] expression SSIS d'origine : "A"
- [SUPP TIRET ARTICLES.DEVISE] expression SSIS d'origine : "EUR"
- [SUPP TIRET ARTICLES.DATE_BL] expression SSIS d'origine : SUBSTRING([Copie de Créé le],7,2) + SUBSTRING([Copie de Créé le],5,2) + SUBSTRING([Copie de Créé le],1,4)
- [Colonne dérivée.REFERENCE LIVREE] expression SSIS d'origine : REPLACE(Article," ","")
- [Colonne dérivée.COMMANDE_FOURNISSEUR] expression SSIS d'origine : [Copie de Doc# vente]
- [Colonne dérivée.PX_ACHAT_UNITAIRE] cast(s) SSIS supprime(s) : la precision/le format peut differer, a verifier
- [Colonne dérivée.PX_ACHAT_UNITAIRE] expression SSIS d'origine : REPLACE((DT_WSTR,9)((DT_NUMERIC,7,2)((DT_DECIMAL,2)[Valeur unitaire])),",",".")
- [Colonne dérivée.REFERENCE COMMANDEE] expression SSIS d'origine : REPLACE(Article," ","")
- [SUPP TIRET ARTICLES.TYPE_COMMANDE] expression SSIS d'origine : "A"
- [SUPP TIRET ARTICLES.DEVISE] expression SSIS d'origine : "EUR"
- [SUPP TIRET ARTICLES.DATE_BL] expression SSIS d'origine : SUBSTRING([Copie de Créé le],7,2) + SUBSTRING([Copie de Créé le],5,2) + SUBSTRING([Copie de Créé le],1,4)
- [Test présence du fichier AUDI] Script Task (VisualBasic) non porte (logique .NET a reimplementer si necessaire) -> Dummy
- [Test présence du fichier SEAT] Script Task (VisualBasic) non porte (logique .NET a reimplementer si necessaire) -> Dummy
- [Test présence du fichier SKODA] Script Task (VisualBasic) non porte (logique .NET a reimplementer si necessaire) -> Dummy
- contrainte Test présence du fichier AUDI -> AUDI : expression SSIS '@[User::Test_Fichier_AUDI]==TRUE' non traduite (hop inconditionnel), a valider
- contrainte Test présence du fichier SEAT -> SEAT : expression SSIS '@[User::Test_Fichier_SEAT]==TRUE' non traduite (hop inconditionnel), a valider
- contrainte Test présence du fichier SKODA -> SKODA : expression SSIS '@[User::Test_Fichier_SKODA]==TRUE' non traduite (hop inconditionnel), a valider

> Genere automatiquement par ssis2pdi. Ouvrir chaque fichier dans Spoon et faire un Apercu avant mise en production.
