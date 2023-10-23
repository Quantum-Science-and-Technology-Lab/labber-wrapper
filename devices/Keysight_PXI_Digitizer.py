

class KeysightPXIDigitizer:

    @staticmethod
    def _keysight_signal_key(channel):
        return f'Ch{channel} - Signal'

    @staticmethod
    def _keysight_number_of_samples_key():
        return 'Number of samples'

    @staticmethod
    def _keysight_number_of_records_key():
        return 'Number of records'

    @staticmethod
    def _keysight_number_of_averages_key():
        return 'Number of averages'

    @staticmethod
    def _keysight_records_per_buffer_key():
        return 'Records per Buffer'

    @staticmethod
    def _keysight_channel_enable_key(channel):
        return f'Ch{channel} - Enabled'

    @staticmethod
    def _keysight_channel_impedance_key(channel):
        return f'Ch{channel} - Impedance'

    @staticmethod
    def _keysight_channel_coupling_key(channel):
        return f'Ch{channel} - Coupling'

    @staticmethod
    def _keysight_channel_range_key(channel):
        return f'Ch{channel} - Range'

    @staticmethod
    def _keysight_trig_mode_key():
        return 'Trig Mode'

    def __init__(self, client):
        self.instr = client.connectToInstrument('Keysight PXI Digitizer', dict(interface='PXI', address='3'))

    def configure_acquisition(
            self,
            samples,
            records,
            averages,
            buffer_size,
            channel,
            impedance,
            coupling,
            range
    ):
        self.instr.startInstrument()
        self.instr.setValue(self._keysight_number_of_samples_key(), samples)
        self.instr.setValue(self._keysight_number_of_records_key(), records)
        self.instr.setValue(self._keysight_number_of_averages_key(), averages)
        self.instr.setValue(self._keysight_records_per_buffer_key(), buffer_size)
        self.instr.setValue(self._keysight_channel_enable_key(channel), True)
        self.instr.setValue(self._keysight_channel_impedance_key(channel), impedance)
        self.instr.setValue(self._keysight_channel_coupling_key(channel), coupling)
        self.instr.setValue(self._keysight_channel_range_key(channel), range)
        self.instr.setValue(self._keysight_trig_mode_key(), 'Immediate')

    def get_voltage(self, channel):
        self.instr.startInstrument()
        return self.instr.getValue(self._keysight_signal_key(channel))
