"""Continuously print all INA229 measurements."""

import time

import ina229_ft232h as ina229


spi = ina229.ft232h_spi(baudrate=1_000_000)
device = ina229.INA229(
    spi,
    shunt_ohms=0.01,
    max_current=8.0,
)
device.configure_adc(
    mode=ina229.MODE_CONT_ALL,
    vbus_ct=ina229.CT_1052US,
    vshunt_ct=ina229.CT_1052US,
    temp_ct=ina229.CT_1052US,
    avg=ina229.AVG_16,
)

while True:
    print(
        "bus={:.4f} V shunt={:.6f} V current={:.6f} A "
        "power={:.6f} W energy={:.6f} J charge={:.6f} C "
        "temperature={:.2f} C".format(
            device.bus_voltage,
            device.shunt_voltage,
            device.current,
            device.power,
            device.energy,
            device.charge,
            device.temperature,
        )
    )
    time.sleep(0.5)
