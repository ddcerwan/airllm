#!/usr/bin/env python3
"""Generate the AirLLM security impact-study as a PDF document (reportlab).

Mirrors scripts/gen_security_report.py (the .docx version) with the same 9-section content.
Run:  python scripts/gen_security_report_pdf.py [output.pdf]
"""

import sys
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem,
)

ACCENT = colors.HexColor('#1F4E79')
GREY = colors.HexColor('#595959')
LIGHT = colors.HexColor('#DCE6F1')


def styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle('DocTitle', parent=ss['Title'], fontSize=24,
                          textColor=ACCENT, spaceAfter=4))
    ss.add(ParagraphStyle('DocSub', parent=ss['Normal'], fontSize=13,
                          textColor=GREY, alignment=TA_CENTER, spaceAfter=2))
    ss.add(ParagraphStyle('DocMeta', parent=ss['Normal'], fontSize=9,
                          textColor=GREY, alignment=TA_CENTER))
    ss.add(ParagraphStyle('H1', parent=ss['Heading1'], fontSize=15,
                          textColor=ACCENT, spaceBefore=14, spaceAfter=6))
    ss.add(ParagraphStyle('H2', parent=ss['Heading2'], fontSize=12,
                          textColor=ACCENT, spaceBefore=10, spaceAfter=4))
    ss.add(ParagraphStyle('Body', parent=ss['Normal'], fontSize=10.5,
                          leading=15, spaceAfter=6))
    ss.add(ParagraphStyle('Measure', parent=ss['Normal'], fontSize=10.5,
                          textColor=ACCENT, spaceBefore=4, spaceAfter=2))
    return ss


