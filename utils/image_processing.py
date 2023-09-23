from os.path import join as join_path

import cv2
import numpy as np

from .tools import parse_time


def extract_video_frame(video_path: str, target_time: tuple[int, int, int], image_name: str) -> None:
    """
    :param target_time: (hour, minute, second)
    """
    time_in_seconds = parse_time(*target_time)
    image_name = image_name if "." in image_name else f"{image_name}.jpg"

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    if time_in_seconds > (video_duration := frames / fps):
        print(f"The time must be within the range of {parse_time(second=int(video_duration), human_readable=True)}")
        return

    # Calculate the frame number at the target second
    target_frame = int(time_in_seconds * fps)

    # Set the video capture to the target frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    # Read the frame at the target second
    success, frame = cap.read()

    if success:
        # Save the extracted frame
        cv2.imwrite(join_path("image_for_markup", image_name), frame)
        print(f"Frame extracted at {time_in_seconds} second and saved as '{image_name}'")
    else:
        print(f"Failed to extract frame at {time_in_seconds} second")

    # Release the video capture
    cap.release()


def retrieve_the_latest_frame(source: str, image_name_to_save: str = "") -> np.ndarray:
    """Retrieve the latest frame from the video stream

    If the `image name_to_save` parameter is defined, a frame will be saved to the `image_for_markup` folder
    """
    cap = cv2.VideoCapture(source)
    _, frame = cap.read()
    cap.release()

    if image_name_to_save:
        cv2.imwrite(join_path("image_for_markup", f"{image_name_to_save}.jpg"), frame)

    return frame
