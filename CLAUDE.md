# Skills de Maeldan

Dépôt de skills Claude pour la création de vidéos 9:16 (TikTok / Instagram).

## HyperFrames

`.claude/skills/` contient les 21 skills publiés de [HyperFrames](https://github.com/heygen-com/hyperframes)
(HTML → MP4 déterministe), copiés depuis le commit `ce08f2042e701269345b29c32d632f8dbf1c4915`
(licence Apache 2.0, voir `.claude/skills/HYPERFRAMES-LICENSE`). Point d'entrée : `/hyperframes`.

Mise à jour : `npx hyperframes skills update` (ou recopier `skills/` depuis le dépôt amont).

### Format par défaut

Toujours initialiser en vertical : `npx hyperframes init <nom> --non-interactive --resolution=portrait`
(1080×1920). Prérequis : Node 22+, FFmpeg.

### Sessions cloud Claude Code (conteneur avec proxy)

Le Chromium headless du rendu ne passe pas par le proxy du conteneur : tout script chargé
depuis un CDN (ex. GSAP sur jsdelivr) échoue avec `sub_timeline_script_failure`.
Servir les librairies en local depuis npm :

```bash
npm pack gsap@3.14.2 && tar xzf gsap-3.14.2.tgz package/dist/gsap.min.js \
  && mv package/dist/gsap.min.js . && rm -rf package gsap-*.tgz
sed -i 's#https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js#gsap.min.js#' index.html
```

`HYPERFRAMES_SKIP_SKILLS=1` évite que `init` retélécharge les skills.

## Analyse de niche

`/analyse-niche` décortique des Reels / TikTok de référence (fichiers + stats) et tient à
jour `niche/PLAYBOOK.md`. **Avant tout montage 9:16, lire `niche/PLAYBOOK.md`** et dire
quelles règles on applique. Les vidéos ne vont pas dans git ; seules les mesures, fiches et
planches (`niche/refs/<id>/`) y vont. Le conteneur cloud ne joint ni TikTok ni Instagram :
travailler à partir de fichiers fournis.
