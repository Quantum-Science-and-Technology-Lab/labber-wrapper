import Labber
import unittest
from ...devices.QDevil_QDAC import QDAC
from unittest.mock import MagicMock, call


class TestQDAC(unittest.TestCase):

    def setUp(self):
        self.device = QDAC(
            Labber.connectToServer('localhost'),
            {
                1: 2,
                2: 3,
                3: 4,
                4: 5
            }
        )

    def test_init(self):
        self.assertIsInstance(self.device, QDAC)
        assert hasattr(self.device, 'instr')
        self.assertIsNotNone(self.device.instr)

        cases = [
            (
                Labber.connectToServer('localhost'),
                {
                    1: 2,
                    2: 3,
                    3: 4,
                    4: 5
                }
            ),
            (
                Labber.connectToServer('localhost'),
                {
                    1: 3,
                    2: 4,
                    3: 5,
                    4: 6
                }
            ),
            (
                Labber.connectToServer('localhost'),
                {
                    1: 0,
                    2: 3,
                    3: 4,
                    4: 10
                }
            ),
            (
                Labber.connectToServer('localhost'),
                {
                    22: 2,
                    23: 3,
                    24: 4,
                    25: 5
                }
            ),
            (Labber.connectToServer('localhost'), None)
        ]

        for case in cases:
            if case[1] is not None:
                for ch_id in list(case[1].keys()):
                    if ch_id > 24 or ch_id < 1 or case[1][ch_id] > 10 or case[1][ch_id] < 1:
                        self.assertRaises(Exception, QDAC, case)

                    # could be optimized
                    else:
                        device = QDAC(*case)
                        config = device.instr.getLocalInitValuesDict()

                        self.assertEqual(config[device._qdac_channel_mode_key(ch_id)], f'Generator {case[1][ch_id]}')
                        self.assertEqual(config[device._qdac_mode_apply_key(ch_id)], True)

                        self.assertEqual(device._channel_generator_map, case[1])

    def test_sync(self):
        self.device.instr.setValue = MagicMock()

        cases = [(1, 1), (2, 2), (3, 3), (0, 4), (1, 25), (0, 0)]

        for case in cases:
            self.device.sync(*case)

            if case[0] not in (1, 2) or case[1] > 24 or case[1] < 1:
                self.assertRaises(Exception, self.device.sync, case)

            generator = case[1] + 1
            self.device.instr.setValue.assert_called_with(self.device._qdac_sync_key(case[0]), f'Generator {generator}')

    def test_ramp_setup(self):

        cases = [
            (
                [0, 0, 1],
                [1, 1, 0],
                0.1
            ),
            (
                [-1, -1, 10],
                [0, 0, 0],
                0.05
            ),
            (
                [9, -10, -10],
                [1, 0.5, 0],
                0.0
            ),
            (
                [],
                [1, 0.5, 0],
                0.0
            ),
        ]

        for case in cases:
            if case[2] < 0.001 or \
                    not (len(case[1]) == len(list(self.device._channel_generator_map.keys()))) or \
                    len(list(self.device._channel_generator_map.keys())) > 10 or \
                    len(case[0]) != len(list(self.device._channel_generator_map.keys())) and len(case[0]) != 0:

                self.assertRaises(Exception, self.device._ramp_setup, case)

            v_startlist = self.device._ramp_setup(*case)

            if len(case[0]) == 0:
                init = self.device.instr.getLocalInitValuesDict()
                for ch_id in list(self.device._channel_generator_map.keys()):
                    mode = init[self.device._qdac_channel_mode_key(ch_id)]
                    if mode == "DC":
                        self.assertEqual([init[self.device._qdac_channel_voltage_key(ch_id)]], v_startlist)
                    else:
                        self.assertEqual([init[self.device._qdac_channel_offset_key(ch_id)]], v_startlist)
            else:
                self.assertEqual(v_startlist, case[0])

    def test_ramp_voltages_software(self):

        v_startlists = [
            [0, 0, 1],
            [1, 2, 1],
            [-2, 1, -1]
        ]

        ramp_times = [
            0.2,
            0.4,
            0.8
        ]

        step_lengths = [
            0.1,
            0.2,
            0.4
        ]

        v_endlist = [1, 1, 0]

        for i, v_startlist in enumerate(v_startlists):

            self.device.ramp_voltages_software(
                v_startlist,
                v_endlist,
                ramp_times[i],
                step_lengths[i],
                1,
                self.device._channel_generator_map.keys()
            )

            self.device.setValue = MagicMock()

            # check that all configured channels are in DC mode
            for ch_id in [1, 2, 3]:
                self.assertEqual(self.device.instr.getValue(self.device._qdac_channel_mode_key(ch_id)), 'DC')
                self.assertEqual(self.device.instr.getValue(self.device._qdac_mode_apply_key(ch_id)), True)

            # check that each channel has a starting voltage
            self.device.setValue.assert_has_calls([
                call(self.device._qdac_channel_voltage_key(k + 1), v_startlist[k]) for k in [0, 1, 2]
            ])

            # check that each device has a stepped voltage
            voltages = [
                v_startlist[j] + (v_endlist[j] - v_startlist[j] / (ramp_times[i] / step_lengths[i])) for j in [0, 1, 2]
            ]

            calls = []

            for i, voltage in enumerate(voltages):
                calls.append(call(self.device._qdac_channel_voltage_key(i + 1), voltage))

            self.device.setValue.assert_has_calls(calls)
