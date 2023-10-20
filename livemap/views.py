from functools import lru_cache

import folium
import requests  # type: ignore[import]
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render

from livemap.models import ParkingLot


@lru_cache()
def _extract_client_ip_address(request: WSGIRequest) -> str | None:
    req_headers = request.META
    if x_forwarded_for_value := req_headers.get("HTTP_X_FORWARDED_FOR"):
        ip_addr = x_forwarded_for_value.split(",")[0].strip()
    else:
        ip_addr = req_headers.get("REMOTE_ADDR")
    return ip_addr


@lru_cache()
def _fetch_geolocation(ip_address: str) -> tuple[float, float] | None:
    response = requests.get(f"https://ipinfo.io/{ip_address}/json")

    if response.status_code == 200:
        data = response.json()
        location = data.get("loc", "").split(",")
        if len(location) == 2:
            latitude, longitude = location
            return float(latitude), float(longitude)
    return None


def _compose_html_table(parking: ParkingLot) -> str:
    parking_popup = {
        "Address": "<a href='https://www.google.com/maps/search/?api=1&query="
        f"{parking.geolocation[0]},{parking.geolocation[1]}'>{parking.address}</a>",
        "Private": parking.get_is_private,
        "Free": parking.get_is_free,
        "Total spots": parking.total_spots,
        "Spots for disables": spots_for_disabled if (spots_for_disabled := parking.spots_for_disabled) else "",
        "Free spots": parking.total_spots - parking.occupancies.latest().occupied_spots
        if parking.occupancies.exists()
        else "",
    }
    lives = "- Live "
    for stream_source in parking.stream_sources.filter(parking_lot_id=parking.id):
        lives += f"<a href='{stream_source.stream_source}'> 🔴 </a>"

    html_table = f"""
    <table class="styled-table" style="width:100%">
        <thead>
            <tr>
                <th colspan="2">
                    Parking details {lives}
                </th>
            </tr>
        </thead>
    """
    for field, value in parking_popup.items():
        html_table += f"""
        <tr>
            <td>{field}</td>
            <td>{value}</td>
        </tr>
        """
    html_table += """
    </table>
    """
    return html_table


def index(request: WSGIRequest) -> HttpResponse:
    parkings = ParkingLot.objects.select_related("address", "address__city", "address__city__country").prefetch_related(
        "occupancies", "stream_sources"
    )
    client_ip_address = _extract_client_ip_address(request)
    geolocation = _fetch_geolocation(client_ip_address) if client_ip_address else None
    folium_map = folium.Map(geolocation)

    for parking in parkings:
        popup = _compose_html_table(parking)
        folium.Marker(parking.geolocation, folium.Popup(popup)).add_to(folium_map)

    return render(request, "index.html", {"map": folium_map.get_root().render()})
