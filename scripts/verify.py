#!/usr/bin/env python3
"""Contrôles de cohérence du jeu de données produit par build.py."""
import json, re, sys, unicodedata
from pathlib import Path

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
livres = json.loads((OUT / "livres.json").read_text())
lex = {e["strong_etendu"]: e for e in json.loads((OUT / "lexique.json").read_text())}
V = {}
for f in sorted((OUT / "versets").glob("*.json")):
    for r in json.loads(f.read_text()):
        V[r["ref"]] = r

def norm(s):
    s = unicodedata.normalize("NFD", s)
    return re.sub(r"[^\w]|ʼ", "", "".join(c for c in s if unicodedata.category(c) != "Mn")).lower()

problems = []
# 1. texte MACULA == texte SBLGNT officiel (mot à mot, sans accents), par livre
SBL = {"MAT":"Matt","MRK":"Mark","LUK":"Luke","JHN":"John","ACT":"Acts","ROM":"Rom","1CO":"1Cor",
       "2CO":"2Cor","GAL":"Gal","EPH":"Eph","PHP":"Phil","COL":"Col","1TH":"1Thess","2TH":"2Thess",
       "1TI":"1Tim","2TI":"2Tim","TIT":"Titus","PHM":"Phlm","HEB":"Heb","JAS":"Jas","1PE":"1Pet",
       "2PE":"2Pet","1JN":"1John","2JN":"2John","3JN":"3John","JUD":"Jude","REV":"Rev"}
for b in livres:
    xml = (SRC / f"SBLGNT/data/sblgnt/xml/{SBL[b['code']]}.xml").read_text(encoding="utf-8-sig")
    sbl_words = [norm(w) for w in re.findall(r"<w>(.*?)</w>", xml)]
    mac_words = [norm(w["grec"]) for r in V.values() if r["livre"] == b["code"] for w in r["mots"]]
    diff = sum(1 for a, c in zip(sbl_words, mac_words) if a != c) + abs(len(sbl_words) - len(mac_words))
    if diff:
        problems.append(f"{b['code']}: {diff} écarts SBLGNT/MACULA ({len(sbl_words)} vs {len(mac_words)} mots)")

# 2. chaque mot a un Strong étendu présent dans le lexique
nolex = sum(1 for r in V.values() for w in r["mots"] if w["strong_etendu"] not in lex)
if nolex:
    problems.append(f"{nolex} mots sans entrée de lexique")

# 3. numérotation continue des versets dans chaque chapitre
for b in livres:
    for ch in range(1, b["nb_chapitres"] + 1):
        vs = sorted(r["verset"] for r in V.values() if r["livre"] == b["code"] and r["chapitre"] == ch)
        gaps = sorted(set(range(1, vs[-1] + 1)) - set(vs)) if vs else []
        if gaps:
            problems.append(f"{b['code']} {ch}: versets absents {gaps}")

print("Contrôles :", "OK" if not problems else "")
for p in problems:
    print(" -", p)

def show(ref):
    r = V[ref]
    print(f"\n== {ref} ({r['livre_fr']}) paragraphe={r['debut_paragraphe']}\n{r['texte_grec']}")
    for w in r["mots"]:
        e = lex[w["strong_etendu"]]
        print(f"  {w['grec']:<14} {w['strong_etendu']:<7} {w['morpho']:<14} {w['glose_en']:<16} "
              f"LN={w['louw_nida'] or '-':<8} réf={w['referent'] or ''} | lex: {e['glose']}")
    print("  apparat:", r["apparat_sblgnt"])
    print("  variantes TAGNT:", [(v['grec'], v['editions']) for v in r["variantes_tagnt"]])

for ref in sys.argv[3:]:
    show(ref)
print("\nVersets hors SBLGNT :", [a["ref"] for a in json.loads((OUT / "versets_hors_sblgnt.json").read_text())])
