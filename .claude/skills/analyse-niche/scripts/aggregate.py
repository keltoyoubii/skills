#!/usr/bin/env python3
"""Agrège les références analysées en benchmarks chiffrés pour PLAYBOOK.md.

Usage : python3 aggregate.py niche/refs

Chaque sous-dossier de référence contient analysis.json (analyze_reel.py) et
optionnellement meta.json :
  {"url": "...", "account": "@x", "platform": "tiktok|instagram",
   "views": 1200000, "likes": 0, "comments": 0, "shares": 0, "saves": 0,
   "account_median_views": 80000, "posted": "2026-09-30"}

Score de surperformance = views / account_median_views. Les vues brutes
mesurent surtout la taille du compte ; ce ratio isole ce que la vidéo a fait
de mieux que d'habitude. Les vidéos à score >= 3 forment le groupe « outliers ».
"""
import json
import statistics
import sys
from pathlib import Path

OUTLIER = 3.0


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 2) if xs else None


def load(root):
    refs = []
    for d in sorted(Path(root).iterdir()):
        a = d / "analysis.json"
        if not a.exists():
            continue
        m = d / "meta.json"
        meta = json.loads(m.read_text()) if m.exists() else {}
        refs.append({"id": d.name, "a": json.loads(a.read_text()), "m": meta})
    return refs


def score(r):
    v, base = r["m"].get("views"), r["m"].get("account_median_views")
    return round(v / base, 1) if v and base else None


def engagement(r):
    m = r["m"]
    v = m.get("views")
    parts = [m.get(k) for k in ("likes", "comments", "shares", "saves")]
    if not v or all(p is None for p in parts):
        return None
    return round(100 * sum(p or 0 for p in parts) / v, 1)


def row(label, group):
    a = [r["a"] for r in group]
    return (f"| {label} ({len(group)}) | {med([x['video']['duration_s'] for x in a])} "
            f"| {med([x['edit']['cuts_per_10s'] for x in a])} "
            f"| {med([x['edit']['shot_len_median_s'] for x in a])} "
            f"| {med([x['edit']['first_cut_s'] for x in a])} "
            f"| {med([x['edit']['cuts_in_first_3s'] for x in a])} "
            f"| {med([(x['audio'] or {}).get('sound_coverage') for x in a])} |")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    refs = load(sys.argv[1])
    if not refs:
        sys.exit("aucune référence analysée")

    print("## Références\n")
    print("| id | compte | durée | coupes/10s | 1re coupe | surperf. | engagement % |")
    print("|---|---|---|---|---|---|---|")
    for r in sorted(refs, key=lambda r: -(score(r) or 0)):
        e = r["a"]["edit"]
        s, eng = score(r), engagement(r)
        print(f"| {r['id']} | {r['m'].get('account', '?')} | {r['a']['video']['duration_s']}s "
              f"| {e['cuts_per_10s']} | {e['first_cut_s'] if e['first_cut_s'] is not None else '-'} "
              f"| {f'{s}x' if s is not None else '?'} | {eng if eng is not None else '?'} |")

    scored = [r for r in refs if score(r) is not None]
    top = [r for r in scored if score(r) >= OUTLIER]
    rest = [r for r in scored if score(r) < OUTLIER]
    print("\n## Benchmarks (médianes)\n")
    print("| groupe | durée s | coupes/10s | plan médian s | 1re coupe s | coupes < 3s | couverture son |")
    print("|---|---|---|---|---|---|---|")
    print(row("toutes", refs))
    if top:
        print(row(f"outliers >= {OUTLIER:g}x", top))
    if rest:
        print(row("le reste", rest))
    if len(top) < 3 or len(rest) < 3:
        print(f"\n> Comparaison outliers / reste peu fiable : {len(top)} outliers, {len(rest)} autres "
              f"avec stats. Il en faut au moins 3 de chaque ; {len(refs) - len(scored)} réf. sans meta.json.")


if __name__ == "__main__":
    main()
