import unittest


def _library(test_case):
    try:
        import ina229_ft232h
    except ModuleNotFoundError:
        test_case.fail("ina229_ft232h package has not been implemented")
    return ina229_ft232h


class MemorySPI:
    def __init__(self):
        self.registers = {}
        self.last_transfer = None
        self.locked = False

    def try_lock(self):
        self.locked = True
        return True

    def unlock(self):
        self.locked = False

    def write_readinto(self, output, received):
        self.last_transfer = bytes(output)
        register = output[0] >> 2
        if output[0] & 1:
            value = self.registers.get(register, 0)
            byte_count = len(output) - 1
            data = value.to_bytes(byte_count, "big")
            received[0] = 0
            received[1:] = data
            return

        value = int.from_bytes(output[1:], "big")
        if register == 0 and value & 0x8000:
            value = 0
        self.registers[register] = value


class DriverTests(unittest.TestCase):
    def test_calibration_uses_shunt_and_expected_maximum_current(self):
        ina229 = _library(self)
        spi = MemorySPI()

        device = ina229.INA229(spi, shunt_ohms=0.01, max_current=8.0)

        self.assertAlmostEqual(device.current_lsb, 8.0 / (1 << 19))
        self.assertEqual(spi.registers[ina229.SHUNT_CAL], 2000)

    def test_measurements_are_scaled_to_si_units(self):
        ina229 = _library(self)
        spi = MemorySPI()
        device = ina229.INA229(spi, shunt_ohms=0.01, max_current=8.0)
        spi.registers.update(
            {
                ina229.VBUS: 25000 << 4,
                ina229.VSHUNT: 3200 << 4,
                ina229.CURRENT: 1000 << 4,
                ina229.POWER: 2000,
                ina229.ENERGY: 3000,
                ina229.CHARGE: 4000,
                ina229.DIETEMP: 3200,
            }
        )

        self.assertAlmostEqual(device.bus_voltage, 4.8828125)
        self.assertAlmostEqual(device.shunt_voltage, 0.001)
        self.assertAlmostEqual(device.current, 1000 * device.current_lsb)
        self.assertAlmostEqual(device.power, 2000 * 3.2 * device.current_lsb)
        self.assertAlmostEqual(device.energy, 3000 * 16 * 3.2 * device.current_lsb)
        self.assertAlmostEqual(device.charge, 4000 * device.current_lsb)
        self.assertAlmostEqual(device.temperature, 25.0)

    def test_read_register_uses_one_full_duplex_spi_frame(self):
        ina229 = _library(self)
        spi = MemorySPI()
        device = ina229.INA229(spi, shunt_ohms=0.01, max_current=2.0)
        spi.registers[ina229.MANUFACTURER_ID] = 0x5449

        value = device.read_register(ina229.MANUFACTURER_ID)

        self.assertEqual(value, 0x5449)
        self.assertEqual(
            spi.last_transfer,
            bytes([(ina229.MANUFACTURER_ID << 2) | 1, 0, 0]),
        )

    def test_rejects_calibration_that_does_not_fit_register(self):
        ina229 = _library(self)
        spi = MemorySPI()

        with self.assertRaisesRegex(ValueError, "SHUNT_CAL"):
            ina229.INA229(spi, shunt_ohms=10.0, max_current=100.0)


if __name__ == "__main__":
    unittest.main()
