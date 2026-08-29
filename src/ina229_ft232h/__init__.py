"""INA229 driver with an FT232H-compatible SPI helper."""

import time

__version__ = "0.1.0"

# Registers
CONFIG = 0x00
ADC_CONFIG = 0x01
SHUNT_CAL = 0x02
SHUNT_TEMPCO = 0x03
VSHUNT = 0x04
VBUS = 0x05
DIETEMP = 0x06
CURRENT = 0x07
POWER = 0x08
ENERGY = 0x09
CHARGE = 0x0A
DIAG_ALRT = 0x0B
SOVL = 0x0C
SUVL = 0x0D
BOVL = 0x0E
BUVL = 0x0F
TEMP_LIMIT = 0x10
PWR_LIMIT = 0x11
MANUFACTURER_ID = 0x3E
DEVICE_ID = 0x3F

# ADC modes
MODE_SHUTDOWN = 0x0
MODE_TRIG_BUS = 0x1
MODE_TRIG_SHUNT = 0x2
MODE_TRIG_SHUNT_BUS = 0x3
MODE_TRIG_TEMP = 0x4
MODE_TRIG_TEMP_BUS = 0x5
MODE_TRIG_TEMP_SHUNT = 0x6
MODE_TRIG_ALL = 0x7
MODE_CONT_BUS = 0x9
MODE_CONT_SHUNT = 0xA
MODE_CONT_SHUNT_BUS = 0xB
MODE_CONT_TEMP = 0xC
MODE_CONT_TEMP_BUS = 0xD
MODE_CONT_TEMP_SHUNT = 0xE
MODE_CONT_ALL = 0xF

# Conversion time per channel
CT_50US, CT_84US, CT_150US, CT_280US = 0, 1, 2, 3
CT_540US, CT_1052US, CT_2074US, CT_4120US = 4, 5, 6, 7

# Averaging count
AVG_1, AVG_4, AVG_16, AVG_64 = 0, 1, 2, 3
AVG_128, AVG_256, AVG_512, AVG_1024 = 4, 5, 6, 7

_REG_BYTES = {
    ENERGY: 5,
    CHARGE: 5,
    VSHUNT: 3,
    VBUS: 3,
    CURRENT: 3,
    POWER: 3,
}
_BUS_LSB = 195.3125e-6
_TEMP_LSB = 7.8125e-3


def _signed(value, bits):
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value


