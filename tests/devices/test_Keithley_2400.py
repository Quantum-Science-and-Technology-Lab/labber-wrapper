import Labber
import unittest
from unittest.mock import MagicMock
from functools import partial
from devices.Keithley_2400 import Keithley2400


class TestKeithley2400(unittest.TestCase):

    def setUp(self):
        self.device = Keithley2400(Labber.connectToServer('localhost'))
        self.device.set_value = partial(self.device.set_value, validating=True)

    def test_init(self):
        self.assertIsInstance(self.device, Keithley2400)
        assert hasattr(self.device, 'instr')
        self.assertIsNotNone(self.device.instr)

    def test_set_voltage(self):
        self.device.set_value = MagicMock()
        self.device.instr.setValue = MagicMock()

        # check that bad values are filtered out
        self.device.set_voltage('f')
        self.device.set_voltage(-3)
        self.device.set_voltage(3)

        self.device.instr.setValue.assert_not_called()

        # check that good values are set properly
        for v in [-2, -1, 0, 1, 2]:
            self.device.set_voltage(v)

            self.device.set_value.assert_called_with(self.device._keithley_src_status_key(), True)
            self.device.set_value.assert_called_with(self.device._keithley_src_func_key(), 'Voltage')
            self.device.set_value.assert_called_with(self.device._keithley_src_volt_key(), v)
            self.device.instr.setValue.assert_called_with(self.device._keithley_src_volt_key(), v)


