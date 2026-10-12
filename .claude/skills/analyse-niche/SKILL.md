---
name: analyse-niche
description: Décortique des Reels / TikTok de référence (fichiers vidéo + stats) pour en tirer ce qui fait performer la niche de Maeldan : hooks, rythme de coupe, texte à l'écran, structure, son. Écrit et tient à jour niche/PLAYBOOK.md, que tout montage 9:16 doit lire avant de commencer. Déclencheurs : « analyse ces vidéos », « qu'est-ce qui marche dans ma niche », « ajoute cette référence », « mets à jour le playbook ».
---

# Analyse de niche (Reels / TikTok)

But : transformer un lot de vidéos qui performent en règles de montage chiffrées et
vérifiables, stockées dans `niche/PLAYBOOK.md`. Les skills de montage (`/hyperframes` et
ses workflows) lisent ce fichier avant de proposer un plan.

Deux couches, à ne jamais mélanger :
- **Mesures** (script) : durée, coupes, longueur des plans, timing du hook, couverture
  sonore. Objectives, comparables d'une vidéo à l'autre.
- **Lecture** (toi, en regardant les planches d'images) : type de hook, texte à l'écran,
  format, procédés de rétention, payoff, CTA. Remplie avec la grille de
  `references/grille.md`, jamais de mémoire ni par supposition.

## 1. Récupérer les vidéos

Le conteneur cloud **ne peut pas** joindre tiktok.com ni instagram.com (proxy 403, testé
le 2026-10-12 avec yt-dlp). Ne pas perdre de temps à réessayer. Sources possibles :

1. Fichiers MP4 envoyés dans le projet (`/mnt/project-files/uploads/…`) ou déposés dans
   un dossier de l'appareil de l'utilisateur. TikTok permet « Enregistrer la vidéo » ;
   pour Instagram, un enregistrement d'écran convient (couper la barre d'état).
2. Si une session tourne sur la machine de l'utilisateur (réseau non filtré),
   `yt-dlp -o "%(id)s.%(ext)s" URL` y fonctionne ; `yt-dlp -j URL` donne aussi
   vues / likes / commentaires.

Copier chaque vidéo dans `/mnt/project-files/niche/videos/<id>.mp4` (jamais dans git).
`<id>` = `<compte>-<sujet-court>`, en kebab-case.

**Stats** : pour chaque vidéo, il faut au minimum ses vues et la médiane des vues du
compte (sa base habituelle). Le plus simple : une capture d'écran de la grille du profil,
où chaque vignette affiche ses vues ; lis-la et calcule la médiane. Remplis
`niche/refs/<id>/meta.json` (format dans `scripts/aggregate.py`). Sans stats, la vidéo
reste analysable mais ne compte pas dans la comparaison outliers / reste.

Pourquoi la médiane du compte : 1 M de vues sur un compte à 2 M d'abonnés est un échec,
80 k sur un compte qui fait 5 k d'habitude est un signal fort. On étudie les vidéos qui
ont **surperformé leur propre compte** (score ≥ 3×), et on les compare aux vidéos
ordinaires des mêmes comptes : c'est l'écart entre les deux qui enseigne quelque chose.

## 2. Mesurer

```bash
python3 .claude/skills/analyse-niche/scripts/analyze_reel.py \
  /mnt/project-files/niche/videos/<id>.mp4 --out niche/refs/<id>
```

Produit `analysis.json`, `hook.jpg` (0 / 0,5 / 1 / 1,5 / 2 / 3 s) et `shots.jpg` (une
image par plan, horodatée). Seuil de coupe : 0,3 par défaut. Si `shots.jpg` montre des
coupes manquées (deux plans différents dans une même vignette) baisser à 0,2 ; si un même
plan apparaît plusieurs fois (mouvement rapide, flash) monter à 0,4. Les jump cuts sur un
même cadrage face caméra passent souvent sous le seuil : le noter dans la fiche.

Transcription (optionnelle) : `npx hyperframes transcribe <video>` sur la machine de
l'utilisateur. Dans le cloud, les modèles ne se téléchargent pas (huggingface bloqué) ;
s'appuyer alors sur les sous-titres incrustés visibles dans les planches.

## 3. Lire chaque vidéo

Ouvre `hook.jpg` et `shots.jpg` avec Read, puis remplis `niche/refs/<id>/fiche.md` avec la
grille de `references/grille.md`. Règles :
- Chaque affirmation pointe vers un instant (`0,5 s`, `plan #4`).
- Ce qui n'est pas visible dans les images (musique exacte, ton de voix) s'écrit
  « non vérifié » ou se demande à l'utilisateur.
- Termine par « Ce que Maeldan peut reprendre » : 1 à 3 procédés concrets, transposables
  à son métier (vidéaste, monteur, DA), pas le sujet de la vidéo.

## 4. Mettre à jour le playbook

```bash
python3 .claude/skills/analyse-niche/scripts/aggregate.py niche/refs
```

Colle la sortie dans la section « Benchmarks » de `niche/PLAYBOOK.md`, puis réécris les
sections qualitatives à partir des fiches. Une règle n'entre dans le playbook que si elle
apparaît dans au moins 3 références (ou est marquée « hypothèse, 1-2 réf. »). Indique le
nombre de références derrière chaque règle. Date la mise à jour.

Taille d'échantillon : sous 10 références, le playbook décrit des tendances, pas des
lois. Le dire en tête de fichier. 15 à 30 références issues de 5+ comptes de la niche,
dont des vidéos ordinaires des mêmes comptes, donnent une base sérieuse.

Les trends (sons, formats) vieillissent en semaines : chaque référence garde sa date de
publication ; au-delà de 3 mois, la marquer « ancienne » dans le playbook.

## 5. Utiliser le playbook pour un montage

Avant tout montage 9:16, lis `niche/PLAYBOOK.md` et annonce en 2-3 lignes les règles
appliquées (ex. « hook texte + mouvement avant 0,5 s, une coupe toutes les 1,5 s, boucle
fin → début »). Si le brief de l'utilisateur contredit le playbook, suis le brief et
signale l'écart une fois.

Après publication d'une vidéo de Maeldan, ses propres stats valent plus que n'importe
quelle référence externe : les ajouter comme références (`<id>` préfixé `moi-`) pour que
le playbook apprenne de son audience réelle.

## Fichiers

- `scripts/analyze_reel.py` : mesures + planches (ffmpeg, Pillow optionnel).
- `scripts/aggregate.py` : tableau des références et benchmarks outliers / reste.
- `references/grille.md` : grille de lecture et taxonomie des hooks.
- `niche/PLAYBOOK.md` (racine du dépôt) : le livrable vivant.
- `niche/refs/<id>/` : `analysis.json`, `meta.json`, `fiche.md`, planches JPG.
