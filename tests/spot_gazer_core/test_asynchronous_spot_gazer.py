import asyncio
from unittest.mock import patch

from livemap.models import Occupancy, VideoStreamSource
from spot_gazer_core import SpotGazer
from run import select_grouped_stream_sources
from .. import TestCaseWithData, fake


async def _detect_the_parking_lot_occupancy_patch(*args) -> None:
    await asyncio.sleep(1)


class SpotGazerTest(TestCaseWithData):
    def setUp(self) -> None:
        super().setUp()
        self.stream_sources = select_grouped_stream_sources()
        self.parking_lot_with_broken_url = VideoStreamSource.objects.create(
            parking_lot=self.parking_lot,
            stream_source=fake.url(),
            processing_rate=self.small_parking_lot.processing_rate,
            is_active=True,
        )

    @patch.object(SpotGazer, "_detect_the_parking_lot_occupancy", _detect_the_parking_lot_occupancy_patch)
    async def test_start_stop_detection(self) -> None:
        spot_gazer = SpotGazer(self.stream_sources)
        await spot_gazer.start_detection()
        spot_gazer.stop_detection()

    async def test__detect_the_parking_lot_occupancy(self) -> None:
        await SpotGazer(self.stream_sources)._detect_the_parking_lot_occupancy(
            [self.parking_lot_with_broken_url.__dict__]
        )
        self.assertFalse(
            (
                await VideoStreamSource.objects.aget(stream_source=self.parking_lot_with_broken_url.stream_source)
            ).is_active
        )

        OCCUPIED_SPOTS_IN_A_SMALL_PARKING_LOT = 33
        await SpotGazer(self.stream_sources)._detect_the_parking_lot_occupancy([self.stream_sources[0][0]])
        self.assertEqual((await Occupancy.objects.alast()).occupied_spots, OCCUPIED_SPOTS_IN_A_SMALL_PARKING_LOT)
        self.assertFalse(
            (await VideoStreamSource.objects.aget(stream_source=self.small_parking_lot.stream_source)).is_active
        )

        OCCUPIED_SPOTS_IN_A_BIG_PARKING_LOT = 147
        await SpotGazer(self.stream_sources)._detect_the_parking_lot_occupancy(self.stream_sources[0])
        self.assertEqual((await Occupancy.objects.alast()).occupied_spots, OCCUPIED_SPOTS_IN_A_BIG_PARKING_LOT)
        self.assertFalse(
            (await VideoStreamSource.objects.aget(stream_source=self.big_parking_lot.stream_source)).is_active
        )
