import sys
import types
import unittest
from unittest import mock


def _library(test_case):
    try:
        import ina229_ft232h
    except ModuleNotFoundError:
        test_case.fail("ina229_ft232h package has not been implemented")
    return ina229_ft232h


class FakePort:
    def __init__(self):
        self.mode = None

    def set_mode(self, mode):
        self.mode = mode


class FakeSPI:
    def __init__(self, clock, mosi, miso):
        self.pins = (clock, mosi, miso)
        self._spi = types.SimpleNamespace(_port=FakePort())
        self.configuration = None

    def try_lock(self):
        return True

    def configure(self, **kwargs):
        self.configuration = kwargs

    def unlock(self):
        pass


class Ft232hTests(unittest.TestCase):
    def test_ft232h_helper_defaults_to_working_mode_two(self):
        ina229 = _library(self)
        board = types.SimpleNamespace(SCK="sck", MOSI="mosi", MISO="miso")
        busio = types.SimpleNamespace(SPI=FakeSPI)

        with mock.patch.dict(sys.modules, {"board": board, "busio": busio}):
            spi = ina229.ft232h_spi()

        self.assertEqual(
            spi.configuration,
            {"baudrate": 1_000_000, "polarity": 0, "phase": 0},
        )
        self.assertEqual(spi._spi._port.mode, 2)


if __name__ == "__main__":
    unittest.main()
