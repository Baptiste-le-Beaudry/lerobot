import time
import cv2
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from lerobot.common.datasets.utils import hw_to_dataset_features
from lerobot.common.robots.lekiwi.config_lekiwi import LeKiwiClientConfig
from lerobot.common.robots.lekiwi.lekiwi_client import LeKiwiClient
from lerobot.common.teleoperators.keyboard import KeyboardTeleop, KeyboardTeleopConfig
from lerobot.common.teleoperators.so100_leader import SO100Leader, SO100LeaderConfig
import numpy as np
NB_CYCLES_CLIENT_CONNECTION = 250

leader_arm_config = SO100LeaderConfig(port="COM3")
leader_arm = SO100Leader(leader_arm_config)

keyboard_config = KeyboardTeleopConfig()
keyboard = KeyboardTeleop(keyboard_config)

robot_config = LeKiwiClientConfig(remote_ip="192.168.100.128", id="lekiwi")
robot = LeKiwiClient(robot_config)

action_features = hw_to_dataset_features(robot.action_features, "action")
obs_features = hw_to_dataset_features(robot.observation_features, "observation")
dataset_features = {**action_features, **obs_features}




dataset = LeRobotDataset.create(
    repo_id="Baptiste-le-Beaudry/lerobot-dataset" + str(int(time.time())),
    fps=10,
    features=dataset_features,
    robot_type=robot.name,
)

leader_arm.connect()
keyboard.connect()
robot.connect()

if not robot.is_connected or not leader_arm.is_connected or not keyboard.is_connected:
    exit()

print("Starting LeKiwi teleoperation")
i = 0
while i < NB_CYCLES_CLIENT_CONNECTION:
    arm_action = leader_arm.get_action()
    arm_action = {f"arm_{k}": v for k, v in arm_action.items()}

    keyboard_keys = keyboard.get_action()

    base_action = robot._from_keyboard_to_base_action(keyboard_keys)

    action = {**arm_action, **base_action} if len(base_action) > 0 else arm_action

    action_sent = robot.send_action(action)
    observation = robot.get_observation()


    task = "Dummy Example Task Dataset"

    ######
    # Construis le dictionnaire `frame` sans imbriquer `observation`
    
    frame = {**action_sent, **observation}

    # Nom “plat” de la clé pour l’image du poignet
    wrist_key = "observation.images.wrist"

    # Sécurité : vérifier que l'image existe
    if wrist_key not in frame:
        print("❌ L'image 'wrist' est introuvable dans le frame.")
        print(f"Clés disponibles : {list(frame.keys())}")
        exit(1)

    # Récupère l'image (Tensor ou ndarray)
    wrist_img = frame[wrist_key]
    # Si c'est un tensor PyTorch, convertis en ndarray
    if hasattr(wrist_img, "numpy"):
        wrist_img = wrist_img.numpy()

    # Corriger l'orientation si besoin
    if wrist_img.shape == (480, 640, 3):
        wrist_img = cv2.rotate(wrist_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif wrist_img.shape == (480, 3, 640):
        wrist_img = np.transpose(wrist_img, (0, 2, 1))

    # Remplace l'image dans le frame
    frame[wrist_key] = wrist_img

    # Ajoute la frame au dataset
    dataset.add_frame(frame, task)


    

    dataset.add_frame(frame, task)
    i += 1

print("Disconnecting Teleop Devices and LeKiwi Client")
robot.disconnect()
leader_arm.disconnect()
keyboard.disconnect()

print("Uploading dataset to the hub")
dataset.save_episode()
dataset.push_to_hub()