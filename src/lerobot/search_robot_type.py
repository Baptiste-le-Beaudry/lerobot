# search_robot_type.py
import os

for root, dirs, files in os.walk("lerobot"):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if "robot.type" in line:
                        print(f"{path}:{i}: {line.strip()}")
