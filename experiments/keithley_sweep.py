import Labber
import numpy as np
import time
import json

from labberwrapper.devices.NI_DAQ import NIDAQ
from labberwrapper.devices.Keithley_6430 import Keithley6430
from labberwrapper.devices.SET import SET
from labberwrapper.logging.log import Log
from jsonschema import validate


def keithley_sweep(
    single_e_transistor,
    slow_vstart,
    slow_vend,
    slow_steps,
    step_length,
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
    keithley = Keithley6430(client)

    if verbose:
        # print NIDAQ overview
        print(nidaq.instr.getLocalInitValuesDict())

        # print Keithley overview
        print(keithley.instr.getLocalInitValuesDict())

    # NI_DAQ parameters calculation
    num_samples_raw = int(step_length * sample_rate_per_channel)

    vslow_list = np.linspace(slow_vstart, slow_vend, slow_steps)
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
        time.sleep(step_length)

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
    jschema_sweep = json.load(open('../json_schemas/experiment_schemas/keithley_sweep.json', 'r'))
    jschema_dev = json.load(open('../json_schemas/device_schemas/QDAC_SET.json', 'r'))

    # voltage safety check
    validate(instance=config, schema=jschema_sweep)
    validate(instance=dev_config, schema=jschema_dev)

    # perform the sweep
    keithley_sweep(
        SET1,
        slow_vstart=config['slow_vstart'],
        slow_vend=config['slow_vend'],
        slow_steps=config['slow_steps'],
        step_length=config['step_length'],
        v_min=-10,
        v_max=10,
        sample_rate_per_channel=1e3
    )