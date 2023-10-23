

class KeysightPXIAWG:

    @staticmethod
    def _keysight_trigger_key():
        return 'Trig All'

    @staticmethod
    def _keysight_offset_key(channel):
        return f'Ch{channel} - Offset'

    @staticmethod
    def _keysight_function_key(channel):
        return f'Ch{channel} - Function'
    
    @staticmethod
    def _keysight_enabled_key(channel):
        return f'Ch{channel} - Enabled'

    @staticmethod
    def _keysight_waveform_key(channel):
        return f'Ch{channel} - Waveform'

    @staticmethod
    def _keysight_run_key():
        return 'Run'

    @staticmethod
    def _keysight_trig_mode_key(channel):
        return f'Ch{channel} - Trig mode'

    def __init__(self, client):
        self.instr = client.connectToInstrument('Keysight PXI AWG', dict(interface='PXI', address='4'))

    def set_voltage(self, channel, voltage):
        self.instr.startInstrument()
        self.instr.setValue(self._keysight_function_key(channel), 'DC')
        self.instr.setValue(self._keysight_enabled_key(channel), 'On')
        self.instr.setValue(self._keysight_offset_key(channel), voltage)

    def set_waveform(self, channel, voltages):
        self.instr.startInstrument()
        # errors thrown with each of these commented out lines
        # self.instr.setValue(self._keysight_enabled_key(channel), True)
        # self.instr.setValue(self._keysight_function_key(channel), 'AWG')
        # self.instr.setValue(self._keysight_trig_mode_key(channel), 'Continuous')
        self.instr.setValue(self._keysight_waveform_key(channel), voltages)
        # self.instr.setValue(self._keysight_run_key(), True)
