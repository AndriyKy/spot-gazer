import cv2
import numpy as np


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
