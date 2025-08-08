#!/usr/bin/env python3
# merge_full_datasets.py

import json
import shutil
import os
from pathlib import Path
from typing import Dict, Any


def load_meta(path: Path) -> Dict[str, Any]:
    meta = json.loads((path / "meta" / "info.json").read_text())
    return meta

def update_meta(meta1, meta2):
    merged = meta1.copy()
    # Totaux
    merged["total_episodes"] = meta1["total_episodes"] + meta2["total_episodes"]
    merged["total_frames"]   = meta1["total_frames"]   + meta2["total_frames"]
    merged["total_videos"]   = meta1["total_videos"]   + meta2["total_videos"]
    # Splits (train = "0:N")
    merged["splits"]["train"] = f"0:{merged['total_episodes']}"
    return merged

def merge_folder(src: Path, dst: Path, idx_offset: int, pattern: str):
    """
    Copie tous les fichiers matching pattern (glob) de src -> dst,
    en réindexant l'épisode de src par idx_offset.
    """
    for src_file in sorted(src.rglob(pattern)):
        # src_file.name = episode_000012.parquet or episode_000012.mp4
        num = int(src_file.stem.split("_")[1])
        new_num = num + idx_offset
        new_name = f"episode_{new_num:06d}{src_file.suffix}"
        # construit le même sous-dossier relatif
        rel = src_file.relative_to(src)
        dst_path = dst / rel.parent
        dst_path.mkdir(parents=True, exist_ok=True)
        shutil.copy(src_file, dst_path / new_name)

def main():
    base = Path.home() / ".cache" / "huggingface" / "lerobot" / "Baptiste-le-Beaudry"
    ds1 = base / "lekiwi_roll_to_lego"
    ds2 = base / "lekiwi_go_to_lego"
    out = Path.cwd() / "merged_lekiwi_roll_and_go"

    # 1) Charge et fusionne le meta
    meta1 = load_meta(ds1)
    meta2 = load_meta(ds2)
    merged_meta = update_meta(meta1, meta2)

    # 2) Copie les fichiers statiques (.gitattributes, README.md, LICENSE…)
    for fname in [".gitattributes", "README.md"]:
        src = ds1 / fname
        if src.exists():
            shutil.copy(src, out / fname)

    # 3) Fusionne le dossier 'data'
    idx_offset = meta1["total_episodes"]  # on commence ds2 après ds1
    merge_folder(ds1 / "data", out / "data", 0, "episode_*.parquet")
    merge_folder(ds2 / "data", out / "data", idx_offset, "episode_*.parquet")

    # 4) Fusionne le dossier 'videos'
    merge_folder(ds1 / "videos", out / "videos", 0, "episode_*.mp4")
    merge_folder(ds2 / "videos", out / "videos", idx_offset, "episode_*.mp4")

    # 5) Copie et mets à jour meta/info.json
    (out / "meta").mkdir(parents=True, exist_ok=True)
    with open(out / "meta" / "info.json", "w") as f:
        json.dump(merged_meta, f, indent=2)
    print(f"[✓] Dataset merged in `{out}`")
    print(f"    Total episodes: {merged_meta['total_episodes']}")
    print(f"    Total frames:   {merged_meta['total_frames']}")
    print(f"    Total videos:   {merged_meta['total_videos']}")

    print("\n👉 Il ne te reste plus qu’à :")
    print(f"   cd {out} && git init && git add . && git commit -m 'Merge datasets'")
    print("   git remote add origin https://huggingface.co/datasets/Baptiste-le-Beaudry/merged_lekiwi_roll_and_go")
    print("   git push origin main")

if __name__ == "__main__":
    main()
