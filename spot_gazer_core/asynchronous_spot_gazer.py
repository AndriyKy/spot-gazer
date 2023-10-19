import asyncio
from pathlib import Path
from typing import Any, Generator

import numpy as np
from .settings import YOLOv8_PREDICTION_PARAMETERS
from torch import Tensor
from ultralytics import YOLO
from ultralytics.yolo.engine.results import Results
from ultralytics.yolo.utils import SETTINGS, callbacks
from ultralytics.yolo.v8.detect import DetectionPredictor
from .utils import create_mask, logging
import django

django.setup()

from livemap.models import Occupancy, VideoStreamSource  # noqa: E402

SETTINGS.update({"sync": False})  # Prevent sync analytics and crashes with Ultralytics HUB (Google Analytics)
logger = logging.getLogger(__name__)


class Interceptor(DetectionPredictor):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.parking_zone: Any | None = None

    def preprocess(self, image: Tensor | list[np.ndarray]) -> Tensor:
        if not isinstance(image, Tensor) and self.parking_zone:
            image[0] = create_mask(image[0], self.parking_zone, False)
        self.parking_zone = None
        return super().preprocess(image)


class SpotGazer(YOLO):
    """Detect parking spot occupancy in concurrent mode.

    Args:
        - parking_lots: dictionary list of all video sources. Dictionary fields:
            - parking_lot_id: int
            - stream_source: str
            - processing_rate: int
            - parking_zone: Optional[list[list[list[list[int]]]]]
    """

    def __init__(
        self,
        parking_lots: list[list[dict[str, Any]]],
        model: str | Path = YOLOv8_PREDICTION_PARAMETERS["model"],  # type: ignore[assignment]
        task=YOLOv8_PREDICTION_PARAMETERS["task"],
    ) -> None:
        super().__init__(model, task)
        # Manual predictor initialization
        self.overrides = YOLOv8_PREDICTION_PARAMETERS
        self.predictor = Interceptor(overrides=self.overrides, _callbacks=callbacks.get_default_callbacks())
        self.predictor.setup_model(model=model, verbose=False)
        # Initializing parking lots and gathering detection coroutines
        self.parking_lots = parking_lots
        self._gathered_tasks = []

    async def start_detection(self) -> None:
        """Start separate asynchronous tasks for each parking lot. One parking lot can have several camera streams"""
        logger.info(f"Occupancy detection of {len(self.parking_lots)} parking lots has been started!")
        self._gathered_tasks = await asyncio.gather(
            *(self._detect_the_parking_lot_occupancy(parking_lot) for parking_lot in self.parking_lots),
        )

    def stop_detection(self) -> None:
        (task.cancel() for task in self._gathered_tasks)
        logger.info("Detection stopped!")

    async def _detect_the_parking_lot_occupancy(self, parking_lot: list[dict[str, Any]]) -> None:
        logger.info(f"Determining the occupancy of parking lot №{(stream := parking_lot[0])['parking_lot_id']}")

        if len(parking_lot) == 1:
            # Set parking zone as a predictor class instance attribute which will be converted to a mask
            parking_zone = stream["parking_zone"]
            self.predictor.parking_zone = parking_zone
            results: Generator[None, None, Results] = self.predict(
                source=stream["stream_source"], stream=True, **YOLOv8_PREDICTION_PARAMETERS
            )

            try:
                for result in results:
                    self.predictor.parking_zone = parking_zone
                    await self._save_occupancy(stream["parking_lot_id"], len(result))  # type: ignore[arg-type]

                    # Sleep for the specified processing rate before processing the next frame
                    await asyncio.sleep(stream["processing_rate"])
            except ConnectionError:
                pass
            await VideoStreamSource.objects.filter(parking_lot_id=stream["parking_lot_id"]).aupdate(is_active=False)
            logger.warning(f"Parking lot {stream['parking_lot_id']} is not active anymore.")
        else:
            for stream in parking_lot:
                # Initialize predictor
                stream["prediction"] = self.predict(
                    source=stream["stream_source"], stream=True, **YOLOv8_PREDICTION_PARAMETERS
                )

            # Continuously process frames from the video streams
            while True:
                detected_cars = count = 0
                stream_count = len(parking_lot)
                for stream in parking_lot:
                    self.predictor.parking_zone = stream["parking_zone"]
                    try:
                        detected_cars += len(next(stream["prediction"]))
                    except (StopIteration, ConnectionError):
                        await VideoStreamSource.objects.filter(parking_lot_id=stream["parking_lot_id"]).aupdate(
                            is_active=False
                        )
                        parking_lot.remove(stream)
                        logger.warning(f"Parking lot {stream['parking_lot_id']} is not active anymore.")
                        break
                    count += 1
                    if stream_count == count:
                        await self._save_occupancy(stream["parking_lot_id"], detected_cars)
                        detected_cars = count = 0

                        # Sleep for the specified processing rate before processing the next frame
                        await asyncio.sleep(stream["processing_rate"])
                if not stream_count:
                    break

    @staticmethod
    async def _save_occupancy(parking_lot_id: int, occupied_spots: int) -> None:
        await Occupancy.objects.acreate(parking_lot_id=parking_lot_id, occupied_spots=occupied_spots)
        logger.debug(f"Parking lot: {parking_lot_id}; occupied spots: {occupied_spots}.")
