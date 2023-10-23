import unittest
from devices.SET import SET


class TestSET(unittest.TestCase):

    def test_init(self):

        device = SET()
        self.assertIsInstance(device, SET)

        self.assertEqual(device.bias_ch_num, 1)
        self.assertEqual(device.plunger_ch_num, 2)
        self.assertEqual(device.acc_ch_num, 3)
        self.assertEqual(device.vb1_ch_num, 4)
        self.assertEqual(device.vb2_ch_num, 5)
        self.assertEqual(device.ai_ch_num, 1)

        for i in range(4):
            bias_ch_num = i
            plunger_ch_num = i
            acc_ch_num = i
            vb1_ch_num = i
            vb2_ch_num = i
            ai_ch_num = i

            device = SET(
                bias_ch_num,
                plunger_ch_num,
                acc_ch_num,
                vb1_ch_num,
                vb2_ch_num,
                ai_ch_num
            )

            self.assertEqual(device.bias_ch_num, i)
            self.assertEqual(device.plunger_ch_num, i)
            self.assertEqual(device.acc_ch_num, i)
            self.assertEqual(device.vb1_ch_num, i)
            self.assertEqual(device.vb2_ch_num, i)
            self.assertEqual(device.ai_ch_num, i)

            st = f'SET(' \
                   f'{bias_ch_num}, ' \
                   f'{plunger_ch_num}, ' \
                   f'{acc_ch_num}, ' \
                   f'{vb1_ch_num}, ' \
                   f'{vb2_ch_num}, ' \
                   f'{ai_ch_num}' \
                   f')'
            self.assertEqual(str(device), st)
