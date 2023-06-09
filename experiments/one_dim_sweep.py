import Labber
import numpy as np
import time
import json

from labberwrapper.devices.NI_DAQ import NIDAQ
from labberwrapper.devices.QDevil_QDAC import QDAC
from labberwrapper.devices.SET import SET
from labberwrapper.logging.log import Log

V_LIMIT = 2.5


# TODO: add one_dimensional_sweep_hardware
def one_dimensional_sweep(
        single_e_transistor,
        config,
        channel_generator_map,
        gain=1,
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
    qdac.ramp_voltages_software(
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
    num_samples_raw = config['fast_steps']

    # collect data and save to database
    start_time = time.time()

    vfast_list = np.linspace(config['fast_vstart'], config['fast_vend'], config['fast_steps'])
    Vx = dict(name=config['fast_ch_name'], unit='V', values=vfast_list)

    # initialize logging
    log = Log(
        "TEST.hdf5",
        'I',
        'A',
        [Vx]
    )

    fast_ramp_mapping = {}
    results = np.array([])

    for i in range(len(config['fast_ch'])):
        fast_ramp_mapping[config['fast_ch'][i]] = channel_generator_map[config['fast_ch'][i]]

    fast_qdac = QDAC(client, fast_ramp_mapping)

    # TODO: call ramp_voltages_software once and remove this outer loop
    for vfast in vfast_list:
        fast_qdac.ramp_voltages_software(
            v_startlist=[],
            v_endlist=[vfast for _ in range(len(config['fast_ch']))],
            ramp_time=0.1,
            repetitions=1,
            step_length=config['fast_step_size']
        )
        time.sleep(0.005)
        result = nidaq.read(
            ch_id=single_e_transistor.ai_ch_num,
            v_min=v_min,
            v_max=v_max,
            gain=gain,
            num_samples=num_samples_raw,
            sample_rate=sample_rate_per_channel
        )
        results = np.append(results, np.average(result))
    data = {'I': results}
    log.file.addEntry(data)

    qdac.instr.stopInstrument()
    fast_qdac.instr.stopInstrument()

    end_time = time.time()
    print(f'Time elapsed: {np.round(end_time - start_time, 2)} sec.')


if __name__ == '__main__':

    # define the SET to be measured
    dev_config = json.load(open('../device_configs/SET.json', 'r'))
    SET1 = SET(dev_config["bias_ch_num"],
               dev_config["plunger_ch_num"],
               dev_config["acc_ch_num"],
               dev_config["vb1_ch_num"],
               dev_config["vb2_ch_num"],
               dev_config["ai_ch_num"])

    #SET1 = SET(9, 10, 11, 12, 13, 0) - old SET1 (without config)

    # load the experiment config
    config = json.load(open('../configs/1D_sweep.json', 'r'))

    # voltage safety check
    if any(np.abs([
                config['bias_v'],  # TODO: move out of config
                config['plunger_v'],
                config['acc_v'],
                config['vb1_v'],
                config['vb2_v'],
                config['fast_vend']
            ]) > V_LIMIT):
        raise Exception("Voltage too high")

    # perform the sweep
    one_dimensional_sweep(SET1, config, {
        SET1.bias_ch_num: 1,
        SET1.plunger_ch_num: 2,
        SET1.acc_ch_num: 3,
        SET1.vb1_ch_num: 4,
        SET1.vb2_ch_num: 5
    })