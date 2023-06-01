class NIDAQ:
    _ni_num_sames_key = 'Number of samples'
    _ni_sample_rate_key = 'Sample rate'
    _ni_trig_key = 'Trig source'

    @staticmethod
    def _ni_data_key(ch_id):
        return f'Ch{ch_id}: Data'

    @staticmethod
    def _ni_enable_key(ch_id):
        return f'Ch{ch_id}: Enabled'

    @staticmethod
    def _ni_high_range_key(ch_id):
        return f'Ch{ch_id}: High range'

    @staticmethod
    def _ni_low_range_key(ch_id):
        return f'Ch{ch_id}: Low range'

    def __init__(self, client):
        self.instr = client.connectToInstrument('NI DAQ', dict(interface='PXI', address='Dev1'))

    def read(self, ch_id, gain, num_samples, sample_rate, v_min=-10, v_max=10, trigger=None):

        # configure sampling
        self.instr.setValue(self._ni_num_sames_key, num_samples)
        self.instr.setValue(self._ni_sample_rate_key, sample_rate)

        # enable channel
        for channel in range(1, 8, 1):
            self.instr.setValue(self._ni_enable_key(channel), False)
        self.instr.setValue(self._ni_enable_key(ch_id), True)

        # configure range
        self.instr.setValue(self._ni_high_range_key(ch_id), v_max)
        self.instr.setValue(self._ni_low_range_key(ch_id), v_min)

        # optionally use triggering
        if trigger is not None:
            self.instr.setValue(self._ni_trig_key, trigger)

        # make measurement
        self.instr.startInstrument()
        result = self.instr.getValue(self._ni_data_key(ch_id)) / gain
        self.instr.stopInstrument()

        return result