TIME_ZONE = "Europe/Kiev"

CONFIDENCE = 0.1  # confidence threshold
IOU = 0.7  # IoU threshold

# The classes on the basis of which the dataset was collected
CLASS_CAR = 0
CLASS_FREE = 1
YOLOv8_PREDICTION_PARAMETERS = {
    "stream": True,
    "conf": CONFIDENCE,
    "iou": IOU,
    "show_labels": True,
    "show_conf": True,
    "classes": CLASS_CAR,
    "boxes": False,
    "verbose": False,
}

# Set separate global logging level for console and file
# Supported values: DEBUG, INFO, WARNING, ERROR, CRITICAL
CONSOLE_LOG_LEVEL = "DEBUG"
FILE_LOG_LEVEL = "WARNING"
