# run_convert.py
from pathlib import Path
import traceback
import lerobot.datasets.v2.convert_dataset_v1_to_v2 as conv_mod

# ----- EDIT THESE IF NEEDED -----
REPO_ID = "Baptiste-le-Beaudry/lekiwi_roll_to_and_look_lego"
SINGLE_TASK = "lekiwi_roll_to_blue_lego"
LOCAL_DIR = Path(r"C:/tmp/lerobot_dataset_v2")  # racine qui contient v1.6/...
ROBOT_ID = "motsaikiwi"  # juste pour info/compatibilité
# -------------------------------

# Keep original parse if present
_real_parse = getattr(conv_mod, "parse_robot_config", None)

# We'll build a dict {'robot_type': <>, 'names': {...}} and also create a
# lightweight object with .type so convert_dataset() can read robot_config.type later.
class OrigRobotObj:
    def __init__(self, rtype: str, id: str | None = None, **kwargs):
        self.type = rtype
        self.robot_type = rtype
        self.id = id
        # keep other attrs if needed
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f"OrigRobotObj(type={self.type!r}, id={self.id!r})"


def _parse_wrapper(robot_cfg):
    """
    Wrapper for parse_robot_config used by get_features_from_hf_dataset.
    Behavior:
      - If robot_cfg is already a dict, return it (it's assumed to be the expected format).
      - If robot_cfg has an attribute 'type' and is NOT an aloha/koch robot, return the
        precomputed robot_config_dict (see below).
      - Otherwise, defer to the original parse function.
    """
    # if the caller passed a dict already — just return it
    if isinstance(robot_cfg, dict):
        return robot_cfg

    # If it's an OrigRobotObj (or any object with .type) and not aloha/koch,
    # return the dict we'll build below (we set `robot_config_dict` in outer scope).
    if hasattr(robot_cfg, "type"):
        if getattr(robot_cfg, "type") not in ("aloha", "koch"):
            # robot_config_dict will be defined before we call convert_dataset
            return robot_config_dict

    # fallback to original parser if available
    if _real_parse is not None:
        return _real_parse(robot_cfg)
    return robot_cfg


# Apply monkey-patch
conv_mod.parse_robot_config = _parse_wrapper

# Build the robot_config_dict by inspecting the v1 dataset locally
from datasets import load_dataset
import datasets as _ds

v1_data_dir = LOCAL_DIR / "v1.6" / REPO_ID / "data"
print("Loading dataset to infer sequence lengths (this is local, fast)...")
dataset = load_dataset("parquet", data_dir=v1_data_dir, split="train")

names_map: dict = {}
for key, ft in dataset.features.items():
    if isinstance(ft, _ds.Sequence):
        length = ft.length
        names_map[key] = [f"motor_{i}" for i in range(length)]

print("Detected sequence features and generated names:")
for k, v in names_map.items():
    print(f"  {k}: {len(v)} names (example: {v[:6]})")

# final dict parse_robot_config expects (format enforced by code)
robot_config_dict = {"robot_type": "lekiwi", "names": names_map}

# create the original object that convert_dataset will later inspect (.type)
orig_robot_obj = OrigRobotObj("lekiwi", id=ROBOT_ID)

# Call convert_dataset with orig_robot_obj (so later robot_config.type works)
from lerobot.datasets.v2.convert_dataset_v1_to_v2 import convert_dataset

try:
    convert_dataset(
        repo_id=REPO_ID,
        single_task=SINGLE_TASK,
        local_dir=LOCAL_DIR,
        robot_config=orig_robot_obj,
    )
    print("✅ convert_dataset completed (or advanced without raising a final exception).")
except Exception:
    print("❌ convert_dataset crashed; full traceback below:")
    traceback.print_exc()
