from dataclasses import dataclass


@dataclass
class SET:
    bias_ch_num: int = 1
    plunger_ch_num: int = 2
    acc_ch_num: int = 3
    vb1_ch_num: int = 4
    vb2_ch_num: int = 5
    ai_ch_num: int = 1

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f'SET(' \
               f'{self.bias_ch_num}, ' \
               f'{self.plunger_ch_num}, ' \
               f'{self.acc_ch_num}, ' \
               f'{self.vb1_ch_num}, ' \
               f'{self.vb2_ch_num}, ' \
               f'{self.ai_ch_num}' \
               f')'
