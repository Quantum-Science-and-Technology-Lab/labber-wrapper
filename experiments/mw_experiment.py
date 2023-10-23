import Labber
import numpy as np
import time
from dataclasses import dataclass
from typing import Optional
from math import floor
import json
from jsonschema import validate
from statistics import mean

from labberwrapper.devices.Keysight_PXI_AWG import KeysightPXIAWG
from labberwrapper.devices.Keysight_PXI_Digitizer import KeysightPXIDigitizer
from labberwrapper.logging.log import Log
from labberwrapper.devices.AWG_SET import SET


import matplotlib
import matplotlib.pyplot as plt


@dataclass
class Piece(object):
    volts: float
    time_ns: float
    ramp_time_ns: Optional[float] = None
    length: Optional[int] = None

    def __len__(self):
        return self.length


class Piecewise(object):

    def __init__(self, pieces, ramp_time_ns, repeat=1, resolution_ns=1):
        for i, piece in enumerate(pieces):
            assert isinstance(piece, Piece)
            if piece.time_ns < 2 * resolution_ns:
                print(f'WARNING: piecewise function segment of length {piece.time_ns}ns depends on sampling beyond the Nyquist frequency.')
            if piece.ramp_time_ns is None and i != 0:
                piece.ramp_time_ns = ramp_time_ns
            elif piece.ramp_time_ns is None and repeat == 1 and i == 0:
                piece.ramp_time_ns = 0
            elif piece.ramp_time_ns is None and repeat != 1 and i == 0:
                piece.ramp_time_ns = ramp_time_ns
            if piece.length is None:
                piece.length = floor((piece.time_ns + piece.ramp_time_ns) / resolution_ns)

        self._pieces = pieces
        self._ramp_time = ramp_time_ns
        self._piece_index = 0
        self._raster_index = 0
        self._repeat_index = 0
        self._repeat = repeat
        self.resolution = resolution_ns

        waveform_length = 0
        for i, piece in enumerate(pieces):
            if i != len(pieces) - 1:
                waveform_length += floor((piece.time_ns + piece.ramp_time_ns) / resolution_ns)
            else:
                waveform_length += floor(piece.time_ns / resolution_ns)

        self.length = waveform_length

    def add(self, piece):
        assert isinstance(piece, Piece)
        if piece.ramp_time_ns is None:
            piece.ramp_time_ns = self._ramp_time
        self._pieces.append(piece)

    def insert(self, piece, index):
        assert isinstance(piece, Piece)
        before = self._pieces[0:index]
        after = self._pieces[index:]
        self._pieces = before + [piece] + after

    def remove(self, index):
        del self._pieces[index]

    def __len__(self):
        return self.length * self._repeat

    def __iter__(self):
        return self

    def __next__(self):

        # conditionally move to next piece
        if self._piece_index < len(self._pieces) - 1 and self._raster_index == len(self._pieces[self._piece_index]):
            self._piece_index += 1
            self._raster_index = 0

        # conditionally repeat the waveform from the start
        elif self._repeat_index < self._repeat - 1 and self._raster_index == len(self._pieces[self._piece_index]) \
                and self._piece_index == len(self._pieces) - 1:
            self._repeat_index += 1
            self._piece_index = 0
            self._raster_index = 0

        # end the iteration when we finish the last piece
        elif self._repeat_index == self._repeat - 1 and self._piece_index == len(self._pieces) - 1 \
            and self._raster_index == len(self._pieces[self._piece_index]):
            self._piece_index = 0
            self._raster_index = 0
            self._repeat_index = 0
            raise StopIteration

        # get the current piece
        piece = self._pieces[self._piece_index]

        # skip the ramp on the first piece of the first iteration
        if self._repeat_index == 0 and self._piece_index == 0 and self._raster_index == 0:
            self._raster_index += floor(piece.ramp_time_ns / self.resolution)

        # raster the ramp between pieces
        if self._raster_index < floor(piece.ramp_time_ns / self.resolution):
            curr_raster = self._raster_index
            self._raster_index += 1

            # get the starting voltage
            if self._piece_index != 0:
                target = self._pieces[self._piece_index - 1].volts
            elif self._repeat_index != 0:
                target = self._pieces[len(self._pieces) - 1].volts

            # calculate the slope
            slope = (piece.volts - target) / floor(piece.ramp_time_ns / self.resolution)
            x = curr_raster

            # get the voltage at this instant
            y = slope * x + target
            return y

        # raster the piece
        elif self._raster_index < floor((piece.time_ns + piece.ramp_time_ns) / self.resolution):
            self._raster_index += 1
            return piece.volts


def software_piecewise_microwave(
    single_electron_transistor,
    piecewise,
    num_samples,
    records,
    averages,
    buffer_size,
    impedance,
    coupling,
    rng,
    log_file='MW_TEST.hdf5',
    verbose=True
):
    # check for feasibility assuming this loop speed is limiting
    start = time.time()
    for i in range(100):
        pass
    stop = time.time()
    per_step = (stop - start) / 100

    if piecewise.resolution * 1e-9 < per_step:
        raise Exception('Piecewise signal resolution is beyond this computer\'s iteration speed.')

    # connect to server
    client = Labber.connectToServer('localhost')

    awg = KeysightPXIAWG(client)
    digitizer = KeysightPXIDigitizer(client)

    if verbose:
        # print AWG overview
        print(awg.instr.getLocalInitValuesDict())

        # print Digitizer overview
        print(digitizer.instr.getLocalInitValuesDict())

    volts = []
    for volt in piecewise:
        volts.append(volt)
    Vg1 = dict(name='Vg1', unit='V', values=volts)

    # initialize logging
    log = Log(
        log_file,
        'ai',
        'V',
        [Vg1]
    )

    reads = np.array([])

    digitizer.configure_acquisition(
        num_samples,
        records,
        averages,
        buffer_size,
        single_electron_transistor.ai_ch_num,
        impedance,
        coupling,
        rng
    )

    for volt in piecewise:
        awg.set_voltage(single_electron_transistor.plunger_1, volt)
        time.sleep(piecewise.resolution * 1e-9)
        values = digitizer.get_voltage(single_electron_transistor.ai_ch_num)
        reads = np.append(reads, mean(values['y']))

    data = {'ai': reads}
    log.file.addEntry(data)

    # fig, ax = plt.subplots()  # Create a figure containing a single axes.
    # ax.plot(np.linspace(0, len(reads), len(reads)), reads)  # Plot some data on the axes.
    # ax.set_xlabel(f'{piecewise.resolution} ns')
    # ax.set_ylabel('volts')
    # plt.show()

    digitizer.instr.stopInstrument()
    awg.instr.stopInstrument()

    # close connection
    client.close()


