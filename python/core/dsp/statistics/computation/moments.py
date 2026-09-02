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

def complex_moment_grid(x: np.ndarray, max_order:int = 4, central:bool = False) -> tuple[dict[tuple[int, int,int,int], complex], dict[tuple[int, int,int,int], np.ndarray]]:
    """Compute E[x^px conj(x)^qx] for each element in x.
    Returns a 2D array of shape (x.shape[0], max_order+1) containing the moments."""
    x = as_1d_complex(x)
    moments_val = {}
    moments_seq = {}
    for p in range(max_order+1):
        for q in range(max_order+1-p):
            (moments_val[(p, q)], moments_seq[(p, q)]) = complex_moment(x=x, p=p, q=q, central=central)
    return moments_val, moments_seq

def cross_complex_moment_grid(x: np.ndarray, y: np.ndarray, max_order:int = 4, central:bool = False) -> tuple[dict[tuple[int, int,int,int], complex], dict[tuple[int, int,int,int], np.ndarray]]:
    """Compute E[x^px conj(x)^qx y^py conj(y)^qy] for each element in x and y.
    Returns a 2D array of shape (x.shape[0], y.shape[0]) containing the moments."""
    x = as_1d_complex(x)
    y = as_1d_complex(y)
    x, y = validate_same_shape(x, y)

    moments_val = {}
    moments_seq = {}
    for px in range(max_order+1):
        for qx in range(max_order+1-px):
            for py in range(max_order+1-px-qx):
                for qy in range(max_order+1-py-qx-px):
                    (moments_val[(px, qx, py, qy)], moments_seq[(px, qx, py, qy)]) = cross_complex_moment(x=x, y=y, px=px, qx=qx, py=py, qy=qy, central=central)

    return moments_val, moments_seq

def complex_moment(x: np.ndarray, p: int, q: int, central: bool = False) -> tuple[complex, np.ndarray]:
    """Compute E[x^px conj(x)^qx].
    Returns the mean and sequence of instant moments."""
    x = as_1d_complex(x)
    return cross_complex_moment(x=x,
                                    y=x,
                                    px=p,
                                    qx=q,
                                    py=0,
                                    qy=0,
                                    central=central)

def cross_complex_moment(
    x: np.ndarray,
    y: np.ndarray,
    px: int,
    qx: int,
    py: int,
    qy: int,
    central: bool = False,
) -> tuple[complex, np.ndarray]:
    """Compute E[x^px conj(x)^qx y^py conj(y)^qy].
    Returns the mean and sequence of instant moments. """
    x, y = validate_same_shape(x, y)
    calc: np.ndarray = np.zeros(x.shape, dtype=np.complex128)
    if central:
        x0 = x - np.mean(x)
        y0 = y - np.mean(y)
        calc = (x0 ** px) * (np.conj(x0) ** qx) * (y0 ** py) * (np.conj(y0) ** qy)
    else:
        calc =(x ** px) * (np.conj(x) ** qx) * (y ** py) * (np.conj(y) ** qy)

    return np.mean(calc), calc