from lerobot.common.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.common.cameras.opencv.configuration_opencv import OpenCVCameraConfig

def debug_camera(index: int):
    print(f"\n>>> Testing LeRobot OpenCVCamera with index {index}")
    config = OpenCVCameraConfig(
        index_or_path=index,
        width=640,
        height=480,
        fps=30
    )
    camera = OpenCVCamera(config)

    try:
        camera.connect()
        frame = camera.read()
        print(f"✅ Success reading frame from camera {index}: shape={frame.shape}")
        camera.release()
    except Exception as e:
        print(f"❌ Failed with exception: {e}")

if __name__ == "__main__":
    for index in [0, 1, 2]:
        debug_camera(index)