class INA229:
    """Control one INA229 over an already-configured SPI bus.

    Args:
        spi: CircuitPython-compatible SPI bus, preferably from ft232h_spi.
        cs: Optional DigitalInOut chip select. Leave unset to use the FT232H
            hardware chip select on D3.
        shunt_ohms: External shunt resistance in ohms.
        max_current: Largest expected signed current magnitude in amperes.
        adc_range: False for +/-163.84 mV or True for +/-40.96 mV.
    """

    def __init__(
        self,
        spi,
        cs=None,
        shunt_ohms=0.1,
        max_current=10.0,
        adc_range=False,
    ):
        self._spi = spi
        self._cs = cs
        if cs is not None:
            cs.switch_to_output(value=True)
        self._current_lsb = 0.0
        self.reset()
        self.calibrate(shunt_ohms, max_current, adc_range)

    def _transfer(self, output):
        received = bytearray(len(output))
        while not self._spi.try_lock():
            pass
        try:
            if self._cs is not None:
                self._cs.value = False
            self._spi.write_readinto(output, received)
            if self._cs is not None:
                self._cs.value = True
        finally:
            self._spi.unlock()
        return received

    def read_register(self, register, byte_count=None):
        """Read a register and return its raw unsigned value."""
        if byte_count is None:
            byte_count = _REG_BYTES.get(register, 2)
        received = self._transfer(
            bytes([(register << 2) | 1]) + bytes(byte_count)
        )
        value = 0
        for byte in received[1:]:
            value = (value << 8) | byte
        return value

    def write_register(self, register, value):
        """Write a 16-bit register."""
        value &= 0xFFFF
        self._transfer(
            bytes([register << 2, value >> 8, value & 0xFF])
        )

    def _update(self, register, mask, value):
        current = self.read_register(register)
        self.write_register(register, (current & ~mask) | (value & mask))

    @property
    def manufacturer_id(self):
        """Manufacturer identifier, expected to be 0x5449 (TI)."""
        return self.read_register(MANUFACTURER_ID)

    @property
    def die_id(self):
        """Device identifier, expected to be 0x229."""
        return self.read_register(DEVICE_ID) >> 4

    @property
    def revision(self):
        """Silicon revision nibble."""
        return self.read_register(DEVICE_ID) & 0x0F

    def reset(self):
        """Restore power-on register defaults."""
        self.write_register(CONFIG, 0x8000)
        time.sleep(0.002)

    def reset_accumulators(self):
        """Clear the ENERGY and CHARGE accumulators."""
        self._update(CONFIG, 0x4000, 0x4000)

    @property
    def adc_range(self):
        """False for +/-163.84 mV, True for +/-40.96 mV."""
        return bool(self.read_register(CONFIG) & 0x0010)

    @property
    def shunt_lsb(self):
        """Shunt-voltage resolution in volts per LSB."""
        return 78.125e-9 if self.adc_range else 312.5e-9

    @property
    def current_lsb(self):
        """Current resolution in amperes per LSB."""
        return self._current_lsb

    def calibrate(self, shunt_ohms, max_current, adc_range=False):
        """Configure ADC range and current/power calibration."""
        self._update(
            CONFIG,
            0x0010,
            0x0010 if adc_range else 0x0000,
        )
        self._current_lsb = max_current / (1 << 19)
        shunt_cal = 13107.2e6 * self._current_lsb * shunt_ohms
        if adc_range:
            shunt_cal *= 4
        shunt_cal = int(round(shunt_cal))
        if not 0 < shunt_cal <= 0x7FFF:
            raise ValueError(
                "SHUNT_CAL {} out of range; adjust shunt_ohms or "
                "max_current".format(shunt_cal)
            )
        self.write_register(SHUNT_CAL, shunt_cal)

    def configure_adc(
        self,
        mode=None,
        vbus_ct=None,
        vshunt_ct=None,
        temp_ct=None,
        avg=None,
    ):
        """Update selected ADC_CONFIG fields, preserving all others."""
        value = self.read_register(ADC_CONFIG)
        for field, shift, width in (
            (mode, 12, 0xF),
            (vbus_ct, 9, 0x7),
            (vshunt_ct, 6, 0x7),
            (temp_ct, 3, 0x7),
            (avg, 0, 0x7),
        ):
            if field is not None:
                value = (
                    value & ~(width << shift)
                ) | ((field & width) << shift)
        self.write_register(ADC_CONFIG, value)

    def set_conversion_delay(self, steps):
        """Set the initial conversion delay in 2 ms steps (0 through 255)."""
        self._update(CONFIG, 0x3FC0, (steps & 0xFF) << 6)

    @property
    def bus_voltage(self):
        """Bus voltage in volts."""
        return (self.read_register(VBUS) >> 4) * _BUS_LSB

    @property
    def shunt_voltage(self):
        """Signed shunt voltage in volts."""
        raw = _signed(self.read_register(VSHUNT) >> 4, 20)
        return raw * self.shunt_lsb

    @property
    def current(self):
        """Signed current in amperes."""
        raw = _signed(self.read_register(CURRENT) >> 4, 20)
        return raw * self._current_lsb

    @property
    def power(self):
        """Power in watts."""
        return self.read_register(POWER) * 3.2 * self._current_lsb

    @property
    def energy(self):
        """Accumulated energy in joules."""
        return (
            self.read_register(ENERGY)
            * 16
            * 3.2
            * self._current_lsb
        )

    @property
    def charge(self):
        """Signed accumulated charge in coulombs."""
        return _signed(self.read_register(CHARGE), 40) * self._current_lsb

    @property
    def temperature(self):
        """Internal die temperature in degrees Celsius."""
        return _signed(self.read_register(DIETEMP), 16) * _TEMP_LSB

    @property
    def diag_alert(self):
        """Raw DIAG_ALRT register."""
        return self.read_register(DIAG_ALRT)

    @diag_alert.setter
    def diag_alert(self, value):
        self.write_register(DIAG_ALRT, value)

    @property
    def conversion_ready(self):
        """Whether a fresh conversion is available."""
        return bool(self.read_register(DIAG_ALRT) & 0x0002)


def ft232h_spi(baudrate=1_000_000, mode=2):
    """Open the FT232H SPI bus with INA229-compatible edge timing.

    Set BLINKA_FT232H=1 before Python starts. Blinka rejects CPHA=1
    for the FT232H, while pyftdi's mode-1 three-phase emulation shifts
    INA229 responses on tested hardware. Mode 2 provides the equivalent
    working edge timing without three-phase emulation.
    """
    import board  # pylint: disable=import-outside-toplevel
    import busio  # pylint: disable=import-outside-toplevel

    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    while not spi.try_lock():
        pass
    try:
        spi.configure(
            baudrate=baudrate,
            polarity=0,
            phase=0,
        )
    finally:
        spi.unlock()
    spi._spi._port.set_mode(mode)  # pylint: disable=protected-access
    return spi
