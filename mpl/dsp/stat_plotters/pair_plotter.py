import numpy as np
from matplotlib import pyplot as plt

from mpl.axis_config import AxisConfig
from matplotlib.axes import Axes

from mpl.dsp.stat_plotters.complex_distrobution import *
from core.dsp.statistics.computation.second_order import correlation
from matplotlib.transforms import Bbox


def apply_axis_config(ax:Axes, axis_config: AxisConfig):
    ax.set_title(axis_config.title, y=0.88, x=0.05, loc="left", fontsize=10, color="dimgray", fontweight="bold")
    ax.set_xlabel(axis_config.xlabel)
    ax.set_ylabel(axis_config.ylabel)
    ax.grid(axis_config.grid)
    return ax


def pair_plot_complex_signals(x: np.ndarray, y: np.ndarray, axes= None,  axis_config: AxisConfig = None):
    np.column_stack([np.real(x), np.imag(x), np.real(y), np.imag(y)])
    layout = [["hist_I1", "I1*Q1", "I1*I2", "I1*Q2"],
              [".", "hist_Q1", "Q1*I2", "Q1*Q2"],
              ["BIG", "BIG", "hist_I2", "I2*Q2"],
              ["BIG", "BIG", ".", "hist_Q2"]]
    if axes is None:
        fig, axes = plt.subplot_mosaic(layout, sharex=False, sharey=False, figsize=(12,12), constrained_layout=False)
        fig.subplots_adjust(
            left=0.03,
            right=0.995,
            bottom=0.03,
            top=0.995,
            wspace=0.02,
            hspace=0.02,
        )
    else:
        # check if axes follows layout???
        pass

    # disable axis labels and title, and ticks
    axis_config = AxisConfig(title="", xlabel="", ylabel="", grid=True, legend=False)
    for ax in axes.values():
        ax.tick_params(
            left=False,
            bottom=False,
            labelleft=False,
            labelbottom=False,
        )
        ax.set_box_aspect(1.0) # defualt aspect to 1.0

    # axis title spacing
    axis_y = 0.90
    axis_x = 0.05

    # histogram axis limits
    axis_limit = np.maximum(np.max(np.abs(x)), np.max(np.abs(y)))
    lims = (-axis_limit, axis_limit)

    # popluate diagonals with histograms
    bins = 100
    hists = {"x_real": axes["hist_I1"],
             "x_imag": axes["hist_Q1"],
             "y_real": axes["hist_I2"],
             "y_imag": axes["hist_Q2"]}

    hists["x_real"].hist(x.real, bins=bins)
    hists["x_real"].set_title("Signal_1 Real (I1)", y=axis_y, x=axis_x, loc="left", fontsize=10, color="dimgray", fontweight="bold")
    hists["x_imag"].hist(x.imag, bins=bins)
    hists["x_imag"].set_title("Signal_1 Imag (Q1)", y=axis_y, x=axis_x, loc="left", fontsize=10, color="dimgray", fontweight="bold")

    hists["y_real"].hist(y.real, bins=bins)
    hists["y_real"].set_title("Signal_2 Real (I2)", y=axis_y, x=axis_x, loc="left", fontsize=10, color="dimgray", fontweight="bold")
    hists["y_imag"].hist(y.imag, bins=bins)
    hists["y_imag"].set_title("Signal_2 Imag (Q2)", y=axis_y, x=axis_x, loc="left", fontsize=10, color="dimgray", fontweight="bold")

    # configure hist axes
    for key in hists.keys():
        hists[key].set_box_aspect(1.0)
        hists[key].set_xlim(lims)


    # populate 2d auto distros
    axis_config.title = "I1xQ1"
    plot_complex_distribution(x, axes["I1*Q1"], axis_config)

    axis_config.title = "I2xQ2"
    plot_complex_distribution(y, axes["I2*Q2"], axis_config)

    # populate cross distributions
    axis_config.title = "I1xI2"
    plot_cross_distribution(x.real, y.real, axes["I1*I2"], axis_config)
    axis_config.title = "I1xQ2"
    plot_cross_distribution(x.real, y.imag, axes["I1*Q2"], axis_config)
    axis_config.title = "Q1xI2"
    plot_cross_distribution(x.imag, y.real, axes["Q1*I2"], axis_config)
    axis_config.title = "Q1xQ2"
    plot_cross_distribution(x.imag, y.imag, axes["Q1*Q2"], axis_config)

    # plot complex correlation distribution (non-central)
    axis_config.title = "xCorr"
    plot_correlation_distribution(x, y, axes["BIG"], axis_config)



    return fig, axes


