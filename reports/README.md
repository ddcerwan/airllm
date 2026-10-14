# Rapports — Audit de sécurité AirLLM

Ce dossier conserve les livrables de l'audit de sécurité et du durcissement de la
bibliothèque AirLLM. Ils sont versionnés dans Git pour archivage et consultation ultérieure.

## Livrables

| Document | Formats | Contenu |
|---|---|---|
| **Compte rendu détaillé** (`AirLLM_Compte_Rendu_Securite_Detaille`) | `.docx` · `.pdf` · `.md` | Rapport complet : sommaire, 13 sections (contexte, cartographie V1–V4, analyse détaillée, matrice avant/après, volumétrie, tests, risques résiduels, conclusion) et 4 annexes (commits, fichiers audités, extraits de code, glossaire). |
| **Étude des impacts** (`AirLLM_Etude_Impacts_Securite`) | `.docx` · `.pdf` | Synthèse condensée (9 sections) de la construction des impacts. |

Recommandation : privilégier le **compte rendu détaillé** (`.pdf` pour lecture/impression,
`.md` pour un wiki ou une description de PR, `.docx` pour édition).

## Régénération

Les documents sont produits depuis une source de contenu unique, afin que les formats
restent synchronisés. Depuis la racine du dépôt :

```bash
cd scripts
pip install python-docx reportlab pypdf   # dépendances de rendu

# Compte rendu détaillé (Word + PDF + Markdown)
python gen_detailed_report.py AirLLM_Compte_Rendu_Securite_Detaille
# → déplacer les sorties dans ../reports/

# Étude des impacts (Word seul)
python gen_security_report.py
# → déplacer AirLLM_Etude_Impacts_Securite.docx dans ../reports/
```

Le contenu éditorial du compte rendu détaillé est centralisé dans
[`scripts/report_content.py`](../scripts/report_content.py) sous forme de blocs typés ;
le rendu est assuré par [`scripts/gen_detailed_report.py`](../scripts/gen_detailed_report.py).

## Voir aussi

- Commits de sécurité : `a6d631f` (durcissement initial) et `ac9e260` (généralisation
  tri-état de `trust_remote_code`).
- Tests associés : `air_llm/tests/test_safe_load.py` et `air_llm/tests/test_trust_remote_code.py`.
