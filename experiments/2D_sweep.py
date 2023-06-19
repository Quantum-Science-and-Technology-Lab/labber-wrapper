from threading import Thread

import Labber
import numpy as np
import time
import json

from ..devices.NI_DAQ import NIDAQ
from ..devices.QDevil_QDAC import QDAC
from ..devices.SET import SET
from ..logging import Log
from jsonschema import validate

def two_dimensional_sweep(
        single_e_transistor,
        config,
        channel_generator_map,
        gain=1e8,
        sample_rate_per_channel=1e6,
        v_min=-1,
        v_max=1
):

    # connect to instrument server
    client = Labber.connectToServer('localhost')

    # connect to instruments
    nidaq = NIDAQ(client)
    qdac = QDAC(client, channel_generator_map)

    # print QDAC overview
    print(qdac.instr.getLocalInitValuesDict())

    # ramp to initial voltages in 1 sec
    qdac.ramp_voltages(
        v_startlist=[],
        v_endlist=[
            config['bias_v'],
            config['plunger_v'],
            config['acc_v'],
            config['vb1_v'],
            config['vb2_v']
        ],
        ramp_time=1,
        repetitions=1,
        step_length=config['fast_step_size']
    )
    time.sleep(2)

    # NI_DAQ parameters calculation
    num_samples_raw = int(config['fast_steps'] * config['fast_step_size'] * sample_rate_per_channel)

    # collect data and save to database
    start_time = time.time()

    # setup logging parameters
    vfast_list = np.linspace(config['fast_vstart'], config['fast_vend'], config['fast_steps'])
    Vx = dict(name=config['fast_ch_name'], unit='V', values=vfast_list)

    vslow_list = np.linspace(config['slow_vstart'], config['slow_vend'], config['slow_steps'])
    Vy = dict(name=config['slow_ch_name'], unit='V', values=vslow_list)


    # initialize logging
    log = Log(
        "C:/Users/Measurement2/OneDrive/GroupShared/Data/QSim/20230530_measurement/TEST2.hdf5",
        'I',
        'A',
        [Vx, Vy]
    )

    for i, vslow in enumerate(vslow_list):
        qdac.ramp_voltages(
            v_startlist=[],
            v_endlist=[vslow for _ in range(len(config['slow_ch']))],
            ramp_time=config['slow_step_size'] * config['slow_steps'],
            repetitions=1,
            step_length=config['slow_step_size']
        )

        qdac.sync(1, config['fast_ch'][0])
        qdac.ramp_voltages(
            v_startlist=[config['fast_vstart'] for _ in range(len(config['fast_ch']))],
            v_endlist=[config['fast_vend'] for _ in range(len(config['fast_ch']))],
            ramp_time=config['fast_step_size'] * config['fast_steps'],
            step_length=config['fast_step_size'],
            repetitions=1
        )

        time.sleep(0.015)  # it usually takes about 2 ms for setting up the NIDAQ tasks

        qdac.instr.startInstrument()  # ramp_voltages only sets config, we still have to start

        result = nidaq.read(  # this read is not precise - it will just take num_samples_raw samples over the ramp time
            ch_id=single_e_transistor.ai_ch_num,
            v_min=v_min,
            v_max=v_max,
            gain=gain,
            num_samples=num_samples_raw,
            sample_rate=sample_rate_per_channel
        )

        qdac.instr.stopInstrument()

        data = {'I': result}
        log.file.addEntry(data)

        print(
            f'Time elapsed: {np.round(time.time() - start_time, 2)} sec. '
            f'Loop finished: {i + 1}/{config["slow_steps"]}.')

    end_time = time.time()
    print(f'Time elapsed: {np.round(end_time - start_time, 2)} sec.')


if __name__ == '__main__':

    # define the SET to be measured
    SET1 = SET(9, 10, 11, 12, 13, "Dev2/ai0")  # TODO: get from config

    # load the experiment config
    config = json.load(open('../configs/2D_sweep.json', 'r'))
    jschema = jschema = json.load(open('../json_schemas/1d_&_2Dsweeps.json', 'r'))

    # voltage safety check
    validate(instance=config, schema=jschema)

    # perform the sweep
    two_dimensional_sweep(SET1, config, {
        SET1.bias_ch_num: 1,
        SET1.plunger_ch_num: 2,
        SET1.acc_ch_num: 3,
        SET1.vb1_ch_num: 4,
        SET1.vb2_ch_num: 5
    })
