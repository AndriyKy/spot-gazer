from django.contrib import admin

from livemap.models import Address, City, Country, Occupancy, ParkingLot, VideoStreamSource

admin.site.register(Country)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("city_name", "country")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("parking_lot_address", "city")


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ("geolocation", "total_spots", "address")


@admin.register(VideoStreamSource)
class VideoStreamSourceAdmin(admin.ModelAdmin):
    list_display = ("id", "stream_source", "is_active", "processing_rate", "parking_lot")


@admin.register(Occupancy)
class OccupancyAdmin(admin.ModelAdmin):
    def time_seconds(self, occupancy: Occupancy) -> str:
        return occupancy.timestamp.strftime("%d.%m.%Y %X")

    time_seconds.admin_order_field = "timestamp"  # type: ignore[attr-defined]
    time_seconds.short_description = "Timestamp"  # type: ignore[attr-defined]

    list_display = ("occupied_spots", "time_seconds", "parking_lot")
