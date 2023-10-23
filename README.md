# labber-wrapper
A library of software utilities and experimental procedures built on Labber. The library provides the following features on top of the Labber python API.

1) Ease of use. Labber's data model exposes all of its instrument configurations as key, value dictionaries with setters and getters. The objects have keys that are irregular and hard to predict. Therefore we have written utilities that allow code complletion to fill in the blanks for you.

2) Validation. We have written JSON Schemas for all of the configuration dictionaries relevant to devices in the QSTL lab that specify acceptable value types and ranges. Any experiment script can be validated in real-time or before-hand by either enabling continuous validation or a precursory call to `validate()`. This way we won't fry any devices.

3) Compatibility. We initialize our objects with the appropriate JSON Schemas and use the Labber API to populate them so that they match whatever configuration you have setup on your instrument at startup. We can then validate any changes that your script makes to the configuration with no effort.

4) Experiments. We have provided a number of out-of-the-box experiments such as voltage sweeps and piecewise voltage ramps.

5) Testability. We provide (passing) tests with our experiments and with our classes that wrap Labber API usage.

# Examples

Each experiment is encapsulated in an importable function. Some come with additional public
utilities such as classes and functions that can be imported alongside the experiment.

For example, below we make use of the Piece and Piecewise utilities to construct a piecewise
ramp function to run on a Keysight 3202A PXI AWG. We also make use of an optional validatable 
config file to parameterize the experiment.

```
from labberwrapper.experiments.mw_experiment import Piece, Piecewise, hardware_piecewise_microwave

# define the SET to be measured
SET1 = AWG_SET(1)

# load the experiment config
config = json.load(open('./labberwrapper/experiment_configs/mw_experiment.json', 'r'))
jschema_mw = json.load(open('./labberwrapper/json_schemas/mw_experiment.json', 'r'))

# validate the config
validate(instance=config, schema=jschema_mw)

# run the experiment
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
```

See the `/examples` folder for more examples. Examples usages are also provided at the bottom of each
experiment file under `/experiments`.

# Testing

To run the tests associated with a particular driver run the correpsonding test suite like `python -m unittest tests/devices/test_Keithley_2400.py`. To run the entire test suite use `python -m unittest discover`.
