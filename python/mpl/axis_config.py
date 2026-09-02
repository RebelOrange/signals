from dataclasses import dataclass
from matplotlib.axes import Axes

@dataclass
class AxisConfig:
    title: str = ""
    xlabel: str =""
    ylabel: str = ""
    grid: bool = True
    legend: bool = True
    markercolor: str = "blue"


def apply_axis_config(ax: Axes, axis_config: AxisConfig|None = None) -> Axes:
    if axis_config is None:
        return ax

    ax.set_title(axis_config.title)
    ax.set_xlabel(axis_config.xlabel)
    ax.set_ylabel(axis_config.ylabel)
    ax.grid(axis_config.grid)
    if axis_config.legend:
        ax.legend()
    return ax