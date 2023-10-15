from typing import Any
from django.forms import ValidationError
from django.test import TestCase
from parameterized import parameterized

from livemap.models import City, Country, Address, ParkingLot, VideoStreamSource, validate_geolocation

from faker import Faker

fake = Faker()


class TestCaseWithData(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # Set up data for the whole TestCase
        cls.country = Country.objects.create(country_name=fake.country())
        cls.city = City.objects.create(country=cls.country, city_name=fake.city())
        cls.address = Address.objects.create(city=cls.city, parking_lot_address=fake.street_address())
        cls.parking_lot = ParkingLot.objects.create(
            address=cls.address,
            total_spots=fake.pyint(),
            spots_for_disabled=fake.pyint(),
            is_private=fake.random_element(ParkingLot.Answer.values),
            is_free=fake.random_element(ParkingLot.Answer.values),
            geolocation=[float(fake.latitude()), float(fake.longitude())],
        )
        cls.stream_source_data = {
            "parking_lot": cls.parking_lot,
            "stream_source": "tests/test_media/parking_video_1.mp4",
            "processing_rate": fake.pyint(min_value=1, max_value=5),
            "is_active": True,
        }
        cls.stream_source = VideoStreamSource.objects.create(**cls.stream_source_data)


class ParkingLotModelTest(TestCaseWithData):
    def test_parking_lot_choices(self) -> None:
        self.assertTrue(self.parking_lot.get_is_private in ParkingLot.Answer.labels)
        self.assertTrue(self.parking_lot.get_is_free in ParkingLot.Answer.labels)

    @parameterized.expand(
        [
            (
                fake.pyfloat(),
                "The geolocation value must be a list of 2 integers or floating-point numbers!",
            ),
            (
                fake.pylist(nb_elements=fake.pyint(min_value=3, max_value=10)),
                "The geolocation value must be a list of 2 integers or floating-point numbers!",
            ),
            (
                fake.pylist(nb_elements=2, variable_nb_elements=False, value_types=[str]),
                "Both values must be either integers or floating-point numbers!",
            ),
            (
                [fake.pyfloat(max_value=-91), fake.pyfloat(max_value=-181)],
                "The latitude should be in the range [-90, 90] and the longitude should be in the range [-180, 180]",
            ),
        ]
    )
    def test_validate_geolocation(self, input: Any, error_message: str) -> None:
        with self.assertRaisesMessage(ValidationError, error_message, msg=input):
            validate_geolocation(input)


class VideoStreamSourceTest(TestCaseWithData):
    def test_clean(self) -> None:
        processing_rate = self.stream_source_data["processing_rate"]
        self.stream_source_data["processing_rate"] = fake.pyint(min_value=6)
        with self.assertRaisesMessage(
            ValidationError, f"The processing rate for this parking lot should be {processing_rate} s!"
        ):
            VideoStreamSource.objects.create(**self.stream_source_data)
