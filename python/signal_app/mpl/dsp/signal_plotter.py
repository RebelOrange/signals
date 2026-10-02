import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from mpl.axis_config import *


def plot_iq_timeseries(t: np.ndarray, iq: np.ndarray, ax:Axes, axis_config: AxisConfig|None = None)->Axes:
    ax.plot(t,np.real(iq), label=f"Real")
    ax.plot(t,np.imag(iq), label=f"Imag")

    if axis_config is None:
        axis_config = AxisConfig(title="Time Series",
                                 xlabel="Time [s]",
                                 ylabel="Amplitude",
                                 grid=True,
                                 legend=True)

    return apply_axis_config(ax, axis_config)

def plot_event_window(t, start_idx, end_idx, ax: Axes,name:str="Unlabeled Event"):
    all_y = np.concatenate([line.get_ydata() for line in ax.get_lines()])
    scale_factor = np.max(np.abs(all_y))

    y = np.zeros_like(t, dtype=float)
    y[start_idx:end_idx] = (3/4)*scale_factor

    ax.plot(t,y, "--", label=name)
    ax.legend(loc="upper right")
    return ax



def plot_fft(f: np.ndarray, F: np.ndarray, ax:Axes, axis_config: AxisConfig|None = None)->Axes:
    ax.plot(f,F, label=f"FFT")

    if axis_config is None:
        axis_config = AxisConfig(title="FFT",
                                 xlabel="Frequency [Hz]",
                                 ylabel="Magnitude",
                                 grid=True)

    return apply_axis_config(ax, axis_config)

def plot_phase(t: np.ndarray, P: np.ndarray, ax:Axes, axis_config: AxisConfig|None = None,
               unwrap:bool=True,
               degrees:bool=True)->Axes:
    if unwrap:
        P = np.unwrap(P)
    if degrees:
        P = np.rad2deg(P)
        ylabel = "Phase [deg]"
    else:
        ylabel = "Phase [rad]"

    ax.plot(t,P, label=f"Phase")

    if axis_config is None:
        axis_config = AxisConfig(title="Phase",
                                 xlabel="Time [s]",
                                 ylabel=ylabel,
                                 grid=True)

    return apply_axis_config(ax, axis_config)

def plot_spectrogram(S: np.ndarray, extent:tuple[float,float,float,float],  ax:Axes, axis_config: AxisConfig|None = None,
                     colorbar=True)->Axes:
    if S.dtype == np.complex128:
        S = 20*np.log10(np.abs(S))
    im = ax.imshow(S, extent=extent, aspect="auto", origin="lower", cmap="jet", )
    if colorbar:
        cbar = ax.figure.colorbar(im, ax=ax)
        print(type(cbar))

    if axis_config is None:
        axis_config = AxisConfig(title="Spectrogram",
                                 xlabel="Time [s]",
                                 ylabel="Frequency [Hz]",
                                 grid=True)

    return apply_axis_config(ax, axis_config)
