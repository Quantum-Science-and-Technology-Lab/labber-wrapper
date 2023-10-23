from threading import Thread

import Labber
import numpy as np
import time
import json

from labberwrapper.devices.NI_DAQ import NIDAQ
from labberwrapper.devices.QDevil_QDAC import QDAC
from labberwrapper.devices.SET import SET
from labberwrapper.logging.log import Log
from jsonschema import validate


def two_dimensional_sweep(
        single_e_transistor,
        slow_ch,
        fast_ch,
        slow_vstart,
        slow_vend,
        slow_steps,
        fast_vstart,
        fast_vend,
        fast_steps,
        fast_step_size,
        fast_ch_name,
        slow_ch_name,
        slow_step_size,
        channel_generator_map,
        gain=1,
        sample_rate_per_channel=1e6,
        v_min=-1,
        v_max=1,
        log_file='TEST.hdf5',
        verbose=True
):

    # connect to instrument server
    client = Labber.connectToServer('localhost')

    # connect to instruments
    nidaq = NIDAQ(client)
    qdac = QDAC(client, channel_generator_map)

    if verbose:
        # print NIDAQ overview
        print(nidaq.instr.getLocalInitValuesDict())

        # print QDAC overview
        print(qdac.instr.getLocalInitValuesDict())

    # NI_DAQ parameters calculation
    num_samples_raw = int(fast_steps * fast_step_size * sample_rate_per_channel)

    # collect data and save to database
    start_time = time.time()

    # setup logging parameters
    vfast_list = np.linspace(fast_vstart, fast_vend, fast_steps)
    Vx = dict(name=fast_ch_name, unit='V', values=vfast_list)

    vslow_list = np.linspace(slow_vstart, slow_vend, slow_steps)
    Vy = dict(name=slow_ch_name, unit='V', values=vslow_list)

    # initialize logging
    log = Log(
        log_file,
        'I',
        'A',
        [Vx, Vy]
    )

    slow_ramp_mapping = {}

    for i in range(len(slow_ch)):
        slow_ramp_mapping[slow_ch[i]] = channel_generator_map[slow_ch[i]]

    fast_ramp_mapping = {}

    for i in range(len(fast_ch)):
        fast_ramp_mapping[fast_ch[i]] = channel_generator_map[fast_ch[i]]

    slow_qdac = QDAC(client, slow_ramp_mapping)
    fast_qdac = QDAC(client, fast_ramp_mapping)

    for i, vslow in enumerate(vslow_list):
        results = np.array([])
        
        slow_qdac.ramp_voltages_software(
            v_startlist=[],
            v_endlist=[vslow for _ in range(len(slow_ch))],
            ramp_time=slow_step_size * slow_steps,
            repetitions=1,
            step_length=slow_step_size
        )

        qdac.sync(1, fast_ch[0])

        nidaq.configure_read(  # this read is not precise - it will just take num_samples_raw samples over the ramp time
            ch_id=single_e_transistor.ai_ch_num,
            v_min=v_min,
            v_max=v_max,
            num_samples=num_samples_raw,
            sample_rate=sample_rate_per_channel
        )

        fast_qdac.ramp_voltages(
            v_startlist=[fast_vstart for _ in range(len(fast_ch))],
            v_endlist=[fast_vend for _ in range(len(fast_ch))],
            ramp_time=fast_step_size * fast_steps,
            step_length=fast_step_size,
            repetitions=1
        )

        time.sleep(fast_step_size)

        result = nidaq.read(  # this read is not precise - it will just take num_samples_raw samples over the ramp time
            ch_id=single_e_transistor.ai_ch_num,
            gain=gain
        )

        bins = fast_steps
        bin_size = int(num_samples_raw / bins)

        for i in range(bins):
            results = np.append(results, np.average(result[i * bin_size:(i+1) * bin_size]))

        data = {
            'I': results,
            'Vx': vfast_list,
            'Vy': vslow
        }
        log.file.addEntry(data)

        print(
            f'Time elapsed: {np.round(time.time() - start_time, 2)} sec. '
            f'Loop finished: {i + 1}/{slow_steps}.')
    
    qdac.instr.stopInstrument()

    end_time = time.time()
    print(f'Time elapsed: {np.round(end_time - start_time, 2)} sec.')


if __name__ == '__main__':

    # define the SET to be measured
    dev_config = json.load(open('../device_configs/SET.json', 'r'))
    SET1 = SET(
        dev_config["bias_ch_num"],
        dev_config["plunger_ch_num"],
        dev_config["acc_ch_num"],
        dev_config["vb1_ch_num"],
        dev_config["vb2_ch_num"],
        dev_config["ai_ch_num"]
    )

    # load the experiment config
    config = json.load(open('../experiment_configs/2D_sweep.json', 'r'))
    jschema_sweep = jschema = json.load(open('../json_schemas/experiment_schemas/1D_&_2Dsweeps.json', 'r'))
    jschema_dev = json.load(open('../json_schemas/device_schemas/QDAC_SET.json', 'r'))

    # voltage safety check
    validate(instance=config, schema=jschema_sweep)
    validate(instance = dev_config, schema = jschema_dev) 

    # perform the sweep
    two_dimensional_sweep(
        SET1,
        config['slow_ch'],
        config['fast_ch'],
        config['slow_vstart'],
        config['slow_vend'],
        config['slow_steps'],
        config['fast_vstart'],
        config['fast_vend'],
        config['fast_steps'],
        config['fast_step_size'],
        config['fast_ch_name'],
        config['slow_ch_name'],
        config['slow_step_size'],
        channel_generator_map={
            SET1.bias_ch_num: 1,
            SET1.plunger_ch_num: 2,
            SET1.acc_ch_num: 3,
            SET1.vb1_ch_num: 4,
            SET1.vb2_ch_num: 5
        }
    )