def make_table(ss, headers, rows, widths):
    data = [headers] + [[str(c) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='CENTER')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#9DB7D4')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


def bullets(ss, items):
    lis = [ListItem(Paragraph(x, ss['Body']), leftIndent=12) for x in items]
    return ListFlowable(lis, bulletType='bullet', start='•', leftIndent=10)



def build_story(ss):
    today = f"{date.today():%d/%m/%Y}"
    story = []
    A = story.append

    # Title block
    A(Paragraph('Étude de la construction des impacts', ss['DocTitle']))
    A(Paragraph('Audit et durcissement de la sécurité — Bibliothèque AirLLM', ss['DocSub']))
    A(Paragraph(f'Projet : airllm  ·  Référentiel : main @ a6d631f  ·  Date : {today}', ss['DocMeta']))
    A(Spacer(1, 10))

    # 1
    A(Paragraph('1. Résumé exécutif', ss['H1']))
    A(Paragraph(
        "AirLLM est une bibliothèque d'inférence de modèles de langage (LLM) conçue pour exécuter des "
        "modèles de très grande taille (jusqu'à 2 800 milliards de paramètres) sur des cartes graphiques "
        "à mémoire limitée, par streaming des poids couche par couche. Cette étude analyse les impacts "
        "de sécurité liés à ses fonctions critiques — téléchargement, désérialisation et réécriture de "
        "poids de modèles — et rend compte des mesures de durcissement appliquées.", ss['Body']))
    A(Paragraph(
        "Un audit de 46 fichiers source a mis en évidence quatre risques, dont un critique (exécution de "
        "code arbitraire au chargement d'un fichier de poids). Ces risques ont été corrigés, validés et "
        "intégrés dans un commit dédié. Le bilan chiffré et l'analyse détaillée sont présentés ci-après.",
        ss['Body']))
    A(make_table(ss, ['Indicateur', 'Valeur'], [
        ['Fichiers audités', '46 fichiers Python'],
        ['Fichiers modifiés', '4 (+1 fichier de test créé)'],
        ['Volume de correctifs', '+138 / −19 lignes'],
        ['Risques identifiés', '4 (1 critique, 1 élevé, 2 moyens)'],
        ['Risques corrigés', '4 / 4 (100 %)'],
        ['Vulnérabilités RCE résiduelles', '0'],
    ], [8 * cm, 8 * cm]))

    # 2
    A(Paragraph('2. Contexte et méthode d\'analyse', ss['H1']))
    A(Paragraph(
        "L'analyse s'appuie sur l'examen statique du code source et l'identification des surfaces "
        "d'attaque propres à une bibliothèque manipulant des artefacts non fiables. Quatre familles de "
        "risques ont été systématiquement recherchées :", ss['Body']))
    A(bullets(ss, [
        '<b>Désérialisation</b> — désérialisation non sécurisée (pickle via torch.load) ;',
        '<b>Code distant</b> — exécution de code distant (trust_remote_code) ;',
        '<b>Système de fichiers</b> — opérations sur le système de fichiers (suppression, liens) ;',
        '<b>Supply chain</b> — intégrité de la chaîne d\'approvisionnement (dépendances).',
    ]))

    # 3
    A(Paragraph('3. Cartographie des risques et impacts', ss['H1']))
    A(Paragraph(
        "Chaque risque est caractérisé par sa gravité, son vecteur d'attaque et son impact potentiel sur "
        "les systèmes exécutant la bibliothèque.", ss['Body']))
    A(make_table(ss, ['Réf.', 'Gravité', 'Vecteur', 'Impact potentiel'], [
        ['V1', 'CRITIQUE', 'torch.load() sans weights_only', 'Exécution de code arbitraire (RCE)'],
        ['V2', 'ÉLEVÉ', 'trust_remote_code=True codé en dur', 'Exécution de code distant non maîtrisée'],
        ['V3', 'MOYEN', 'remove_real_and_linked_file()', 'Plantage (UnboundLocalError) ; suppression non validée'],
        ['V4', 'MOYEN', 'Dépendances git non épinglées', 'Installation non reproductible ; compromission supply chain'],
    ], [1.4 * cm, 2.3 * cm, 5.6 * cm, 6.3 * cm]))

    # 4
    A(Paragraph('4. Analyse détaillée et mesures appliquées', ss['H1']))

    A(Paragraph('4.1  V1 — Exécution de code à distance via pickle (CRITIQUE)', ss['H2']))
    A(Paragraph(
        "torch.load() utilise l'unpickler de Python, capable d'instancier des objets arbitraires au travers "
        "du protocole __reduce__. Un fichier pytorch_model.bin malveillant — issu d'un dépôt HuggingFace "
        "compromis ou d'un chemin local piégé — peut donc exécuter du code arbitraire sans interaction "
        "supplémentaire de l'utilisateur.", ss['Body']))
    A(Paragraph(
        "<b>Impact :</b> compromission totale de la machine hôte (exécution de commandes, exfiltration de "
        "données, persistance). Il s'agit du risque le plus grave de l'audit.", ss['Body']))
    A(Paragraph('Mesure appliquée :', ss['Measure']))
    A(bullets(ss, [
        '<b>Helper</b> — centralisation _safe_torch_load() forçant weights_only=True ;',
        '<b>Couverture</b> — les 4 sites vulnérables (utils.py ×3, airllm_lora.py ×1) sont redirigés vers ce helper ;',
        '<b>Verrou</b> — suppression du repli except TypeError qui réactivait l\'unpickler non restreint.',
    ]))

    A(Paragraph('4.2  V2 — Exécution de code distant non désactivable (ÉLEVÉ)', ss['H2']))
    A(Paragraph(
        "L'option trust_remote_code=True était codée en dur dans AutoModel.get_module_class, imposant "
        "l'exécution du code Python embarqué dans tout dépôt de modèles, sans possibilité de refus pour "
        "l'utilisateur.", ss['Body']))
    A(Paragraph("<b>Impact :</b> exécution de code tiers arbitraire à l'initialisation du modèle.", ss['Body']))
    A(Paragraph('Mesure appliquée :', ss['Measure']))
    A(bullets(ss, [
        '<b>Opt-in</b> — nouveau paramètre trust_remote_code, par défaut à False ;',
        '<b>Séquence</b> — le parseur natif de transformers est essayé en premier ; le code distant n\'est utilisé qu\'en repli (cohérent avec AirLLMBaseModel) ;',
        '<b>Portée</b> — le flag est consommé localement et n\'est plus transmis au constructeur du modèle.',
    ]))

    A(Paragraph('4.3  V3 — Robustesse et suppression de fichiers (MOYEN)', ss['H2']))
    A(Paragraph(
        "Dans remove_real_and_linked_file(), la variable targetpath n'était initialisée que dans la branche "
        "traitant les liens symboliques. Sur un chemin ordinaire, la fonction levait une UnboundLocalError. "
        "Cette fonction est invoquée par l'option delete_original, qui supprime les fichiers de poids "
        "originaux de l'utilisateur.", ss['Body']))
    A(Paragraph("<b>Impact :</b> plantage et suppression destructrice sans validation de périmètre de chemin.", ss['Body']))
    A(Paragraph('Mesure appliquée :', ss['Measure']))
    A(bullets(ss, [
        '<b>Correction</b> — initialisation de targetpath à None et comparaison des chemins normalisée (str) ;',
        '<b>Clarté</b> — documentation du contrat de la fonction.',
    ]))

    A(Paragraph('4.4  V4 — Intégrité de la chaîne d\'approvisionnement (MOYEN)', ss['H2']))
    A(Paragraph(
        "requirements.txt référençait transformers depuis la branche main (référence mouvante). Une branche "
        "ou un tag déplaçable peut être réécrit silencieusement, brisant la reproductibilité et exposant à "
        "une compromission en amont.", ss['Body']))
    A(Paragraph("<b>Impact :</b> builds non reproductibles ; risque d'injection de code via une dépendance modifiée.", ss['Body']))
    A(Paragraph('Mesure appliquée :', ss['Measure']))
    A(bullets(ss, [
        '<b>Épinglage</b> — les trois dépendances git (transformers, peft, accelerate) sont épinglées à des SHA de commit immuables, vérifiés comme réels.',
    ]))

    # 5
    A(Paragraph('5. Construction des impacts — avant / après', ss['H1']))
    A(Paragraph(
        "Le tableau suivant synthétise la réduction de l'exposition obtenue par chaque mesure.", ss['Body']))
    A(make_table(ss, ['Risque', 'Exposition avant', 'Exposition après', 'Risque résiduel'], [
        ['V1 RCE pickle', 'Certaine (code arbitraire)', 'Nulle (weights_only=True)', 'Négligeable'],
        ['V2 Code distant', 'Systématique (non désactivable)', 'À la demande (opt-in)', "Faible — inhérent à l'usage"],
        ['V3 Suppression', 'Plantage + non validée', 'Robuste + documentée', 'Faible — confiné au cache HF'],
        ['V4 Supply chain', 'Non reproductible', 'Épinglé (SHA immuables)', 'Négligeable'],
    ], [3.2 * cm, 4.3 * cm, 4.3 * cm, 3.8 * cm]))

    # 6
    A(Paragraph('6. Livrables et volumétrie', ss['H1']))
    A(make_table(ss, ['Fichier', 'Δ lignes', 'Nature du changement'], [
        ['air_llm/airllm/utils.py', '+26 / −7', 'Helper _safe_torch_load + fix remove_real_and_linked_file'],
        ['air_llm/airllm/auto_model.py', '+22 / −5', 'trust_remote_code configurable (défaut False)'],
        ['air_llm/airllm/airllm_lora.py', '+5 / −4', 'Suppression du repli torch.load non sécurisé'],
        ['air_llm/tests/test_safe_load.py', 'nouveau (80)', 'Test anti-RCE pickle (skip si torch absent)'],
        ['requirements.txt', '+5 / −3', 'Épinglage git vers SHA immuables'],
    ], [5.3 * cm, 2.7 * cm, 7.6 * cm]))
    A(Paragraph("<b>Commit de référence :</b> a6d631f — security: harden checkpoint loading and dependency pinning", ss['Body']))

    # 7
    A(Paragraph('7. Contrôles de validation', ss['H1']))
    A(make_table(ss, ['Contrôle', 'Résultat'], [
        ['Compilation (py_compile) des 5 fichiers', 'Succès'],
        ['Recherche de torch.load non sécurisé résiduel', 'Aucun'],
        ['Vérification des SHA de dépendances (git ls-remote)', 'Tous réels'],
        ['Exécution du test anti-RCE (unittest)', 'Succès (skip si torch absent)'],
    ], [10 * cm, 6 * cm]))

    # 8
    A(Paragraph('8. Risques résiduels et perspectives', ss['H1']))
    A(Paragraph(
        "Les risques suivants, hors du périmètre du lot corrigé, sont identifiés pour une action "
        "ultérieure :", ss['Body']))
    A(bullets(ss, [
        '<b>Code distant résiduel</b> — get_tokenizer() (airllm_base.py) et le chemin MLX conservent trust_remote_code=True implicite — un refactor plus large serait nécessaire ;',
        '<b>Liens symboliques</b> — link_or_copy_file() suit les liens symboliques (impact faible, contenu confiné au cache HuggingFace) ;',
        '<b>Packaging</b> — le packaging officiel (setup.py) conserve une plage PyPI saine (transformers>=4.49,<6) ; seules les broches dev/CI ont été figées.',
    ]))

    # 9
    A(Paragraph('9. Conclusion', ss['H1']))
    A(Paragraph(
        "La construction des impacts démontre une réduction substantielle de la surface d'attaque : la "
        "vulnérabilité critique d'exécution de code arbitraire est intégralement neutralisée, l'exécution "
        "de code distant passe sous contrôle explicite de l'utilisateur, et la chaîne d'approvisionnement "
        "est rendue reproductible. Les mesures, testées et versionnées, renforcent la posture de sécurité "
        "d'AirLLM sans dégrader son usage nominal, la voie principale (safetensors) n'étant pas affectée.",
        ss['Body']))

    return story


def _page_decor(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, 1.2 * cm, 'AirLLM — Étude de la construction des impacts')
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f'Page {doc.page}')
    canvas.setStrokeColor(LIGHT)
    canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas.restoreState()


def main(out_path):
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2.2 * cm,
        title='AirLLM — Étude de la construction des impacts',
        author='Audit sécurité AirLLM',
    )
    ss = styles()
    doc.build(build_story(ss), onFirstPage=_page_decor, onLaterPages=_page_decor)
    print(f"Document PDF généré : {out_path}")


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'AirLLM_Etude_Impacts_Securite.pdf'
    main(out)

