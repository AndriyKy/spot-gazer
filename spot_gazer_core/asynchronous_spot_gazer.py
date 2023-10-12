import asyncio
from itertools import cycle
from pathlib import Path
from typing import Any, Generator

import numpy as np
from configs.settings import TIME_ZONE, YOLOv8_PREDICTION_PARAMETERS
from pendulum import now
from torch import Tensor
from ultralytics import YOLO
from ultralytics.yolo.engine.results import Results
from ultralytics.yolo.utils import DEFAULT_CFG, SETTINGS
from ultralytics.yolo.v8.detect import DetectionPredictor
from utils import create_mask, logging

SETTINGS.update({"sync": False})  # Prevent sync analytics and crashes with Ultralytics HUB (Google Analytics)
logger = logging.getLogger(__name__)


class Interceptor(DetectionPredictor):
    def __init__(self, cfg=DEFAULT_CFG, overrides=None, _callbacks=None) -> None:
        super().__init__(cfg, overrides, _callbacks)
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
        model: str | Path = "spot_gazer_core/yolov8m_spot_gazer.pt",
        task="detect",
    ) -> None:
        super().__init__(model, task)
        # Manual predictor initialization
        self.predictor = Interceptor(overrides=self.overrides, _callbacks=self.callbacks)
        self.predictor.setup_model(model=model, verbose=False)
        # Initializing parking lots and gathering detection coroutines
        self.parking_lots = parking_lots
        self._gathered_tasks = asyncio.gather(
            *(self._detect_the_parking_lot_occupancy(parking_lot) for parking_lot in self.parking_lots),
            return_exceptions=True,
        )

    async def start_detection(self) -> None:
        """Start separate asynchronous tasks for each parking lot. One parking lot can have several camera streams"""
        logger.info(f"Occupancy detection of {len(self.parking_lots)} parking lots has been started!")
        self._gathered_tasks = await self._gathered_tasks  # type: ignore[assignment]

    def stop_detection(self) -> None:
        (task.cancel() for task in self._gathered_tasks)
        logger.info("Detection stopped!")

    async def _detect_the_parking_lot_occupancy(self, parking_lot: list[dict[str, Any]]) -> None:
        logger.info(f"Determining the occupancy of parking lot №{(stream := parking_lot[0])['parking_lot_id']}")
        stream_count = len(parking_lot)

        if stream_count == 1:
            # Set parking zone as a predictor class instance attribute which will be converted to a mask
            parking_zone = stream["parking_zone"]
            self.predictor.parking_zone = parking_zone
            results: Generator[None, None, Results] = self.predict(
                source=stream["stream_source"], **YOLOv8_PREDICTION_PARAMETERS
            )

            for result in results:
                self.predictor.parking_zone = parking_zone
                parking_occupancy = self._save_occupancy(
                    stream["parking_lot_id"],
                    len(result),  # type: ignore[arg-type]
                )
                print(parking_occupancy)

                # Sleep for the specified processing rate before processing the next frame
                await asyncio.sleep(stream["processing_rate"])
        else:
            # Continuously process frames from the video streams
            while True:
                for stream in parking_lot:
                    # Initialize predictor and run streams in the background (threads)
                    stream["prediction"] = self.predict(source=stream["stream_source"], **YOLOv8_PREDICTION_PARAMETERS)
                detected_cars = count = 0
                for stream in cycle(parking_lot):
                    self.predictor.parking_zone = stream["parking_zone"]
                    detected_cars += len(next(stream["prediction"]))
                    count += 1
                    if stream_count == count:
                        parking_occupancy = self._save_occupancy(stream["parking_lot_id"], detected_cars)
                        print(parking_occupancy)
                        detected_cars = count = 0

                        # Sleep for the specified processing rate before processing the next frame
                        await asyncio.sleep(stream["processing_rate"])

    @staticmethod
    def _save_occupancy(parking_lot_id: int, occupied_spots: int) -> dict[str, Any]:
        # TODO: save the data to the DB instead of returning
        return {
            "parking_lot_id": parking_lot_id,
            "occupied_spots": occupied_spots,
            "timestamp": now(TIME_ZONE).to_datetime_string(),
        }


if __name__ == "__main__":
    stream_1 = {
        "parking_lot_id": 1,
        "stream_source": "tests/test_media/parking_video_1.mp4",
        "processing_rate": 3,  # Process 1 frame every 3 seconds
        "parking_zone": [
            [[[0, 222]], [[633, 222]], [[635, 330]], [[3, 329]]],
            [[[9, 124]], [[637, 125]], [[633, 16]], [[352, 7]], [[7, 14]]],
        ],
        # "parking_zone": None,
    }
    stream_2 = {
        "parking_lot_id": 1,
        "stream_source": "tests/test_media/parking_video_2.mp4",
        "processing_rate": 5,
        "parking_zone": [
            [[[1, 256]], [[242, 76]], [[422, 117]], [[254, 288]], [[161, 359]], [[2, 308]]],
            [[[469, 134]], [[636, 162]], [[610, 357]], [[466, 357]], [[327, 329]]],
            [[[1, 199]], [[207, 87]], [[89, 66]], [[1, 98]]],
        ],
        # "parking_zone": None,
    }
    stream_3 = {
        "parking_lot_id": 3,
        "stream_source": "https://youtu.be/mpwfjhmyEzw",
        "processing_rate": 5,
        "parking_zone": [
            [[[46, 637]], [[544, 870]], [[1135, 1023]], [[1493, 1066]], [[1493, 838]], [[516, 689]], [[170, 576]]],
            [[[1643, 833]], [[1530, 469]], [[1611, 464]], [[1850, 879]]],
        ],
        # "parking_zone": None,
    }
    video_stream_source = [[stream_1, stream_2]]

    async def main() -> None:
        spot_gazer = SpotGazer(video_stream_source)
        try:
            await spot_gazer.start_detection()
        finally:
            spot_gazer.stop_detection()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
