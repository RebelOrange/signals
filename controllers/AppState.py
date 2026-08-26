from dataclasses import dataclass
from typing import List

from core.antennas.array import AntennaArray
from core.dsp.analog_to_digital import adc
from core.dsp.signal_new import Signal


@dataclass
class AppState:
    antenna: AntennaArray = None
    input_sigs: List[Signal] = None
    rx_sigs: List[Signal] =None
    adc_inst: adc = None
    adc_sigs: List[Signal] = None