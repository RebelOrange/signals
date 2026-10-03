from dataclasses import dataclass
from typing import List

from core.antennas.array import AntennaArray
from core.dsp.analog_to_digital.adc import ADC
from core.dsp.signal_new import Signal

import numpy as np

@dataclass
class AppState:
    antenna: AntennaArray = None
    input_sigs: List[Signal] = None
    rx_sigs: List[Signal] =None
    adc_inst: ADC = None
    adc_sigs: List[Signal] = None
    iq_data_path: str = None

    vitis_iq: np.ndarray = None
    vitis_weights: np.ndarray = None