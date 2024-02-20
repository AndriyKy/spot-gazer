from http import HTTPStatus

from django.test import TestCase
from django.core.handlers.wsgi import WSGIRequest
from io import StringIO
from parameterized import parameterized
from django.urls import reverse

from livemap.views import _fetch_geolocation, _extract_client_ip_address, _compose_html_table

from .. import TestCaseWithData, fake


class HelperFunctionsTest(TestCase):
    def test__extract_client_ip_address(self) -> None:
        fake_ip = fake.ipv4()
        meta = {"REMOTE_ADDR": fake_ip, "REQUEST_METHOD": "GET", "wsgi.input": StringIO()}
        ip_by_remote_addr = _extract_client_ip_address(WSGIRequest(meta))
        self.assertEqual(ip_by_remote_addr, fake_ip)

        ip_by_http_x_forwarded = _extract_client_ip_address(WSGIRequest(meta | {"HTTP_X_FORWARDED_FOR": fake_ip}))
        self.assertEqual(ip_by_http_x_forwarded, fake_ip)

    @parameterized.expand([(fake.pystr(), type(None)), (fake.ipv4(), tuple)])
    def test__fetch_geolocation(self, ip_address: str, return_type: type(None) | tuple) -> None:
        self.assertIsInstance(_fetch_geolocation(ip_address), return_type)


class ViewsTest(TestCaseWithData):
    def test__compose_html_table(self) -> None:
        html_table = _compose_html_table(self.parking_lot)
        for field in {"Address", "Private", "Free", "Total spots", "Spots for disables", "Free spots"}:
            self.assertIn(field, html_table)
        self.assertIn(
            "<a href='https://www.google.com/maps/search/?api=1&query="
            f"{self.parking_lot.geolocation[0]},{self.parking_lot.geolocation[1]}'>{self.parking_lot.address}</a>",
            html_table,
        )
        for stream_source in self.parking_lot.stream_sources.filter(parking_lot_id=self.parking_lot.pk):
            self.assertIn(stream_source.stream_source, html_table)

    def test_index(self) -> None:
        response = self.client.get(reverse("livemap:index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
