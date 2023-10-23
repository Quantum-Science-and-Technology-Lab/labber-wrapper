import json
import numpy as np

from labberwrapper.experiments.mw_experiment import Piece, Piecewise, software_piecewise_microwave, hardware_piecewise_microwave
from labberwrapper.experiments.one_dim_sweep import one_dimensional_sweep
from labberwrapper.experiments.two_dim_sweep import two_dimensional_sweep
from labberwrapper.experiments.keithley_sweep import keithley_sweep
from labberwrapper.experiments.keithley_sourcemeter_sweep import keithley_sourcemeter_sweep
from jsonschema import validate
from labberwrapper.devices.SET import SET
from labberwrapper.devices.AWG_SET import SET as AWG_SET

V_LIMIT = 2.5

if __name__ == "__main__":

    # ONE DIMENSIONAL SWEEP

     # define the SET to be measured
    config = json.load(open('./labberwrapper/configs/1D_sweep.json', 'r'))
    dev_config = json.load(open('./labberwrapper/device_configs/SET.json', 'r'))
    SET1 = SET(dev_config["bias_ch_num"],
               dev_config["plunger_ch_num"],
               dev_config["acc_ch_num"],
               dev_config["vb1_ch_num"],
               dev_config["vb2_ch_num"],
               dev_config["ai_ch_num"]) 

    # perform the sweep
    one_dimensional_sweep(SET1,
                          config["fast_ch"],
                          config["fast_vstart"],
                          config["fast_vend"],
                          config["fast_steps"],
                          config["fast_step_size"],
                          config["fast_ch_name"],
                          {SET1.bias_ch_num: 1,
                          SET1.plunger_ch_num: 2,
                          SET1.acc_ch_num: 3,
                          SET1.vb1_ch_num: 4,
                          SET1.vb2_ch_num: 5},
                          sample_rate_per_channel=1e3)

    # TWO DIMENSIONAL SWEEP

    # define the SET to be measured
    dev_config = json.load(open('./labberwrapper/device_configs/SET.json', 'r'))
    SET1 = SET(dev_config["bias_ch_num"],
               dev_config["plunger_ch_num"],
               dev_config["acc_ch_num"],
               dev_config["vb1_ch_num"],
               dev_config["vb2_ch_num"],
               dev_config["ai_ch_num"])

    # load the experiment config
    config = json.load(open('./labberwrapper/configs/2D_sweep.json', 'r'))

    # voltage safety check
    if any(np.abs([
                config['bias_v'],
                config['plunger_v'],
                config['acc_v'],
                config['vb1_v'],
                config['vb2_v'],
                config['slow_vend'],
                config['fast_vend']
            ]) > V_LIMIT):
        raise Exception("Voltage too high")

    # perform the sweep
    two_dimensional_sweep(SET1, config, {
        SET1.bias_ch_num: 1,
        SET1.plunger_ch_num: 2,
        SET1.acc_ch_num: 3,
        SET1.vb1_ch_num: 4,
        SET1.vb2_ch_num: 5
    },
    sample_rate_per_channel=1e3)

    # KEITHLEY SWEEP
    
    # define the SET to be measured
    dev_config = json.load(open('./labberwrapper/device_configs/SET.json', 'r'))
    SET1 = SET(dev_config["bias_ch_num"])

    # load the experiment config
    config = json.load(open('./labberwrapper/configs/keithley_sweep.json', 'r'))

    # voltage safety check
    if  config['bias_volt'] > V_LIMIT:
        raise Exception("Voltage too high")

    # perform the sweep
    keithley_sweep(SET1, config, {
            SET1.bias_ch_num: 1
        },
        v_min=-10,
        v_max=10,
        sample_rate_per_channel=1e3
    )

    # KEITHLEY SOURCEMETER SWEEP
    
    # define the SET to be measured
    dev_config = json.load(open('./labberwrapper/device_configs/SET.json', 'r'))
    SET1 = SET(dev_config["bias_ch_num"])

    # load the experiment config
    config = json.load(open('./labberwrapper/configs/keithley_sweep.json', 'r'))

    # voltage safety check
    if  config['bias_volt'] > V_LIMIT:
        raise Exception("Voltage too high")

    # perform the sweep
    keithley_sourcemeter_sweep(SET1, config, {
            SET1.bias_ch_num: 1
        },
        v_min=-10,
        v_max=10,
        sample_rate_per_channel=1e3
    )

    # MICROWAVE EXPERIMENT

    # define the SET to be measured
    SET1 = AWG_SET(1)

    # load the experiment config
    config = json.load(open('./labberwrapper/experiment_configs/mw_experiment.json', 'r'))
    jschema_mw = json.load(open('./labberwrapper/json_schemas/mw_experiment.json', 'r'))

    validate(instance=config, schema=jschema_mw)

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
        samples=config['samples'],
        records=config['records'],
        averages=config['averages'],
        buffer_size=config['buffer_size']
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
        samples=config['samples'],
        records=config['records'],
        averages=config['averages'],
        buffer_size=config['buffer_size']
    )
