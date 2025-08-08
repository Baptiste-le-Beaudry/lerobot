#!/usr/bin/env python
import logging
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from huggingface_hub import HfApi, ModelCard, ModelCardData

logging.basicConfig(level=logging.INFO)


def push_folder_to_hub(model_dir: str):
    """
    Copie le dossier `model_dir` (contenant model.safetensors, config.json, train_config.json, etc.)
    dans un répertoire temporaire, y ajoute un README minimal, puis push le tout sur Hugging Face Hub.
    """
    # 1️⃣ Créer/obtenir le repo HF
    # On lit le repo_id depuis le config.json
    import json
    cfg = json.load(open(os.path.join(model_dir, "config.json"), "r", encoding="utf-8"))
    repo_id = cfg.get("repo_id")
    if repo_id is None:
        raise ValueError("Le champ `repo_id` doit être présent dans config.json")

    api = HfApi()
    logging.info(f"☁️  Creating or fetching Hugging Face repo '{repo_id}'")
    api.create_repo(repo_id=repo_id, private=cfg.get("private", False), exist_ok=True)

    # 2️⃣ Copie dans un tmp dir
    with TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp) / repo_id
        logging.info(f"🗂️  Copying files from {model_dir} to {tmp_dir}")
        shutil.copytree(model_dir, tmp_dir)

        # 3️⃣ Générer un README.md si absent
        readme_path = tmp_dir / "README.md"
        if not readme_path.exists():
            logging.info("✏️  Generating minimal README.md")
            card_data = ModelCardData(
                license=cfg.get("license") or "apache-2.0",
                library_name="lerobot",
                pipeline_tag="robotics",
                tags=cfg.get("tags") or ["robotics"],
                model_name=cfg.get("type", "model"),
                datasets=None,
                base_model=None,
            )
            card = ModelCard.from_template(
                card_data,
                template_str=(
                    f"# {Path(model_dir).name}\n\n"
                    "Modèle entraîné avec LeRobot (ACT policy) pour pick-and-place LEGO.\n"
                    f"– repo_id: **{repo_id}**\n"
                    f"– config: `{tmp_dir / 'config.json'}`\n"
                    f"– train config: `{tmp_dir / 'train_config.json'}`\n"
                    f"– poids: `model.safetensors`\n"
                )
            )
            card.save(readme_path)

        # 4️⃣ Pusher le contenu
        logging.info(f"🚀  Pushing contents of {tmp_dir} to the Hub")
        commit_info = api.upload_folder(
            repo_id=repo_id,
            repo_type="model",
            folder_path=tmp_dir,
            commit_message="Initial upload: model weights, configs, README",
            allow_patterns=["*.safetensors", "*.json", "*.yaml", "*.md"],
            ignore_patterns=["*.tmp", "*.log"],
        )
        logging.info(f"✅ Successfully pushed: {commit_info.repo_url.url}")


if __name__ == "__main__":
    # Chemin vers ton dossier contenant model.safetensors, config.json, train_config.json…
    push_folder_to_hub("C:/lerobot/outputs/train/act_lekiwi_pick_and_place_lego")
