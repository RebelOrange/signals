import numpy as np
from matplotlib import pyplot as plt

from mpl.axis_config import AxisConfig
from matplotlib.axes import Axes
from matplotlib.patches import Ellipse, Circle

axis_y = 0.90
axis_x = 0.05

def apply_axis_config(ax:Axes, axis_config: AxisConfig):
    ax.set_title(axis_config.title, y=axis_y, x=axis_x, loc="left", fontsize=10, color="dimgray", fontweight="bold")
    ax.set_xlabel(axis_config.xlabel)
    ax.set_ylabel(axis_config.ylabel)
    ax.grid(axis_config.grid)
    return ax

def real_covariance_helper(x: np.ndarray, y: np.ndarray):
    x = np.asarray(x).squeeze()
    y = np.asarray(y).squeeze()
    data = np.vstack([x, y])
    mean = np.mean(data, axis=1)
    R = np.cov(data)

    eigenvalues, eigenvectors = np.linalg.eigh(R)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    eigenvalues = np.maximum(eigenvalues, 0)

    return mean, eigenvalues, eigenvectors

def plot_variance_elipse(x:np.ndarray, y:np.ndarray, ax:Axes, axis_config: AxisConfig | None = None):
    mean, eigenvalues, eigenvectors = real_covariance_helper(x, y)

    print(f"Eigenvector dot product: {np.dot(eigenvectors[:,0], eigenvectors[:,1])}")

    n_std = 2.0
    w = 2.0*n_std*np.sqrt(eigenvalues[0])
    h = 2.0*n_std*np.sqrt(eigenvalues[1])
    max_variance_vector = eigenvectors[:,0]
    angle = np.arctan2(max_variance_vector[1], max_variance_vector[0])
    ellipse = Ellipse(xy=mean,
                       width=w,
                       height=h,
                       angle=angle*180.0/np.pi,
                       color="r",
                       fill=False,
                        linewidth=1.0)
    ax.add_patch(ellipse)
    plot_vectors = True
    if plot_vectors:
        max_vec = eigenvectors[:,0]
        min_vec = eigenvectors[:,1]
        max_len = n_std*np.sqrt(eigenvalues[0])
        min_len = n_std*np.sqrt(eigenvalues[1])
        #ax.arrow(mean[0], mean[1], max_len*max_vec[0], max_len*max_vec[1], color="r", width=0.001)
        #ax.arrow(mean[0], mean[1], min_len*min_vec[0], min_len*min_vec[1], color="r", width=0.001)
        # maximum variance direction
        ax.plot(
            [mean[0] - max_len * max_vec[0], mean[0] + max_len * max_vec[0]],
            [mean[1] - max_len * max_vec[1], mean[1] + max_len * max_vec[1]],
            color="r",
            linewidth=1.0,
        )

        # minimum variance direction
        ax.plot(
            [mean[0] - min_len * min_vec[0], mean[0] + min_len * min_vec[0]],
            [mean[1] - min_len * min_vec[1], mean[1] + min_len * min_vec[1]],
            color="r",
            linewidth=1.0)

    # set axis limits based on min and max abs value
    lim = 1.05*np.maximum(np.max(np.abs(x)), np.max(np.abs(y)))
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    return ax


def plot_complex_distribution(x: np.ndarray, ax:Axes, axis_config: AxisConfig | None = None):
    color = "b"
    if axis_config is None:
        axis_config = AxisConfig(title="Complex Distribution", xlabel="Real", ylabel="Imaginary", grid=True, legend=False)
        color = axis_config.markercolor

    ax.scatter(x.real, x.imag, s=1,color=color)
    ax.set_box_aspect(1.0)

    ax = plot_variance_elipse(x.real, x.imag, ax, axis_config)

    return apply_axis_config(ax, axis_config)

def plot_cross_distribution(x: np.ndarray, y: np.ndarray, ax:Axes, axis_config: AxisConfig | None = None):
    color = "b"
    if axis_config is None:
        axis_config = AxisConfig(title="Cross Distribution", xlabel="x", ylabel="y", grid=True, legend=False)
        color = axis_config.markercolor

    ax.scatter(x, y, s=1, color=color)
    ax.set_box_aspect(1.0)

    ax=plot_variance_elipse(x, y, ax, axis_config)

    return apply_axis_config(ax, axis_config)

def plot_correlation_distribution(x: np.ndarray, y: np.ndarray, ax:Axes, axis_config: AxisConfig | None = None):
    color = "b"
    if axis_config is None:
        axis_config = AxisConfig(title="Correlation Distribution", xlabel="x", ylabel="y", grid=True, legend=False)
        color = axis_config.markercolor

    cor = np.correlate(x, y, mode="full")
    mean = np.mean(cor)
    cor_abs = np.abs(cor)
    max_cor_ind = np.argmax(cor_abs)
    max_cor = cor[max_cor_ind]
    var = np.mean(np.abs((cor)))



    ax.scatter(cor.real, cor.imag, s=1, color=color)
    lim = 1.05*np.maximum(np.max(np.abs(cor.real)), np.max(np.abs(cor.imag)))

    ax.arrow(mean.real, mean.imag, max_cor.real*0.95 ,max_cor.imag*0.95, color="r", width=0.001)
    c = Circle((mean.real, mean.imag), radius=var, linestyle="--",color="r", fill=False, linewidth=1.0)
    ax.add_patch(c)

    ax.set_box_aspect(1.0)

    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    return apply_axis_config(ax, axis_config)