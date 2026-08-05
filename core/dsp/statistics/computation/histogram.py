import numpy as np

def as_1d_complex(x) -> np.ndarray:
    """squeezes and converts to complex dtype."""
    x = np.asarray(x, dtype=np.complex128).squeeze()
    if x.ndim != 1:
        raise ValueError(f"Input must be 1D. Got shape: {x.shape}")
    return x

def validate_same_shape(x, y):
    if x.shape != y.shape:
        raise ValueError(f"Input arrays must have the same shape. Got shapes: {x.shape} and {y.shape}")
    return x, y


def complex_histogram_2d(
    x: np.ndarray,
    bins: int | tuple[int, int] = 128,
    range: tuple[tuple[float, float], tuple[float, float]] | None = None,
    density: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute a 2D histogram of a complex sequence over the IQ plane.

    Returns
    -------
    tuple
        hist, real_edges, imag_edges
    """
    x = as_1d_complex(x)

    hist, real_edges, imag_edges = np.histogram2d(
        np.real(x),
        np.imag(x),
        bins=bins,
        range=range,
        density=density,
    )

    return hist, real_edges, imag_edges


def complex_histogram_extent(
    real_edges: np.ndarray,
    imag_edges: np.ndarray,
) -> tuple[float, float, float, float]:
    """
    Convert histogram bin edges to an imshow extent.

    Returns
    -------
    tuple
        extent = (real_min, real_max, imag_min, imag_max)
    """
    return (
        float(real_edges[0]),
        float(real_edges[-1]),
        float(imag_edges[0]),
        float(imag_edges[-1]),
    )




def cross_histogram_2d(
    x: np.ndarray,
    y: np.ndarray,
    mode: str = "real-real",
    bins: int | tuple[int, int] = 128,
    range: tuple[tuple[float, float], tuple[float, float]] | None = None,
    density: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute a 2D cross-distribution histogram between two complex sequences.

    Supported modes
    ---------------
    "real-real"
        real(x) vs real(y)

    "imag-imag"
        imag(x) vs imag(y)

    "real-imag"
        real(x) vs imag(y)

    "imag-real"
        imag(x) vs real(y)

    "mag-mag"
        abs(x) vs abs(y)

    "phase-phase"
        angle(x) vs angle(y)

    "phase-diff"
        sample index density is not used here; use phase_difference_histogram instead.

    "corr-plane"
        real(x * conj(y)) vs imag(x * conj(y))

    "product-plane"
        real(x * y) vs imag(x * y)
    """
    x = as_1d_complex(x)
    y = as_1d_complex(y)
    x, y = validate_same_shape(x, y)

    if mode == "real-real":
        a = np.real(x)
        b = np.real(y)
    elif mode == "imag-imag":
        a = np.imag(x)
        b = np.imag(y)
    elif mode == "real-imag":
        a = np.real(x)
        b = np.imag(y)
    elif mode == "imag-real":
        a = np.imag(x)
        b = np.real(y)
    elif mode == "mag-mag":
        a = np.abs(x)
        b = np.abs(y)
    elif mode == "phase-phase":
        a = np.angle(x)
        b = np.angle(y)
    elif mode == "corr-plane":
        z = x * np.conj(y)
        a = np.real(z)
        b = np.imag(z)
    elif mode == "product-plane":
        z = x * y
        a = np.real(z)
        b = np.imag(z)
    else:
        raise ValueError(f"Unsupported cross histogram mode: {mode}")

    hist, a_edges, b_edges = np.histogram2d(
        a,
        b,
        bins=bins,
        range=range,
        density=density,
    )

    return hist, a_edges, b_edges



def histogram_bin_centers(edges: np.ndarray) -> np.ndarray:
    """
    Convert histogram bin edges to bin centers.
    """
    return 0.5 * (edges[:-1] + edges[1:])