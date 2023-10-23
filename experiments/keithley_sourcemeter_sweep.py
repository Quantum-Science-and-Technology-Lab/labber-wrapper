import Labber
import numpy as np
import time
import json

from labberwrapper.devices.NI_DAQ import NIDAQ
from labberwrapper.devices.Keithley_2400 import Keithley2400
from labberwrapper.devices.SET import SET
from labberwrapper.logging.log import Log

V_LIMIT = 2.5


def keithley_sourcemeter_sweep(
        single_e_transistor,
        config,
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
    keithley = Keithley2400(client)

    if verbose:
        # print NIDAQ overview
        print(nidaq.instr.getLocalInitValuesDict())

        # print Keithley overview
        print(keithley.instr.getLocalInitValuesDict())

    # NI_DAQ parameters calculation
    num_samples_raw = int(config['step_length'] * sample_rate_per_channel)

    vslow_list = np.linspace(config['slow_vstart'], config['slow_vend'], config['slow_steps'])
    Vg1 = dict(name='Vg1', unit='V', values=vslow_list)

    # initialize logging
    log = Log(
        log_file,
        'NIai',
        'V',
        [Vg1]
    )

    results = np.array([])

    for vslow in vslow_list:
        keithley.set_voltage(vslow)
        time.sleep(config['step_length'])

        nidaq.configure_read(
            ch_id=single_e_transistor.ai_ch_num,
            v_min=v_min,
            v_max=v_max,
            num_samples=num_samples_raw,
            sample_rate=sample_rate_per_channel
        )
        result = nidaq.read(
            ch_id=single_e_transistor.ai_ch_num,
            gain=gain
        )
        results = np.append(results, np.average(result))
    data = {'NIai': results}
    log.file.addEntry(data)

    keithley.instr.stopInstrument()


if __name__ == '__main__':

    # define the SET to be measured
    dev_config = json.load(open('../device_configs/SET.json', 'r'))
    SET1 = SET(dev_config["bias_ch_num"])

    # load the experiment config
    config = json.load(open('../experiment_configs/keithley_sweep.json', 'r'))

    # voltage safety check
    if config['bias_volt'] > V_LIMIT:
        raise Exception("Voltage too high")

    # perform the sweep
    keithley_sourcemeter_sweep(
        SET1,
        config,
        {
            SET1.bias_ch_num: 1
        },
        v_min=-10,
        v_max=10,
        sample_rate_per_channel=1e3
    )
