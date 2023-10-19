from django.test import TestCase

from livemap.models import City, Country, Address, ParkingLot, VideoStreamSource


from faker import Faker

fake = Faker()


class TestCaseWithData(TestCase):
    def setUp(self) -> None:
        # Set up data for the whole TestCase
        self.country = Country.objects.create(country_name=fake.country())
        self.city = City.objects.create(country=self.country, city_name=fake.city())
        self.address = Address.objects.create(city=self.city, parking_lot_address=fake.street_address())
        self.parking_lot = ParkingLot.objects.create(
            address=self.address,
            total_spots=fake.pyint(),
            spots_for_disabled=fake.pyint(),
            is_private=fake.random_element(ParkingLot.Answer.values),
            is_free=fake.random_element(ParkingLot.Answer.values),
            geolocation=[float(fake.latitude()), float(fake.longitude())],
        )
        self.stream_source_data = {
            "parking_lot": self.parking_lot,
            "stream_source": "tests/test_media/small_parking.jpg",
            "processing_rate": fake.pyint(min_value=1, max_value=5),
            "is_active": True,
        }
        self.small_parking_lot = VideoStreamSource.objects.create(**self.stream_source_data)
        self.big_parking_lot = VideoStreamSource.objects.create(
            parking_lot=self.parking_lot,
            stream_source="tests/test_media/big_parking.jpg",
            processing_rate=self.small_parking_lot.processing_rate,
            is_active=True,
        )
