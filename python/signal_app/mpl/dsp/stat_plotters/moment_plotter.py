import numpy as np

from core.dsp.statistics.computation.moments import complex_moment

from matplotlib.axes import Axes

from core.dsp.statistics.computation.moments import cross_complex_moment
from mpl.axis_config import AxisConfig
from scipy.signal import lfilter

def moving_average(x: np.ndarray, window_len:int = 64) -> np.ndarray:
    b = np.ones(window_len) / float(window_len)
    return lfilter(b, 1.0, x)

def plot_moment(x: np.ndarray, p, q, ax:Axes, axis_config: AxisConfig|None = None, window_len:int=128):
    # plots the timeseries moment of specified order, with a moving average window
    _, sequence = complex_moment(x, p, q)
    sequence = moving_average(sequence, window_len)
    ax.plot(np.abs(sequence), label=f"M[{p:0.0f}{q:0.0f}](t) (order {p+q:0.0f})")

    ax.legend()
    return ax

def plot_cross_moment(x: np.ndarray, y: np.ndarray, px, qx, py, qy , ax:Axes, axis_config: AxisConfig|None = None, window_len:int=128):
    _, sequence = cross_complex_moment(x, y, px=px, qx=qx, py=py, qy=qy)
    sequence = moving_average(sequence, window_len)
    ax.plot(np.abs(sequence), label=f"M[{px:0.0f}{qx:0.0f}{py:0.0f}{qy:0.0f}](t) (order {px + qx+py+qy:0.0f})")

    ax.legend()
    return ax