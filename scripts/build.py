#!/usr/bin/env python3
"""Phase 0 — « Ta version » : fusion SBLGNT + MACULA Greek + STEPBible (TAGNT, TBESG).

Sortie : un enregistrement par verset, avec les mots grecs annotés
(Strong classique et étendu, lemme, morphologie, glose, Louw-Nida, référent),
les débuts de paragraphe SBLGNT, l'apparat critique SBLGNT et les variantes TAGNT.
"""
import csv, json, re, sys, html
from collections import defaultdict, OrderedDict
from pathlib import Path

SRC = Path(sys.argv[1])          # dossier des sources clonées
OUT = Path(sys.argv[2])          # dossier de sortie
OUT.mkdir(parents=True, exist_ok=True)
csv.field_size_limit(10**9)

# ordre, code USFM (MACULA), code TAGNT, fichier SBLGNT, nom français
BOOKS = [
    (1, "MAT", "Mat", "Matt", "Matthieu"), (2, "MRK", "Mrk", "Mark", "Marc"),
    (3, "LUK", "Luk", "Luke", "Luc"), (4, "JHN", "Jhn", "John", "Jean"),
    (5, "ACT", "Act", "Acts", "Actes"), (6, "ROM", "Rom", "Rom", "Romains"),
    (7, "1CO", "1Co", "1Cor", "1 Corinthiens"), (8, "2CO", "2Co", "2Cor", "2 Corinthiens"),
    (9, "GAL", "Gal", "Gal", "Galates"), (10, "EPH", "Eph", "Eph", "Éphésiens"),
    (11, "PHP", "Php", "Phil", "Philippiens"), (12, "COL", "Col", "Col", "Colossiens"),
    (13, "1TH", "1Th", "1Thess", "1 Thessaloniciens"), (14, "2TH", "2Th", "2Thess", "2 Thessaloniciens"),
    (15, "1TI", "1Ti", "1Tim", "1 Timothée"), (16, "2TI", "2Ti", "2Tim", "2 Timothée"),
    (17, "TIT", "Tit", "Titus", "Tite"), (18, "PHM", "Phm", "Phlm", "Philémon"),
    (19, "HEB", "Heb", "Heb", "Hébreux"), (20, "JAS", "Jas", "Jas", "Jacques"),
    (21, "1PE", "1Pe", "1Pet", "1 Pierre"), (22, "2PE", "2Pe", "2Pet", "2 Pierre"),
    (23, "1JN", "1Jn", "1John", "1 Jean"), (24, "2JN", "2Jn", "2John", "2 Jean"),
    (25, "3JN", "3Jn", "3John", "3 Jean"), (26, "JUD", "Jud", "Jude", "Jude"),
    (27, "REV", "Rev", "Rev", "Apocalypse"),
]
TAG2USFM = {b[2]: b[1] for b in BOOKS}
SBL2USFM = {b[3]: b[1] for b in BOOKS}

def classic(strong):
    """'G2424G' / 'G4413_a' / '2424' -> 2424 (int) ou None."""
    m = re.search(r"G?0*(\d+)", strong or "")
    return int(m.group(1)) if m else None

