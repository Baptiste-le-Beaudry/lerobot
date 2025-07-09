#!/usr/bin/env python

# Hardcoded policy-only recording script for LeKiwi
# Automatically uses the configured robot and policy without CLI arguments

import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from pprint import pformat

import numpy as np
import rerun as rr

from lerobot.common.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.common.datasets.image_writer import safe_stop_image_writer
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from lerobot.common.datasets.utils import build_dataset_frame, hw_to_dataset_features
from lerobot.common.policies.factory import make_policy
from lerobot.common.policies.pretrained import PreTrainedPolicy
from lerobot.common.robots import make_robot_from_config, RobotConfig
from lerobot.common.utils.control_utils import (
    init_keyboard_listener,
    sanity_check_dataset_name,
    sanity_check_dataset_robot_compatibility,
)
from lerobot.common.utils.robot_utils import busy_wait
from lerobot.common.utils.utils import get_safe_torch_device, init_logging, log_say
from lerobot.common.utils.visualization_utils import _init_rerun

# === User Configuration (hardcoded) ===
ROBOT_CONFIG = RobotConfig(
    type="so100_follower",
    id="lekiwi",
    port="/dev/ttyACM0",
    cameras={
        "front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}
    }
)
DATASET_REPO = "Baptiste-le-Beaudry/eval_lekiwi"
SINGLE_TASK = "center_over_block"
NUM_EPISODES = 10
POLICY_CONFIG = {
    "path": "Baptiste-le-Beaudry/act_lekiwi_full",
    "type": "act"
}

# Derived dataclass equivalents
@dataclass
class HardDatasetConfig:
    repo_id: str = DATASET_REPO
    single_task: str = SINGLE_TASK
    root: Path | str | None = None
    fps: int = 30
    episode_time_s: float = 60
    reset_time_s: float = 10
    num_episodes: int = NUM_EPISODES
    video: bool = True
    push_to_hub: bool = True
    private: bool = False
    tags: list[str] | None = None
    num_image_writer_processes: int = 0
    num_image_writer_threads_per_camera: int = 4

@dataclass
class HardPolicyConfig:
    path: str = POLICY_CONFIG["path"]
    type: str = POLICY_CONFIG["type"]

# Recording loop
@safe_stop_image_writer
def record_loop(robot, events, cfg, dataset, policy):
    fps = cfg.fps
    control_time_s = cfg.episode_time_s
    t0 = time.perf_counter()
    policy.reset()
    while time.perf_counter() - t0 < control_time_s:
        start = time.perf_counter()
        obs = robot.get_observation()
        frame_obs = build_dataset_frame(dataset.features, obs, prefix="observation")
        action_vals = policy.predict(
            frame_obs,
            task=cfg.single_task,
            device=get_safe_torch_device(policy.config.device),
            use_amp=policy.config.use_amp,
        )
        action = {k: action_vals[i].item() for i, k in enumerate(robot.action_features)}
        sent = robot.send_action(action)
        frame_act = build_dataset_frame(dataset.features, sent, prefix="action")
        dataset.add_frame({**frame_obs, **frame_act}, task=cfg.single_task)
        busy_wait(max(1/fps - (time.perf_counter() - start), 0))

# Main
if __name__ == "__main__":
    init_logging()
    logging.info("Starting hardcoded policy recording for LeKiwi")
    _init_rerun(session_name="record_policy_fixed")

    # Setup robot
    robot = make_robot_from_config(ROBOT_CONFIG)

    # Dataset
    ds_cfg = HardDatasetConfig()
    features = hw_to_dataset_features(robot.action_features, "action", ds_cfg.video)
    features |= hw_to_dataset_features(robot.observation_features, "observation", ds_cfg.video)
    if ds_cfg.num_episodes is None:
        ds_cfg.num_episodes = NUM_EPISODES

    # Create or resume dataset
    dataset = LeRobotDataset.create(
        ds_cfg.repo_id,
        ds_cfg.fps,
        root=ds_cfg.root,
        robot_type=robot.name,
        features=features,
        use_videos=ds_cfg.video,
        image_writer_processes=ds_cfg.num_image_writer_processes,
        image_writer_threads=ds_cfg.num_image_writer_threads_per_camera * len(robot.cameras),
    )

    # Policy
    policy = make_policy(HardPolicyConfig, ds_meta=dataset.meta)

    # Connect
    robot.connect()
    listener, events = init_keyboard_listener()

    # Record episodes
    for _ in range(ds_cfg.num_episodes):
        log_say(f"Recording episode {_+1}/{ds_cfg.num_episodes}", True)
        record_loop(robot, events, ds_cfg, dataset, policy)
        # Reset period
        busy_wait(ds_cfg.reset_time_s)
        dataset.save_episode()

    robot.disconnect()
    listener.stop()
    if ds_cfg.push_to_hub:
        dataset.push_to_hub()
    logging.info("Finished recording.")
