from typing import Any

from django.core.exceptions import ValidationError
from django.db import models


class Country(models.Model):
    country_name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return str(self.country_name)


class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.city_name}, {self.country}"


class Address(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    parking_lot_address = models.CharField(max_length=200)

    def __str__(self) -> str:
        return f"{self.parking_lot_address}, {self.city}"


def validate_geolocation(geolocation: Any) -> None:
    if not isinstance(geolocation, list) or len(geolocation) != 2:
        raise ValidationError("The geolocation value must be a list of 2 integers or floating-point numbers!")
    if not all([isinstance(location, (int, float)) for location in geolocation]):
        raise ValidationError("Both values must be either integers or floating-point numbers!")
    if not (-90 <= geolocation[0] <= 90) or not (-180 <= geolocation[1] <= 180):
        raise ValidationError(
            "The latitude should be in the range [-90, 90] and the longitude should be in the range [-180, 180]"
        )


class ParkingLot(models.Model):
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    geolocation = models.JSONField(
        validators=[validate_geolocation],
        help_text="Latitude and longitude of a parking lot. Ex.: [49.911848, 16.611212]",
    )
    total_spots = models.PositiveIntegerField()

    def __str__(self) -> str:
        return str(self.address)


class VideoStreamSource(models.Model):
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    stream_source = models.URLField()
    processing_rate = models.PositiveIntegerField(help_text="In seconds.")
    parking_zone = models.JSONField(
        blank=True, null=True, help_text="An array in a format [[[[int, int]], [[int, int]], ...]]."
    )

    def __str__(self) -> str:
        return f"{self.stream_source}, {self.parking_lot}"

    def clean(self) -> None:
        # Check for existing instances with the same `parking_lot`
        existing_instances = VideoStreamSource.objects.filter(parking_lot=self.parking_lot)

        for instance in existing_instances:
            if instance.parking_lot == self.parking_lot and instance.processing_rate != self.processing_rate:
                raise ValidationError(
                    f"The processing rate for this parking lot should be {instance.processing_rate} s!"
                )

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)


class Occupancy(models.Model):
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    occupied_spots = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.occupied_spots} occupied spots, {self.parking_lot}"
