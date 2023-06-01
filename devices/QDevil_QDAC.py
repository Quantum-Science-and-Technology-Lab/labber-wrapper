class QDAC:

    # TODO: make use of QCodes with Labber (translate between their msgs and labber setValues statements?)
    # TODO: use JSONSchema to keep track of all these strings
    # TODO: our wrapper is beginning to duplicate QCodes' driver as Labber has a less full-featured driver for the QDAC.
    #   can we somehow use QCodes' driver on top of Labber?

    @staticmethod
    def _qdac_sync_key(sync):
        return f'Syn{sync} Source'

    @staticmethod
    def _qdac_channel_offset_key(ch_id):
        return f'CH{ch_id.zfill(2)} OffsetV'

    @staticmethod
    def _qdac_channel_amplitude_key(ch_id):
        return f'CH{ch_id.zfill(2)} AmplitudeV'

    @staticmethod
    def _qdac_generator_reps_key(g_id):
        return f'G{g_id} Repetitions'

    @staticmethod
    def _qdac_generator_steps_key(g_id):
        return f'G{g_id}'

    @staticmethod
    def _qdac_generator_sweep_rate_key(g_id):
        return f'G{g_id} Waveform - Sweep rate'

    @staticmethod
    def _qdac_generator_waveform_key(g_id):
        return f'G{g_id} Waveform'

    @staticmethod
    def _qdac_generator_trigger_key(g_id):
        return f'G{g_id} trigger'

    @staticmethod
    def _qdac_channel_mode_key(ch_id):
        return f'CH{ch_id.zfill(2)} Mode'

    def __init__(self, client, channel_generator_map):
        self.instr = client.connectToInstrument('QDevil QDAC', dict(interface='Serial', address='3'))

        for i, ch_id in enumerate(list(channel_generator_map.keys())):
            if ch_id > 24 or ch_id < 1:
                raise Exception(f'QDAC channel {ch_id} out of range (1..24).')
            if channel_generator_map[ch_id] > 10 or channel_generator_map[ch_id] < 1:
                raise Exception(f'QDAC generator {channel_generator_map[ch_id]} out of range (1..10).')

            self.instr.setValue(self._qdac_channel_mode_key(ch_id), f'Generator {channel_generator_map[ch_id]}')

        self._channel_generator_map = channel_generator_map

    def sync(self, sync, channel):
        if sync not in (1, 2):
            raise Exception('Sync parameter must be 1 or 2.')

        if channel > 24 or channel < 1:
            raise Exception(f'There are 24 channels labelled 1-24. {channel} specified.')

        generator = self._channel_generator_map[channel]
        self.instr.setValue(self._qdac_sync_key(sync), f'Generator {generator}')

    def ramp_voltages(
            self,
            v_startlist,
            v_endlist,
            ramp_time,
            step_length,
            repetitions,
            trigger=None
    ):
        if step_length < 0.001:
            raise Exception('Step length must be greater than 0.001ms')

        if not (len(v_startlist) == len(v_endlist) == len(list(self._channel_generator_map.keys()))):
            raise Exception('A start and end voltage must be supplied for each channel.')

        if len(list(self._channel_generator_map.keys())) > 10:
            raise Exception('Can\'t map more than 10 QDAC channels to its 10 generators.')

        nsteps = ramp_time / step_length

        for i, ch_id in enumerate(list(self._channel_generator_map.keys())):
            amplitude = v_endlist[i] - v_startlist[i]

            self.instr.setValue(self._qdac_channel_amplitude_key(ch_id), amplitude)
            self.instr.setValue(self._qdac_channel_offset_key(ch_id), v_startlist[i])

            g_id = self._channel_generator_map[ch_id]

            if trigger is not None:
                self.instr.setValue(self._qdac_generator_trigger_key(g_id), trigger)
            else:
                trigger = 'None'

            self.instr.setValue(self._qdac_generator_waveform_key(g_id), 'Stair case')
            self.instr.setValue(self._qdac_generator_sweep_rate_key(g_id), step_length * nsteps)
            self.instr.setValue(self._qdac_generator_steps_key(g_id), nsteps)
            self.instr.setValue(self._qdac_generator_reps_key(g_id), repetitions)
            self.instr.setValue(self._qdac_generator_trigger_key(g_id), trigger)

        time_ramp = nsteps * step_length / 1000  # s

        return time_ramp