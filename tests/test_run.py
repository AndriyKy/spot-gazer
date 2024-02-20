from . import TestCaseWithData
from run import select_grouped_stream_sources


class RunTest(TestCaseWithData):
    def test_select_grouped_stream_sources(self) -> None:
        stream_sources = select_grouped_stream_sources()
        self.assertIsInstance(stream_sources, list)
        self.assertIsInstance(stream_sources[0], list)
        self.assertIsInstance(stream_sources[0][0], dict)
