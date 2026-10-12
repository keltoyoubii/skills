#!/usr/bin/env python3
"""Mesure objective d'un Reel / TikTok local : rythme de montage, hook, audio.

Usage : python3 analyze_reel.py VIDEO.mp4 --out DOSSIER [--scene 0.3]

Produit dans DOSSIER :
  analysis.json   mesures (durée, coupes, plans, audio)
  hook.jpg        planche des 3 premières secondes (0 / 0.5 / 1 / 1.5 / 2 / 3 s)
  shots.jpg       planche d'une image par plan (milieu du plan), horodatée
  frames/         images sources des planches

Dépendances : ffmpeg/ffprobe. Pillow (optionnel) pour les planches légendées,
sinon repli sur le filtre tile de ffmpeg.
"""
import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

HOOK_TIMES = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
MAX_SHOT_FRAMES = 30
THUMB_W = 270  # 1080/4


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    if r.returncode != 0:
        sys.exit(f"ffprobe a échoué : {r.stderr.strip()}")
    data = json.loads(r.stdout)
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        sys.exit("aucune piste vidéo")
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []):
        rot = int(sd.get("rotation", 0) or 0)
    if abs(rot) == 90:
        w, h = h, w
    return {
        "duration_s": round(float(data["format"]["duration"]), 2),
        "width": w,
        "height": h,
        "aspect": f"{w}:{h}",
        "is_vertical_9_16": abs(w / h - 9 / 16) < 0.02,
        "fps": round(fps, 2),
        "has_audio": a is not None,
    }


def detect_cuts(path, threshold):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-an",
             "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    return [round(float(t), 2) for t in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def shots_from_cuts(cuts, duration):
    bounds = [0.0] + [c for c in cuts if 0.05 < c < duration - 0.05] + [duration]
    return [(round(a, 2), round(b, 2)) for a, b in zip(bounds, bounds[1:]) if b - a > 0.04]


def audio_stats(path, duration):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn",
             "-af", "silencedetect=noise=-35dB:d=0.25,ebur128", "-f", "null", "-"])
    err = r.stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
    silences = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else duration
        silences.append((max(0.0, s), min(duration, e)))
    silent = sum(e - s for s, e in silences)
    first_sound = 0.0
    if silences and silences[0][0] <= 0.05:
        first_sound = silences[0][1]
    lufs = re.findall(r"I:\s+(-?[0-9.]+) LUFS", err)
    return {
        "integrated_lufs": float(lufs[-1]) if lufs else None,
        "sound_coverage": round(1 - silent / duration, 2) if duration else None,
        "first_sound_s": round(first_sound, 2),
        "silences": [[round(s, 2), round(e, 2)] for s, e in silences],
    }


def grab(path, t, dest):
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(path),
         "-frames:v", "1", "-vf", f"scale={THUMB_W}:-2", "-q:v", "3", str(dest)])
    return dest.exists()


def sheet(images, labels, dest, cols):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        Image = None
    if Image is None:
        pattern = str(images[0].parent / (images[0].stem.rsplit("_", 1)[0] + "_*.jpg"))
        rows = -(-len(images) // cols)
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-pattern_type", "glob", "-i", pattern,
             "-vf", f"tile={cols}x{rows}:padding=6:color=black", "-frames:v", "1", str(dest)])
        return
    tiles = [Image.open(p).convert("RGB") for p in images]
    tw, th = tiles[0].size
    pad, band = 6, 26
    rows = -(-len(tiles) // cols)
    out = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + band + pad) + pad), "black")
    d = ImageDraw.Draw(out)
    for i, (im, lab) in enumerate(zip(tiles, labels)):
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + band + pad)
        out.paste(im.resize((tw, th)), (x, y + band))
        d.text((x + 4, y + 6), lab, fill="white")
    out.save(dest, quality=85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--scene", type=float, default=0.3,
                    help="seuil de détection de coupe (0.2 = sensible, 0.4 = strict)")
    args = ap.parse_args()

    video = Path(args.video)
    out = Path(args.out)
    frames = out / "frames"
    frames.mkdir(parents=True, exist_ok=True)

    meta = probe(video)
    dur = meta["duration_s"]
    cuts = detect_cuts(video, args.scene)
    shots = shots_from_cuts(cuts, dur)
    lengths = [b - a for a, b in shots]
    cut_times = [a for a, _ in shots[1:]]

    edit = {
        "scene_threshold": args.scene,
        "cuts": len(cut_times),
        "cut_times_s": cut_times,
        "cuts_per_10s": round(len(cut_times) / dur * 10, 2) if dur else None,
        "shots": len(shots),
        "shot_len_median_s": round(statistics.median(lengths), 2) if lengths else None,
        "shot_len_min_s": round(min(lengths), 2) if lengths else None,
        "shot_len_max_s": round(max(lengths), 2) if lengths else None,
        "first_cut_s": cut_times[0] if cut_times else None,
        "cuts_in_first_3s": sum(1 for c in cut_times if c <= 3.0),
        # rythme par tiers : un montage qui ralentit en fin de vidéo perd souvent l'attention
        "cuts_by_third": [sum(1 for c in cut_times if i * dur / 3 <= c < (i + 1) * dur / 3) for i in range(3)],
    }

    hook_imgs, hook_labels = [], []
    for t in HOOK_TIMES:
        if t < dur:
            p = frames / f"hook_{int(t * 1000):05d}.jpg"
            if grab(video, min(t, dur - 0.05), p):
                hook_imgs.append(p)
                hook_labels.append(f"{t:.1f}s")
    if hook_imgs:
        sheet(hook_imgs, hook_labels, out / "hook.jpg", cols=len(hook_imgs))

    picked = shots
    if len(shots) > MAX_SHOT_FRAMES:
        step = len(shots) / MAX_SHOT_FRAMES
        picked = [shots[int(i * step)] for i in range(MAX_SHOT_FRAMES)]
    shot_imgs, shot_labels = [], []
    for i, (a, b) in enumerate(picked):
        p = frames / f"shot_{i:03d}.jpg"
        if grab(video, (a + b) / 2, p):
            shot_imgs.append(p)
            shot_labels.append(f"#{shots.index((a, b)) + 1} {a:.1f}-{b:.1f}s")
    if shot_imgs:
        sheet(shot_imgs, shot_labels, out / "shots.jpg", cols=6)

    result = {
        "source": video.name,
        "video": meta,
        "edit": edit,
        "audio": audio_stats(video, dur) if meta["has_audio"] else None,
        "shot_list": [[a, b] for a, b in shots],
        "shot_frames_sampled": len(shot_imgs) < len(shots),
    }
    (out / "analysis.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    e = edit
    print(f"{video.name}: {dur}s, {e['shots']} plans, {e['cuts_per_10s']} coupes/10s, "
          "1re coupe " + (f"{e['first_cut_s']}s" if e['first_cut_s'] is not None else "aucune") + ", " +
          f"{e['cuts_in_first_3s']} coupes dans les 3 premières s -> {out}")


if __name__ == "__main__":
    main()
