# INA229 FT232H

A small Python driver for the Texas Instruments INA229 SPI
power/energy/charge monitor, including an FT232H helper for
Adafruit Blinka and pyftdi.

## Installation

Install the released package from PyPI:

```bash
python -m pip install ina229-ft232h
```

For local development, clone the repository and install it in editable mode:

```bash
python -m pip install -e .
```

Set `BLINKA_FT232H=1` before starting Python whenever the FT232H helper is
used.

## FT232H wiring

| FT232H | INA229 |
| --- | --- |
| D0 (SCK) | SCLK |
| D1 (MOSI) | SDI |
| D2 (MISO) | SDO |
| D3 | /CS |
| GND | GND |

The FT232H uses 3.3 V logic. Keep the SPI harness short and provide a solid
ground return. For longer harnesses, reduce the baud rate and consider source
series termination on SCK, MOSI, and /CS.

## Basic usage

```python
import ina229_ft232h as ina229

spi = ina229.ft232h_spi(baudrate=1_000_000)
device = ina229.INA229(
    spi,
    shunt_ohms=0.01,
    max_current=8.0,
)

print(device.bus_voltage)
print(device.shunt_voltage)
print(device.current)
print(device.power)
print(device.energy)
print(device.charge)
print(device.temperature)
```

`max_current` defines the signed CURRENT-register full scale and therefore
the current LSB. Choose it above the largest expected transient. The shunt drop
must also remain within the selected ADC range:

- `adc_range=False`: +/-163.84 mV
- `adc_range=True`: +/-40.96 mV, four times finer resolution

## ADC configuration

```python
device.configure_adc(
    mode=ina229.MODE_CONT_ALL,
    vbus_ct=ina229.CT_50US,
    vshunt_ct=ina229.CT_50US,
    temp_ct=ina229.CT_50US,
    avg=ina229.AVG_1,
)
```

The module exports the INA229 register addresses and `MODE_*`, `CT_*`, and
`AVG_*` field constants for lower-level use.

## SPI mode note

The INA229 requires falling-edge sampling. Blinka's FT232H backend rejects
CPHA=1, while pyftdi's mode-1 three-phase emulation shifted received INA229
words by one bit on the tested hardware. `ft232h_spi()` therefore defaults the
underlying pyftdi port to mode 2, which provides the working edge timing
without three-phase emulation. Override it with
`ft232h_spi(mode=...)` if another adapter requires different timing.

## Tests

```bash
python -m unittest discover -v
```

Release maintainers can find the trusted-publishing setup and release process
in [RELEASING.md](RELEASING.md).