def hardware_piecewise_microwave(
    single_electron_transistor,
    piecewise,
    num_samples,
    records,
    averages,
    buffer_size,
    impedance,
    coupling,
    rng,
    log_file='MW_HW_TEST.hdf5',
    verbose=True
):

    if piecewise.resolution != 1:
        raise Exception('Piecewise function resolution must match the memory sampling rate of 1 GS/s. Please use 1ns.')

    # connect to server
    client = Labber.connectToServer('localhost')

    awg = KeysightPXIAWG(client)
    digitizer = KeysightPXIDigitizer(client)

    if verbose:
        # print AWG overview
        print(awg.instr.getLocalInitValuesDict())

        # print Digitizer overview
        print(digitizer.instr.getLocalInitValuesDict())

    volts = []
    for volt in piecewise:
        volts.append(volt)

    Vg1 = dict(name='Vg1', unit='V', values=volts)

    # initialize logging
    log = Log(
        log_file,
        'ai',
        'V',
        [Vg1]
    )

    results = np.array([])

    digitizer.configure_acquisition(
        num_samples,
        records,
        averages,
        buffer_size,
        single_electron_transistor.ai_ch_num,
        impedance,
        coupling,
        rng
    )

    # See https://rfmw.em.keysight.com/wireless/helpfiles/m31xx_m33xxa_awg/Content/M3201A_M3202A_PXIe_AWG_Users_Guide/10%20Overview%20of%20M3201A%20M3202A%20PXIe%20AWGs%20and%20Theory.html#AWG_Prescaler_and_Sampling_Rate
    # Memory sampling rate is either 1 GS/s, 200 MS/s or 100/n MS/s.
    # Defaults to 1 GS/s which is the clock speed for the M2202A.
    # Therefore we have a 1 ns resolution and Labber does not give us
    # control of this sampling rate.
    # The Nyquist frequency is half of the sampling rate from memory.
    # This will be left to the user to consider.
    awg.set_waveform(single_electron_transistor.plunger_1, volts)
    read = digitizer.get_voltage(single_electron_transistor.ai_ch_num)['y']
    time.sleep(piecewise.length * piecewise.resolution * 1e-9)

    # bins = len(piecewise)
    # bin_size = int(num_samples / bins)
    #
    # for i in range(bins):
    #     results = np.append(results, np.average(read[i * bin_size:(i + 1) * bin_size]))

    # data = {'ai': results}
    # log.file.addEntry(data)

    # fig, ax = plt.subplots()  # Create a figure containing a single axes.
    # ax.plot(np.linspace(0, len(read), len(read)), read)  # Plot some data on the axes.
    # ax.set_xlabel('2 ns')
    # ax.set_ylabel('volts')
    # plt.show()

    digitizer.instr.stopInstrument()
    awg.instr.stopInstrument()

    # close connection
    client.close()


if __name__ == '__main__':
    # define the SET to be measured
    dev_config = json.load(open('../device_configs/AWG_SET.json', 'r'))
    SET1 = SET(dev_config['plunger_1'])

    # load the experiment config
    config = json.load(open('../experiment_configs/mw_experiment.json', 'r'))
    jschema_mw = json.load(open('../json_schemas/experiment_schemas/mw_experiment.json', 'r'))
    jschema_set = json.load(open('../json_schemas/device_schemas/AWG_SET.json', 'r'))

    validate(instance=config, schema=jschema_mw)
    validate(instance=dev_config, schema=jschema_set)

    # generate the waveform
    software_piecewise_microwave(
        single_electron_transistor=SET1,
        piecewise=Piecewise(
            pieces=[
                Piece(volts=1, time_ns=1000),
                Piece(volts=2, time_ns=1000),
                Piece(volts=1, time_ns=1000)
            ],
            ramp_time_ns=config['ramp_time'],
            resolution_ns=100
        ),
        num_samples=config['samples'],
        records=config['records'],
        averages=config['averages'],
        buffer_size=config['buffer_size'],
        impedance=config['impedance'],
        coupling=config['coupling'],
        rng=config['range']
    )

    hardware_piecewise_microwave(
        single_electron_transistor=SET1,
        piecewise=Piecewise(
            pieces=[
                Piece(volts=1, time_ns=10),
                Piece(volts=2, time_ns=10),
                Piece(volts=1, time_ns=10)
            ],
            ramp_time_ns=config['ramp_time'],
            resolution_ns=1
        ),
        num_samples=config['samples'],
        records=config['records'],
        averages=config['averages'],
        buffer_size=config['buffer_size'],
        impedance=config['impedance'],
        coupling=config['coupling'],
        rng=config['range']
    )
