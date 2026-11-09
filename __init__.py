"""A Python implementation of FLake with daily example inputs."""
from .configuration import Lake,ModelOptions,InitialConditions
from .inputs import example_lakes,load_example,example_settings,SCENARIO_LABELS
from .model import simulate,Simulation
__all__=['Lake','ModelOptions','InitialConditions','example_lakes','load_example','simulate','Simulation']
__version__='0.4.0'
