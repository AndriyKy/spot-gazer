import asyncio
import time
from typing import Any, Generator, NoReturn

import cv2
from pendulum import now
from ultralytics import YOLO
from ultralytics.yolo.engine.results import Results
from ultralytics.yolo.utils import SETTINGS

from configs.settings import TIME_ZONE, YOLOv8_PREDICTION_PARAMETERS
from utils import create_mask, logging, retrieve_the_latest_frame

SETTINGS.update({"sync": False})  # Prevent sync analytics and crashes with HUB (Google Analytics)
logger = logging.getLogger(__name__)


class SpotGazer:
    """Detect parking spot occupancy in concurrent mode.

    Args:
        - parking_lots: list of all video sources. Dictionary fields:
            - parking_lot_id: int
            - stream_source: str
            - processing_rate: int
            - parking_zone: Optional[list[int]]
    """

    model = YOLO("yolov8m_spot_gazer.pt")

    def __init__(self, parking_lots: list[list[dict[str, Any]]]) -> None:
        self.parking_lots = parking_lots
        self._gathered_tasks = asyncio.gather(
            *(self._detect_the_parking_lot_occupancy(parking_lot) for parking_lot in self.parking_lots),
            return_exceptions=True,
        )

    async def start_detection(self) -> None:
        """Start separate asynchronous tasks for each parking lot. One parking lot can have several camera streams"""
        logger.info(f"Occupancy detection of {len(self.parking_lots)} parking lots has been started!")
        self._gathered_tasks = await self._gathered_tasks

    def stop_detection(self) -> None:
        (task.cancel() for task in self._gathered_tasks)
        logger.info("Detection stopped!")

    async def _detect_the_parking_lot_occupancy(self, parking_lot: list[dict[str, Any]]) -> NoReturn:
        parking_lot = self._convert_array_to_mask(parking_lot)
        logger.debug(f"Determining the occupancy of parking lot №{parking_lot[0]['parking_lot_id']}")

        if len(parking_lot) == 1 and parking_lot[0]["parking_zone"] is None:
            stream = parking_lot[0]

            start_time = time.time()
            results: Generator[Results] = self.model.predict(source=stream, **YOLOv8_PREDICTION_PARAMETERS)
            print(f"\nExecution time of `model.predict` method: {time.time() - start_time}")

            for result in results:
                start_time = time.time()
                detected_cars = len(result.boxes)
                print(f"Execution time of counting of detected cars: {time.time() - start_time}")

                parking_occupancy = self._save_occupancy(stream["parking_lot_id"], detected_cars)

                # Sleep for the specified processing rate before processing the next frame
                await asyncio.sleep(stream["processing_rate"])
        else:
            # Continuously process frames from the video streams
            while True:
                print("\nBatch prediction (list of 2 frames)".upper())
                print("=" * 100)
                iteration_time_start = time.time()

                frames = []
                time_of_fetching_frames = time.time()
                for stream in parking_lot:
                    print(f"\nProcessing frame from '{stream['stream_source']}': {now(TIME_ZONE)}")

                    start_time = time.time()
                    frame = retrieve_the_latest_frame(stream["stream_source"])
                    print(f"Execution time of `retrieve_the_latest_frame` method: {time.time() - start_time}")

                    # If a mask in the `parking_zone` is defined, glue the mask with the frame
                    # Otherwise, use the original frame as is
                    start_time = time.time()
                    frame = (
                        cv2.bitwise_and(frame, parking_zone)
                        if (parking_zone := stream.get("parking_zone")) is not None
                        else frame
                    )
                    print(f"Execution time of inline `if/else` statement WITH masks: {time.time() - start_time}")
                    frames.append(frame)
                print(f"\nExecution time of fetching 2 frames WITH masks: {time.time() - time_of_fetching_frames}")

                start_time = time.time()
                results: Generator[Results] = self.model.predict(source=frames, **YOLOv8_PREDICTION_PARAMETERS)
                print(f"\nExecution time of `model.predict` method: {time.time() - start_time}")

                start_time = time.time()
                detected_cars = sum(len(result) for result in results)

                print(f"Execution time of counting of detected cars (`sum` method): {time.time() - start_time}")
                print(f"Average execution time: {time.time() - iteration_time_start}\n")

                parking_occupancy = self._save_occupancy(stream["parking_lot_id"], detected_cars)
                print(parking_occupancy)

                # Sleep for the specified processing rate before processing the next frame
                await asyncio.sleep(stream["processing_rate"])

    @staticmethod
    def _convert_array_to_mask(parking_lot: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert a parking zone coordinates to a black mask around them"""
        count = 0
        for lot in parking_lot:
            if parking_zone := lot.get("parking_zone"):
                frame = retrieve_the_latest_frame(lot["stream_source"])
                lot["parking_zone"] = create_mask(frame, parking_zone)
                count += 1
        logger.debug(
            f"Successfully converter coordinates of parking lot №{parking_lot[0]['parking_lot_id']}!"
            if count > 0
            else f"There are no coordinates for conversion at parking lot №{parking_lot[0]['parking_lot_id']}"
        )
        return parking_lot

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
        "stream_source": "test_media/parking_video_1.mp4",
        "processing_rate": 3,  # Process 1 frame every 3 seconds
        # "parking_zone": [
        #     [[[0, 222]], [[633, 222]], [[635, 330]], [[3, 329]]],
        #     [[[9, 124]], [[637, 125]], [[633, 16]], [[352, 7]], [[7, 14]]],
        # ],
        "parking_zone": None,
    }
    stream_2 = {
        "parking_lot_id": 1,
        "stream_source": "test_media/parking_video_2.mp4",
        "processing_rate": 3,
        # "parking_zone": [
        #     [[[1, 256]], [[242, 76]], [[422, 117]], [[254, 288]], [[161, 359]], [[2, 308]]],
        #     [[[469, 134]], [[636, 162]], [[610, 357]], [[466, 357]], [[327, 329]]],
        #     [[[1, 199]], [[207, 87]], [[89, 66]], [[1, 98]]],
        # ],
        "parking_zone": None,
    }
    stream_3 = {
        "parking_lot_id": 3,
        "stream_source": "https://youtu.be/mpwfjhmyEzw",
        "processing_rate": 3,
        "parking_zone": None,
    }
    video_stream_source = [[stream_3]]

    async def main() -> None:
        spot_gazer = SpotGazer(video_stream_source)

        # await spot_gazer.start_detection()
        # await asyncio.sleep(5)
        # spot_gazer.stop_detection()

        try:
            await spot_gazer.start_detection()
            await asyncio.sleep(5)
        finally:
            spot_gazer.stop_detection()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
