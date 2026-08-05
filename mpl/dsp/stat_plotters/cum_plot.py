from core.dsp.statistics.computation.cumulents import *

import numpy as np
from matplotlib.axes import Axes

from mpl.axis_config import AxisConfig, apply_axis_config

def plot_auto_cumulant_4th(x:np.ndarray, ax: Axes, config:AxisConfig=None, window_len=64, type:int=0):

    match type:
        case 0:
            _, cum_seq = short_time_cross_cumulant_4th_order(x, x, window_len=window_len)
        case 1:
            cum_seq = gemini_short_time_cross_cumulant_4th(x, x, window_len=window_len)
    n = np.arange(len(cum_seq))
    ax.plot(n, cum_seq, label="Signal C_4")


    if config is None:
        config = AxisConfig(title="Signal 4th Order Cumulant", xlabel="sample index", ylabel="amplitude", grid=True, legend=False)
    apply_axis_config(ax=ax, axis_config=config)

    return ax