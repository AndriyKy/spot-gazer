import os
from asyncio import run
from typing import Any
from spot_gazer_core import SpotGazer

import django
from django.core.wsgi import get_wsgi_application

django.setup()

from livemap.models import VideoStreamSource  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_core.settings")
application = get_wsgi_application()


def stream_sources() -> list[list[dict[str, Any]]]:
    stream_sources_list = list(
        VideoStreamSource.objects.filter(is_active=True).values(
            "parking_lot_id", "stream_source", "processing_rate", "parking_zone"
        )
    )
    # Group video streams sources of the same parking lot.
    grouped_stream_sources: dict[int, list[dict[str, Any]]] = {}
    for stream in stream_sources_list:
        if grouped_stream_sources.get((parking_lot_id := stream["parking_lot_id"])):
            grouped_stream_sources[parking_lot_id].append(stream)
        else:
            grouped_stream_sources[parking_lot_id] = [stream]
    return list(grouped_stream_sources.values())


async def run_spot_gazer(stream_sources_list: list[list[dict[str, Any]]]) -> None:
    spot_gazer = SpotGazer(stream_sources_list)
    try:
        await spot_gazer.start_detection()
    finally:
        spot_gazer.stop_detection()


try:
    # Run Django server in the background
    os.system("screen -dmSL django_session python3 ./manage.py runserver")

    # Select all stream sources from the database and run Stop Gazer
    stream_sources_list = stream_sources()
    run(run_spot_gazer(stream_sources_list))
except KeyboardInterrupt:
    pass
finally:
    # Terminate the background Django session
    os.system("screen -XS django_session quit")
