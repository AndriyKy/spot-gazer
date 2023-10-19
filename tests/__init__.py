from django.test import TestCase

from livemap.models import City, Country, Address, ParkingLot, VideoStreamSource


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
