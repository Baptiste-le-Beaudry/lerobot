# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Provides the OpenCVCamera class for capturing frames from cameras using OpenCV.
"""

import logging
import math
import os
import platform
import time
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any

# Fix MSMF hardware transform compatibility for Windows before importing cv2
if platform.system() == "Windows" and "OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS" not in os.environ:
    os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import cv2
import numpy as np

from lerobot.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from ..camera import Camera
from ..utils import get_cv2_backend, get_cv2_rotation
from .configuration_opencv import ColorMode, OpenCVCameraConfig

# NOTE(Steven): The maximum opencv device index depends on your operating system. For instance,
# if you have 3 cameras, they should be associated to index 0, 1, and 2. This is the case
# on MacOS. However, on Ubuntu, the indices are different like 6, 16, 23.
# When you change the USB port or reboot the computer, the operating system might
# treat the same cameras as new devices. Thus we select a higher bound to search indices.
MAX_OPENCV_INDEX = 60

logger = logging.getLogger(__name__)


class OpenCVCamera(Camera):
    """
    Manages camera interactions using OpenCV for efficient frame recording.

    This class provides a high-level interface to connect to, configure, and read
    frames from cameras compatible with OpenCV's VideoCapture. It supports both
    synchronous and asynchronous frame reading.

    An OpenCVCamera instance requires a camera index (e.g., 0) or a device path
    (e.g., '/dev/video0' on Linux). Camera indices can be unstable across reboots
    or port changes, especially on Linux. Use the provided utility script to find
    available camera indices or paths:
    ```bash
    python -m lerobot.find_cameras opencv
    ```

    The camera's default settings (FPS, resolution, color mode) are used unless
    overridden in the configuration.

    Example:
        ```python
        from lerobot.cameras.opencv import OpenCVCamera
        from lerobot.cameras.configuration_opencv import OpenCVCameraConfig, ColorMode, Cv2Rotation

        # Basic usage with camera index 0
        config = OpenCVCameraConfig(index_or_path=0)
        camera = OpenCVCamera(config)
        camera.connect()

        # Read 1 frame synchronously
        color_image = camera.read()
        print(color_image.shape)

        # Read 1 frame asynchronously
        async_image = camera.async_read()

        # When done, properly disconnect the camera using
        camera.disconnect()

        # Example with custom settings
        custom_config = OpenCVCameraConfig(
            index_or_path='/dev/video0', # Or use an index
            fps=30,
            width=1280,
            height=720,
            color_mode=ColorMode.RGB,
            rotation=Cv2Rotation.ROTATE_90
        )
        custom_camera = OpenCVCamera(custom_config)
        # ... connect, read, disconnect ...
        ```
    """

    def __init__(self, config: OpenCVCameraConfig):
        """
        Initializes the OpenCVCamera instance.

        Args:
            config: The configuration settings for the camera.
        """
        super().__init__(config)

        self.config = config
        self.index_or_path = config.index_or_path

        self.fps = config.fps
        self.color_mode = config.color_mode
        self.warmup_s = config.warmup_s

        self.videocapture: cv2.VideoCapture | None = None

        self.thread: Thread | None = None
        self.stop_event: Event | None = None
        self.frame_lock: Lock = Lock()
        self.latest_frame: np.ndarray | None = None
        self.new_frame_event: Event = Event()

        self.rotation: int | None = get_cv2_rotation(config.rotation)
        self.backend: int = get_cv2_backend()

        if self.height and self.width:
            self.capture_width, self.capture_height = self.width, self.height
            if self.rotation in [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE]:
                self.capture_width, self.capture_height = self.height, self.width

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.index_or_path})"

    @property
    def is_connected(self) -> bool:
        """Checks if the camera is currently connected and opened."""
        return isinstance(self.videocapture, cv2.VideoCapture) and self.videocapture.isOpened()

    def connect(self, warmup: bool = True):
        """
        Connects to the OpenCV camera specified in the configuration.

        Initializes the OpenCV VideoCapture object, sets desired camera properties
        (FPS, width, height), and performs initial checks.

        Raises:
            DeviceAlreadyConnectedError: If the camera is already connected.
            ConnectionError: If the specified camera index/path is not found or the camera is found but fails to open.
            RuntimeError: If the camera opens but fails to apply requested FPS/resolution settings.
        """
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} is already connected.")

        # Use 1 thread for OpenCV operations to avoid potential conflicts or
        # blocking in multi-threaded applications, especially during data collection.
        cv2.setNumThreads(1)

        self.videocapture = cv2.VideoCapture(self.index_or_path, self.backend)

        if not self.videocapture.isOpened():
            self.videocapture.release()
            self.videocapture = None
            raise ConnectionError(
                f"Failed to open {self}."
                f"Run `python -m lerobot.find_cameras opencv` to find available cameras."
            )

        self._configure_capture_settings()

        if warmup:
            start_time = time.time()
            while time.time() - start_time < self.warmup_s:
                self.read()
                time.sleep(0.1)

        logger.info(f"{self} connected.")


    def _configure_capture_settings(self) -> None:
        """
        Applies the specified FPS, width, and height settings to the connected camera.

        This method attempts to set the camera properties via OpenCV. It checks if
        the camera successfully applied the settings and raises an error if not.

        Raises:
            RuntimeError: If the camera fails to set any of the specified properties
                          to the requested value.
            DeviceNotConnectedError: If the camera is not connected when attempting
                                     to configure settings.
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"Cannot configure settings for {self} as it is not connected.")

        # 1) Set FPS if specified
        if self.fps is None:
            self.fps = self.videocapture.get(cv2.CAP_PROP_FPS)
        else:
            self._validate_fps()

        # 2) Determine raw resolution to request based on final (post-rotation) config
        #    width/height in config represent the final dimensions after any rotation
        #    so swap for raw request if rotating by 90 or 270 degrees
        if self.rotation in (cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE):
            raw_width, raw_height = self.capture_height, self.capture_width
        else:
            raw_width, raw_height = self.capture_width, self.capture_height

        # 3) Apply raw width/height settings to the VideoCapture
        self.videocapture.set(cv2.CAP_PROP_FRAME_WIDTH, raw_width)
        self.videocapture.set(cv2.CAP_PROP_FRAME_HEIGHT, raw_height)

        # 4) Verify camera applied settings
        actual_raw_w = int(round(self.videocapture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        actual_raw_h = int(round(self.videocapture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        width_success = (actual_raw_w == raw_width)
        height_success = (actual_raw_h == raw_height)
        if not width_success or not height_success:
            raise RuntimeError(
                f"{self} failed to set raw resolution "
                f"({raw_width}x{raw_height}), actual is {actual_raw_w}x{actual_raw_h}."
            )
        logger.info(f"{self} raw resolution set to {actual_raw_w}x{actual_raw_h}")

        # 5) Assign final capture dimensions for post-processing
        #    These remain as originally configured (width, height)
        self.capture_width = self.capture_width
        self.capture_height = self.capture_height

        # 6) Any additional behavior (e.g. cropping) will use capture_width/height


    """
    def _configure_capture_settings(self) -> None:
        """"""
        Applies the specified FPS, width, and height settings to the connected camera.

        This method attempts to set the camera properties via OpenCV. It checks if
        the camera successfully applied the settings and raises an error if not.

        Args:
            fps: The desired frames per second. If None, the setting is skipped.
            width: The desired capture width. If None, the setting is skipped.
            height: The desired capture height. If None, the setting is skipped.

        Raises:
            RuntimeError: If the camera fails to set any of the specified properties
                          to the requested value.
            DeviceNotConnectedError: If the camera is not connected when attempting
                                     to configure settings.
        """"""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"Cannot configure settings for {self} as it is not connected.")

        if self.fps is None:
            self.fps = self.videocapture.get(cv2.CAP_PROP_FPS)
        else:
            self._validate_fps()

        default_width = int(round(self.videocapture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        default_height = int(round(self.videocapture.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        if self.width is None or self.height is None:
            self.width, self.height = default_width, default_height
            self.capture_width, self.capture_height = default_width, default_height
            if self.rotation in [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE]:
                self.width, self.height = default_height, default_width
                self.capture_width, self.capture_height = default_width, default_height
        else:
            self._validate_width_and_height()
    """
    def _validate_fps(self) -> None:
        """Validates and sets the camera's frames per second (FPS)."""

        success = self.videocapture.set(cv2.CAP_PROP_FPS, float(self.fps))
        actual_fps = self.videocapture.get(cv2.CAP_PROP_FPS)
        # Use math.isclose for robust float comparison
        if not success or not math.isclose(self.fps, actual_fps, rel_tol=1e-3):
            raise RuntimeError(f"{self} failed to set fps={self.fps} ({actual_fps=}).")

    def _validate_width_and_height(self) -> None:
        """Validates and sets the camera's frame capture width and height."""

        width_success = self.videocapture.set(cv2.CAP_PROP_FRAME_WIDTH, float(self.capture_width))
        height_success = self.videocapture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self.capture_height))

        actual_width = int(round(self.videocapture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        if not width_success or self.capture_width != actual_width:
            raise RuntimeError(
                f"{self} failed to set capture_width={self.capture_width} ({actual_width=}, {width_success=})."
            )

        actual_height = int(round(self.videocapture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        if not height_success or self.capture_height != actual_height:
            raise RuntimeError(
                f"{self} failed to set capture_height={self.capture_height} ({actual_height=}, {height_success=})."
            )

    @staticmethod
    def find_cameras() -> list[dict[str, Any]]:
        """
        Detects available OpenCV cameras connected to the system.

        On Linux, it scans '/dev/video*' paths. On other systems (like macOS, Windows),
        it checks indices from 0 up to `MAX_OPENCV_INDEX`.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries,
            where each dictionary contains 'type', 'id' (port index or path),
            and the default profile properties (width, height, fps, format).
        """
        found_cameras_info = []

        if platform.system() == "Linux":
            possible_paths = sorted(Path("/dev").glob("video*"), key=lambda p: p.name)
            targets_to_scan = [str(p) for p in possible_paths]
        else:
            targets_to_scan = list(range(MAX_OPENCV_INDEX))

        for target in targets_to_scan:
            camera = cv2.VideoCapture(target)
            if camera.isOpened():
                default_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                default_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                default_fps = camera.get(cv2.CAP_PROP_FPS)
                default_format = camera.get(cv2.CAP_PROP_FORMAT)
                camera_info = {
                    "name": f"OpenCV Camera @ {target}",
                    "type": "OpenCV",
                    "id": target,
                    "backend_api": camera.getBackendName(),
                    "default_stream_profile": {
                        "format": default_format,
                        "width": default_width,
                        "height": default_height,
                        "fps": default_fps,
                    },
                }

                found_cameras_info.append(camera_info)
                camera.release()

        return found_cameras_info

    def read(self, color_mode: ColorMode | None = None) -> np.ndarray:
        """
        Reads a single frame synchronously from the camera.

        This is a blocking call. It waits for the next available frame from the
        camera hardware via OpenCV.

        Args:
            color_mode (Optional[ColorMode]): If specified, overrides the default
                color mode (`self.color_mode`) for this read operation (e.g.,
                request RGB even if default is BGR).

        Returns:
            np.ndarray: The captured frame as a NumPy array in the format
                       (height, width, channels), using the specified or default
                       color mode and applying any configured rotation.

        Raises:
            DeviceNotConnectedError: If the camera is not connected.
            RuntimeError: If reading the frame from the camera fails or if the
                          received frame dimensions don't match expectations before rotation.
            ValueError: If an invalid `color_mode` is requested.
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        start_time = time.perf_counter()

        ret, frame = self.videocapture.read()

        if not ret or frame is None:
            raise RuntimeError(f"{self} read failed (status={ret}).")

        processed_frame = self._postprocess_image(frame, color_mode)

        read_duration_ms = (time.perf_counter() - start_time) * 1e3
        logger.debug(f"{self} read took: {read_duration_ms:.1f}ms")

        return processed_frame

    def _postprocess_image(self, image: np.ndarray, color_mode: ColorMode | None = None) -> np.ndarray:
        """
        Applies rotation, cropping, dimension validation and color conversion to a raw frame.

        Args:
            image (np.ndarray): The raw BGR image from OpenCV.
            color_mode (Optional[ColorMode]): If provided, overrides self.color_mode.

        Returns:
            np.ndarray: Processed frame of shape (capture_height, capture_width, 3).

        Raises:
            ValueError: Bad color_mode.
            RuntimeError: If final dimensions or channels mismatch.
        """
        # 1) Color mode determination
        requested_color_mode = self.color_mode if color_mode is None else color_mode
        if requested_color_mode not in (ColorMode.RGB, ColorMode.BGR):
            raise ValueError(f"Invalid color mode '{requested_color_mode}'.")

        # 2) Rotate first
        if self.rotation is not None:
            image = cv2.rotate(image, self.rotation)

        # 3) Crop center if too large
        target_h, target_w = self.capture_height, self.capture_width
        h, w = image.shape[:2]
        if w > target_w or h > target_h:
            x0 = (w - target_w) // 2
            y0 = (h - target_h) // 2
            image = image[y0:y0+target_h, x0:x0+target_w]

        # 4) Validate dimensions and channels
        h, w, c = image.shape
        if (h, w) != (target_h, target_w):
            raise RuntimeError(f"{self} frame is {w}x{h}, but expected {target_w}x{target_h}.")
        if c != 3:
            raise RuntimeError(f"{self} frame channels={c}, expected 3.")

        # 5) Convert to RGB if needed
        if requested_color_mode == ColorMode.RGB:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        return image

    def _read_loop(self):
        """
        Internal loop run by the background thread for asynchronous reading.

        On each iteration:
        1. Reads a color frame
        2. Stores result in latest_frame (thread-safe)
        3. Sets new_frame_event to notify listeners

        Stops on DeviceNotConnectedError, logs other errors and continues.
        """
        while not self.stop_event.is_set():
            try:
                color_image = self.read()

                with self.frame_lock:
                    self.latest_frame = color_image
                self.new_frame_event.set()

            except DeviceNotConnectedError:
                break
            except Exception as e:
                logger.warning(f"Error reading frame in background thread for {self}: {e}")

    def _start_read_thread(self) -> None:
        """Starts or restarts the background read thread if it's not running."""
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=0.1)
        if self.stop_event is not None:
            self.stop_event.set()

        self.stop_event = Event()
        self.thread = Thread(target=self._read_loop, args=(), name=f"{self}_read_loop")
        self.thread.daemon = True
        self.thread.start()

    def _stop_read_thread(self) -> None:
        """Signals the background read thread to stop and waits for it to join."""
        if self.stop_event is not None:
            self.stop_event.set()

        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        self.thread = None
        self.stop_event = None

    def async_read(self, timeout_ms: float = 200) -> np.ndarray:
        """
        Reads the latest available frame asynchronously.

        This method retrieves the most recent frame captured by the background
        read thread. It does not block waiting for the camera hardware directly,
        but may wait up to timeout_ms for the background thread to provide a frame.

        Args:
            timeout_ms (float): Maximum time in milliseconds to wait for a frame
                to become available. Defaults to 200ms (0.2 seconds).

        Returns:
            np.ndarray: The latest captured frame as a NumPy array in the format
                       (height, width, channels), processed according to configuration.

        Raises:
            DeviceNotConnectedError: If the camera is not connected.
            TimeoutError: If no frame becomes available within the specified timeout.
            RuntimeError: If an unexpected error occurs.
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        if self.thread is None or not self.thread.is_alive():
            self._start_read_thread()

        if not self.new_frame_event.wait(timeout=timeout_ms / 1000.0):
            thread_alive = self.thread is not None and self.thread.is_alive()
            raise TimeoutError(
                f"Timed out waiting for frame from camera {self} after {timeout_ms} ms. "
                f"Read thread alive: {thread_alive}."
            )

        with self.frame_lock:
            frame = self.latest_frame
            self.new_frame_event.clear()

        if frame is None:
            raise RuntimeError(f"Internal error: Event set but no frame available for {self}.")

        return frame

    def disconnect(self):
        """
        Disconnects from the camera and cleans up resources.

        Stops the background read thread (if running) and releases the OpenCV
        VideoCapture object.

        Raises:
            DeviceNotConnectedError: If the camera is already disconnected.
        """
        if not self.is_connected and self.thread is None:
            raise DeviceNotConnectedError(f"{self} not connected.")

        if self.thread is not None:
            self._stop_read_thread()

        if self.videocapture is not None:
            self.videocapture.release()
            self.videocapture = None

        logger.info(f"{self} disconnected.")
