import json
import shutil
from pathlib import Path

# 1️⃣ Chemin vers la racine de ton dataset HF
ROOT = Path(__file__).parent

# 2️⃣ On pointe vers meta/dataset_info.json
info_path = ROOT / "meta" / "info.json"

# Si tu as vraiment un dataset_info ailleurs, adapte ce chemin.
if not info_path.exists():
    print(f"Aucun {info_path} trouvé, passe cette étape.")
    meta = {}
else:
    meta = json.loads(info_path.read_text())

# Liste des épisodes à supprimer
to_delete = {40, 41, 42, 43, 45}

# 3️⃣ Parcours des chunks de données
for chunk_dir in (ROOT / "data").glob("chunk-*"):
    for ep_file in chunk_dir.glob("episode_*.parquet"):
        idx = int(ep_file.stem.split("_")[1])
        if idx in to_delete:
            print(f"Supprimé (data): {ep_file}")
            ep_file.unlink(missing_ok=True)

# 4️⃣ Parcours des vidéos
for cam in ("observation.images.front", "observation.images.wrist"):
    vid_dir = ROOT / "videos" / "chunk-000" / cam
    for idx in to_delete:
        mp4 = vid_dir / f"episode_{idx:06d}.mp4"
        if mp4.exists():
            print(f"Supprimé (video/{cam}): {mp4}")
            mp4.unlink()
        else:
            # déjà supprimé ou jamais créé, on ne crie pas
            pass

# 5️⃣ Mettre à jour dataset_info.json si besoin
if meta:
    old_total = meta.get("total_episodes", None)
    meta["total_episodes"] = old_total - len([i for i in to_delete if i < old_total])
    info_path.write_text(json.dumps(meta, indent=4))
    print(f"Mis à jour {info_path} → total_episodes = {meta['total_episodes']}")

print("Opération terminée.")
