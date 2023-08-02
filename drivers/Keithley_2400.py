import VISA_Driver from VISA_Driver
from labberwrapper.devices.Keithley_2400 import Keithley2400


class Keithley2400Driver(VISA_Driver):

    def performOpen(self, options={}):
        """Perform the open instrument connection operation"""
        self.dMeasParam = {}
        VISA_Driver.performOpen(self, options=options)

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""

        if quant.name == Keithley2400._keithley_src_volt_key():
            self.setValue(Keithley2400._keithley_src_func_key(), 'Voltage')
            self.setValue(Keithley2400._keithley_src_status_key(), True)
            self.setValue(Keithley2400._keithley_src_volt_key(), value)

        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        return quant.getValue()