import numpy as np

from mpl.axis_config import *
from matplotlib.axes import Axes


def plot_element_positions(P: np.ndarray, ax:Axes, axis_config: AxisConfig|None = None):


    # expected that P is 3 x N elemnts
    # check axis projection 2d vs 3d
    x, y, z = P[0,:], P[1,:], P[2,:]
    x, y, z = np.asarray(x).flatten(), np.asarray(y).flatten(), np.asarray(z).flatten()
    if '3d' in ax.name:
        ax.scatter(x,y,z)
        ax.set_box_aspect([1.0,1.0,1.0])
    else:
        ax.scatter(x,y)
        ax.set_box_aspect(1.0)

    if axis_config is None:
        axis_config = AxisConfig(title="Element Positions", xlabel="x [m]", ylabel="y [m]", grid=True)
    return apply_axis_config(ax, axis_config)

def plot_scan_response(resp: np.ndarray, az_points: np.ndarray, ax:Axes, axis_config: AxisConfig|None = None):
    # for now assume resp is in dB
    ax.plot(az_points, resp)
    if axis_config is None:
        axis_config = AxisConfig(title="Scan Response", xlabel="Azimuth [deg]", ylabel="Response [dB]", grid=True)
    return apply_axis_config(ax, axis_config)

def plot_element_scan_responses(az_grid, element_powers, el: float = 0.0, ax=None, db: bool = True):

    M, _ = element_powers.shape

    for m in range(M):
        ax.plot(az_grid, element_powers[m, :], label=f"Element {m}")

    ax.set_xlabel("Azimuth (deg)")
    ax.set_ylabel("Power (dB)" if db else "Power (Linear)")
    ax.set_title("Individual Element Scan Responses")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()

    return ax