# ---------- 1. MACULA (base : texte SBLGNT mot à mot) ----------
mac_path = SRC / "macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv"
verses = OrderedDict()            # (book, ch, v) -> list of words
by_id = {}
with open(mac_path, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        m = re.match(r"(\w+) (\d+):(\d+)!(\d+)", r["ref"])
        book, ch, v, pos = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        w = {
            "id": r["xml:id"], "pos": pos,
            "grec": r["text"], "apres": r["after"],
            "lemme": r["lemma"], "strong": int(r["strong"]) if r["strong"].isdigit() else None,
            "strong_etendu": None, "morpho": r["morph"], "classe": r["class"],
            "glose_en": r["english"], "glose_ctx": r["gloss"],
            "louw_nida": r["ln"] or None, "domaine": r["domain"] or None,
            "referent_ids": r["referent"].split() if r["referent"] else [],
            "sujet_ids": r["subjref"].split() if r["subjref"] else [],
        }
        verses.setdefault((book, ch, v), []).append(w)
        by_id[w["id"]] = w

def resolve(ids):
    out = []
    for i in ids:
        t = by_id.get(i)
        if t:
            g = (t["glose_en"] or t["lemme"]).strip(" ,.;")
            if g not in out:
                out.append(g)
    if len(out) > 6:                      # pronoms collectifs : garder lisible
        out = out[:6] + [f"+{len(out) - 6}"]
    return out or None

for ws in verses.values():
    for w in ws:
        w["referent"] = resolve(w.pop("referent_ids"))
        w["sujet"] = resolve(w.pop("sujet_ids"))

# ---------- 2. TAGNT (Strong étendus + variantes entre éditions) ----------
tag_line = re.compile(r"^(\w+)\.(\d+)\.(\d+)(?:\{[^}]*\})?#(\d+)=(\S+)\t")
tagnt = defaultdict(list)
for fn in sorted((SRC / "STEPBible-Data/Translators Amalgamated OT+NT").glob("TAGNT*.txt")):
    with open(fn, encoding="utf-8") as f:
        for line in f:
            m = tag_line.match(line)
            if not m:
                continue
            c = line.rstrip("\n").split("\t")
            book = TAG2USFM.get(m.group(1))
            if not book:
                continue
            ds = c[3].split("=")[0]                     # ex. G2424G
            ds = ds.split("«")[-1].split("|")[-1]
            greek = re.sub(r"\s*\(.*?\)\s*$", "", c[1]).strip()
            tagnt[(book, int(m.group(2)), int(m.group(3)))].append({
                "grec": greek, "en": c[2], "strong_etendu": ds,
                "editions": c[5].split("«")[0], "type": m.group(5),
            })

def norm(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^\w]", "", s).lower()

chapter_pool = defaultdict(list)
for k, tw in tagnt.items():
    chapter_pool[k[:2]].extend(tw)

stats = defaultdict(int)
for key, ws in verses.items():
    tw = tagnt.get(key, [])
    sbl = [t for t in tw if "SBL" in t["editions"].split("+")]
    # alignement séquentiel tolérant : même Strong classique, fenêtre glissante
    j = 0
    for w in ws:
        found = None
        for k in range(j, min(j + 4, len(sbl))):
            if classic(sbl[k]["strong_etendu"]) == w["strong"] or norm(sbl[k]["grec"]) == norm(w["grec"]):
                found = k
                break
        if found is not None:
            w["strong_etendu"] = sbl[found]["strong_etendu"]
            j = found + 1
            stats["strong_etendu_ok"] += 1
            continue
        # repli 1 : n'importe quelle édition, même verset puis même chapitre
        # (passages comme Jean 7:53-8:11, Marc 16:9-20, versification différente)
        pool = tw + chapter_pool.get(key[:2], [])
        alt = next((t for t in pool if norm(t["grec"]) == norm(w["grec"])
                    and classic(t["strong_etendu"]) == w["strong"]), None) \
              or next((t for t in pool if norm(t["grec"]) == norm(w["grec"])), None)
        if alt:
            w["strong_etendu"] = alt["strong_etendu"]
            stats["strong_etendu_repli"] += 1
        elif w["strong"]:
            w["strong_etendu"] = f"G{w['strong']:04d}"
            stats["strong_etendu_deduit"] += 1
        else:
            stats["strong_etendu_manquant"] += 1
    # variantes : mots présents dans d'autres éditions mais pas dans SBLGNT
    var = [{"grec": t["grec"], "en": t["en"], "editions": t["editions"]}
           for t in tw if "SBL" not in t["editions"].split("+")]
    verses[key] = {"mots": ws, "variantes_tagnt": var}

# versets absents de SBLGNT mais présents ailleurs (ex. Mat 17:21)
absent = []
for key, tw in tagnt.items():
    if key not in verses:
        absent.append({"ref": key, "grec": " ".join(t["grec"] for t in tw),
                       "en": " ".join(t["en"] for t in tw),
                       "editions": sorted({e for t in tw for e in t["editions"].split("+")})})

# ---------- 3. SBLGNT : paragraphes et apparat critique ----------
para_start = set()
for book_file, usfm in SBL2USFM.items():
    xml = (SRC / f"SBLGNT/data/sblgnt/xml/{book_file}.xml").read_text(encoding="utf-8-sig")
    pending = False
    for tok in re.finditer(r"<p>|<verse-number id=\"[^\"]*?(\d+):(\d+)\"", xml):
        if tok.group(0) == "<p>":
            pending = True
        elif pending:
            para_start.add((usfm, int(tok.group(1)), int(tok.group(2))))
            pending = False

apparat = {}
for book_file, usfm in SBL2USFM.items():
    txt = (SRC / f"SBLGNT/data/sblgntapp/text/{book_file}.txt").read_text(encoding="utf-8-sig")
    for block in re.split(r"\n\s*\n", txt):
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        m = re.match(r".*?(\d+):(\d+)$", lines[0])
        if m and len(lines) > 1:
            entries = []
            for l in lines[1:]:
                l = re.sub(r"^(\d+:)?\d+\s+", "", l.lstrip("• ").strip())
                entries.append(l)
            apparat[(usfm, int(m.group(1)), int(m.group(2)))] = entries

# ---------- 4. Assemblage par livre ----------
book_meta = {b[1]: b for b in BOOKS}
livres, all_verses = [], []
for order, usfm, tagc, sblf, fr in BOOKS:
    keys = [k for k in verses if k[0] == usfm]
    recs = []
    for (b, ch, v) in keys:
        d = verses[(b, ch, v)]
        ws = d["mots"]
        texte = "".join(w["grec"] + (w["apres"] if w["apres"].endswith(" ") else w["apres"] + " ")
                        for w in ws).strip()
        recs.append({
            "ref": f"{usfm} {ch}:{v}", "livre": usfm, "livre_fr": fr, "ordre_livre": order,
            "chapitre": ch, "verset": v,
            "debut_paragraphe": (b, ch, v) in para_start,
            "texte_grec": texte, "nb_mots": len(ws),
            "mots": ws,
            "apparat_sblgnt": apparat.get((b, ch, v), []),
            "variantes_tagnt": d["variantes_tagnt"],
        })
    (OUT / "versets").mkdir(exist_ok=True)
    (OUT / "versets" / f"{order:02d}-{usfm}.json").write_text(
        json.dumps(recs, ensure_ascii=False), encoding="utf-8")
    all_verses += recs
    livres.append({"code": usfm, "nom_fr": fr, "ordre": order,
                   "nb_chapitres": max(r["chapitre"] for r in recs),
                   "nb_versets": len(recs), "nb_mots": sum(r["nb_mots"] for r in recs)})

(OUT / "livres.json").write_text(json.dumps(livres, ensure_ascii=False, indent=1), encoding="utf-8")
absent_out = [{"ref": f"{k[0]} {k[1]}:{k[2]}", **{x: a[x] for x in ("grec", "en", "editions")}}
              for a in absent for k in [a["ref"]]]
absent_out.sort(key=lambda a: (book_meta[a["ref"].split()[0]][0], a["ref"]))
(OUT / "versets_hors_sblgnt.json").write_text(json.dumps(absent_out, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------- 5. Lexique TBESG ----------
lex = {}
L = SRC / "STEPBible-Data/Lexicons/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt"
with open(L, encoding="utf-8") as f:
    for line in f:
        c = line.rstrip("\n").split("\t")
        if len(c) < 8 or not re.match(r"^G\d{4}", c[0]):
            continue
        es = c[1].split("=")[0].strip()
        if not re.match(r"^G\d{4}\w*$", es) or es in lex:
            continue
        defin = re.sub(r"<BR\s*/?>", "\n", c[7], flags=re.I)
        defin = html.unescape(re.sub(r"<[^>]+>", "", defin)).strip()
        lex[es] = {"strong_etendu": es, "strong": classic(es), "lemme": c[3],
                   "translitteration": c[4], "morpho": c[5], "glose": c[6], "definition": defin}
used = {w["strong_etendu"] for r in all_verses for w in r["mots"] if w["strong_etendu"]}
# alias : un code employé dans le texte mais absent du lexique pointe vers
# l'entrée de même numéro (ex. G2453 -> G2453G)
for es in sorted(used - set(lex)):
    base = es[:5]
    cand = sorted(k for k in lex if k.startswith(base))
    if cand:
        lex[es] = {**lex[cand[0]], "strong_etendu": es, "alias_de": cand[0]}
stats["fin"] = 0
report_extra = {k: v for k, v in stats.items() if k.startswith("strong_etendu")}
(OUT / "lexique.json").write_text(json.dumps(list(lex.values()), ensure_ascii=False), encoding="utf-8")

report = {
    "versets": len(all_verses), "mots": sum(r["nb_mots"] for r in all_verses),
    "livres": len(livres), "debuts_paragraphe": sum(r["debut_paragraphe"] for r in all_verses),
    "versets_avec_apparat": sum(1 for r in all_verses if r["apparat_sblgnt"]),
    "versets_avec_variantes_tagnt": sum(1 for r in all_verses if r["variantes_tagnt"]),
    "versets_hors_sblgnt": len(absent_out),
    **report_extra,
    "lexique_entrees": len(lex), "strong_etendus_utilises": len(used),
    "strong_etendus_absents_du_lexique": sorted(used - set(lex))[:50],
}
(OUT / "rapport.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=1))
