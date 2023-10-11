import folium
from django.http import HttpResponse
from django.shortcuts import render
from django.core.handlers.wsgi import WSGIRequest

from livemap.models import ParkingLot


def _compose_html_table(parking: ParkingLot) -> folium.Popup:
    last_occupancy_record = parking.occupancies.last()
    parking_popup = {
        "Address": parking.address,
        "Private": parking.get_is_private,
        "Free": parking.get_is_free,
        "Total spots": parking.total_spots,
        "Spots for disables": spots_for_disabled if (spots_for_disabled := parking.spots_for_disabled) else "",
        "Free spots": parking.total_spots - last_occupancy_record.occupied_spots if last_occupancy_record else "",
    }
    table_html = """
    <table class="styled-table" style="width:100%">
        <thead>
            <tr>
                <th colspan="2">Parking details</th>
            </tr>
        </thead>
    """
    for field, value in parking_popup.items():
        table_html += f"""
        <tr>
            <td>{field}</td>
            <td>{value}</td>
        </tr>
        """
    table_html += """
    </table>
    """
    return folium.Popup(table_html, max_width=400)


def index(request: WSGIRequest) -> HttpResponse:
    parkings = ParkingLot.objects.all()
    folium_map = folium.Map()

    for parking in parkings:
        popup = _compose_html_table(parking)
        folium.Marker(parking.geolocation, popup).add_to(folium_map)

    return render(request, "index.html", {"map": folium_map.get_root().render()})
