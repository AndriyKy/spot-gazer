from os.path import join as join_path

import cv2
import numpy as np
from ultralytics.yolo.data import load_inference_source

from .tools import parse_time


def create_mask(frame: np.ndarray, figure_coords: list[list], mask_only: bool = True) -> np.ndarray:
    """
    The method creates a black mask around the figure whose coordinates were passed.

    If the parameter `mask_only` is False, the method returns the mask glued with an image.
    """
    mask = np.zeros_like(frame)

    arrays = []
    for coord in figure_coords:
        arrays.append(np.array(coord, np.int32))
    cv2.fillPoly(mask, pts=arrays, color=(255, 255, 255))

    if mask_only:
        return mask
    return cv2.bitwise_and(frame, mask)  # Glue the mask and the original image


def retrieve_frame_by_time(video_path: str, target_time: tuple[int, int, int], image_name: str) -> None:
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


def retrieve_frame_from_stream(source: str, image_name_to_save: str | None = None) -> np.ndarray:
    """Retrieve the latest frame from the video stream

    If the `image name_to_save` parameter is defined, a frame will be saved to the `images_for_markup` folder
    """
    for batch in load_inference_source(source):
        _, frame, _, _ = batch
        if image_name_to_save:
            cv2.imwrite(join_path("images_for_markup", f"{image_name_to_save}.jpg"), frame[0])
        return frame


if __name__ == "__main__":
    # retrieve_frame_by_time("test_media/parking_video_1.mp4", (0, 0, 5), "v3")
    # retrieve_frame_from_stream("test_media/parking_video_1.mp4", "parking_video_1")
    retrieve_frame_from_stream(
        "https://www.youtube.com/watch?v=mpwfjhmyEzw&ab_channel=NordicTelecomLan%C5%A1kroun",
        "YouType_stream",
    )
