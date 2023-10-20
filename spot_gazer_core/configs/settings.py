CONFIDENCE = 0.1  # Confidence threshold.
IOU = 0.7  # IoU threshold.

# The classes on the basis of which the dataset was collected.
CLASS_CAR = 0
CLASS_FREE = 1
YOLOv8_PREDICTION_PARAMETERS = {
    "save": False,
    "single_cls": False,
    "model": "spot_gazer_core/yolov8m_spot_gazer.pt",
    "data": "/content/datasets/parking_dataset/data.yaml",
    "task": "detect",
    "half": True,
    "conf": CONFIDENCE,
    "iou": IOU,
    "imgsz": 640,
    "show_labels": False,
    "classes": CLASS_CAR,
    "boxes": False,
    "verbose": False,
    "vid_stride": 10,
}

# Set separate global logging level for console and file.
# Supported values: DEBUG, INFO, WARNING, ERROR, CRITICAL.
CONSOLE_LOG_LEVEL = "DEBUG"
FILE_LOG_LEVEL = "WARNING"
