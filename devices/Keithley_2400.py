import os
from pathlib import PurePath
from labberwrapper.devices.BaseDevice import BaseDevice


class Keithley2400(BaseDevice):

    @staticmethod
    def _keithley_src_status_key():
        return 'Output on'

    @staticmethod
    def _keithley_src_func_key():
        return 'Source type'

    @staticmethod
    def _keithley_src_volt_key():
        return 'Source voltage'

    def __init__(self, client):
        wd = PurePath(os.path.dirname(os.path.realpath(__file__))).parent
        file = open(PurePath(wd).joinpath("json_schemas/instrument_schemas/Keithley_2400_SourceMeter.json"), "r")
        schema = ''.join(file.readlines())
        file.close()
        super().__init__('Keithley 2400 SourceMeter', dict(interface='GPIB', address='2'), client, schema)

    def set_voltage(self, voltage):
        # TODO: use custom driver
        self.instr.startInstrument()
        self.set_value(self._keithley_src_status_key(), True)
        self.set_value(self._keithley_src_func_key(), 'Voltage')
        self.set_value(self._keithley_src_volt_key(), voltage)

