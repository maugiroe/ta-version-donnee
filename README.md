# « Ta version » — données grecques de travail (phase 0)

Jeu de données fusionné pour la traduction du Nouveau Testament, prêt à importer dans l'application Base44.

## Contenu

| Fichier | Contenu |
|---|---|
| `versets/NN-LIV.json` | Un fichier par livre, un enregistrement par verset (7 939 au total) |
| `livres.json` | Les 27 livres : code, nom français, chapitres, versets, mots |
| `lexique.json` | 11 052 entrées : Strong étendu, lemme, translittération, glose, définition |
| `versets_hors_sblgnt.json` | 18 versets présents dans d'autres éditions mais absents du texte SBLGNT |
| `rapport.json` | Chiffres de contrôle |

### Un verset

- `ref` (`MRK 1:15`), `livre`, `livre_fr`, `chapitre`, `verset`
- `debut_paragraphe` : vrai si un paragraphe SBLGNT commence ici (1 272 paragraphes)
- `texte_grec` : le verset complet
- `mots` : pour chaque mot grec
  - `id` : identifiant MACULA, stable, qui servira à l'alignement grec ↔ français
  - `grec`, `lemme`, `morpho`, `classe`
  - `strong` (classique) et `strong_etendu` (STEPBible)
  - `glose_en`, `glose_ctx` : gloses anglaises
  - `louw_nida`, `domaine` : sens du mot selon les domaines sémantiques
  - `referent`, `sujet` : qui est désigné par un pronom ou sujet implicite
- `apparat_sblgnt` : variantes des manuscrits notées par l'éditeur SBLGNT (4 468 versets)
- `variantes_tagnt` : mots présents dans d'autres éditions (NA28, TR, byzantin…) mais pas dans SBLGNT

## Points textuels à connaître pour la traduction

- **Versets absents du texte SBLGNT** : Mt 17:21, 18:11, 23:14 ; Mc 7:16, 9:44, 9:46, 11:26, 15:28 ; Lc 17:36, 23:17 ; Jn 5:4 ; Ac 8:37, 15:34, 24:7, 28:29 ; Rm 16:25-27. Ils sont fournis dans `versets_hors_sblgnt.json` pour être traduits en note.
- **Romains 16** : SBLGNT garde le verset 24 (« la grâce… ») et place la doxologie (16:25-27) seulement dans l'apparat. NA28 fait l'inverse. Décision à prendre.
- **Marc 16:9-20 et Jean 7:53-8:11** sont dans le jeu de données, entre doubles crochets. Il faudra une note expliquant qu'ils manquent dans les plus anciens manuscrits.

## Qualité

- Texte MACULA comparé mot à mot au texte SBLGNT officiel : 1 seule différence d'orthographe (Jn 8:5, Μωϋσῆς / Μωσῆς).
- Strong étendus : 136 730 mots alignés directement sur TAGNT, 779 par repli (passages à numérotation différente), 232 déduits du Strong classique. 100 % des mots ont une entrée de lexique.

## Sources et licences (attribution obligatoire)

- **SBLGNT** — *The Greek New Testament: SBL Edition*, © 2010 Society of Biblical Literature et Logos Bible Software, CC BY 4.0. https://sblgnt.com
- **MACULA Greek** — © Biblica, Inc. / Clear Bible, CC BY 4.0. https://github.com/Clear-Bible/macula-greek
- **STEPBible Data** (TAGNT, TBESG) — STEPBible.org, d'après Tyndale House Cambridge, CC BY 4.0. https://github.com/STEPBible/STEPBible-Data

Toutes les sources sont sous CC BY 4.0 : la traduction peut être publiée sous CC BY-SA 4.0, ce qui garantit qu'elle reste gratuite.

## Régénérer

```
python3 build.py <dossier_sources> <dossier_sortie>
python3 verify.py <dossier_sources> <dossier_sortie> "MRK 1:1"
```
