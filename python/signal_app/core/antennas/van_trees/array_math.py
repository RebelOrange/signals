import numpy as np
from numpy import *
from typing import Optional

# Van Trees angle spaces and conversions
def deg_to_rad(az,el):
    return asarray(az)*pi/180, asarray(el)*pi/180

def doa_to_spherical(az, el) -> tuple[ndarray, ndarray]:
    az, el = deg_to_rad(az, el)
    theta = asarray(el)-pi/2
    phi = asarray(az)+pi/2 # allow boresite to be at 0 degrees
    return theta, phi

def spherical_to_doa(theta, phi) -> tuple[ndarray, ndarray]:
    az = asarray(theta) + pi/2
    el = asarray(phi)
    return az, el

def doa_to_a(az, el):
    theta, phi = doa_to_spherical(az, el)
    a = vstack((-sin(theta)*cos(phi), -sin(theta)*sin(phi), -cos(theta)))
    return a

def a_to_u(a):
    return -a

def u_to_a(u):
    return -u

def a_to_k(a, wavelength: float):
    return (2*pi/wavelength) * a

def k_to_a(k, wavelength: float):
    return (2*pi/wavelength) * k

def doa_to_k(az, el, wavelength: float):
    return a_to_k(doa_to_a(az, el), wavelength)

# steering and spatial vector functions
def manifold_vector_k(k: ndarray, positions:ndarray, wavelength: float):
    N, L = k.shape # 3 columns x 1
    N,M = positions.shape # 3 columns x num_elements

    V = zeros((M,1), dtype=complex)
    for i in range(M):
        phi = k.T @ positions[:,i:i+1]
        V[i] = exp(-1j*phi)
    return V

def manifold_vector_doa(az, el, positions:ndarray, wavelength: float):
    a = asarray(az)
    e = asarray(el)
    k = doa_to_k(a, e, wavelength)
    return manifold_vector_k(k, positions, wavelength)

def scan_response_datamatrix(X: ndarray, positions: ndarray, wavelength: float, angle_resolution: float = 0.5):
    M, L = X.shape # num_elements x num_samples
    R = sample_covariance_matrix(X)

    # azimuth only?
    scan_angles = arange(-90, 90, angle_resolution)
    scan_powers = np.zeros(len(scan_angles))

    for idx, phi in enumerate(scan_angles):
        v = manifold_vector_doa(phi, 0, positions, wavelength)
        w = v / len(v)
        scan_power = abs(w.conj().T @ R @ w)[0,0]
        scan_powers[idx] = scan_power

    return scan_angles, 10*log10(scan_powers)

def scan_response_weights(w:ndarray, positions: ndarray, wavelength: float,
                          angle_resolution: float = 0.5) -> tuple[ndarray, ndarray]:
    scan_angles = arange(-90, 90, angle_resolution)
    scan_powers = np.zeros(len(scan_angles))

    for idx, phi in enumerate(scan_angles):
        v = manifold_vector_doa(phi, 0.0, positions, wavelength)
        scan_power = abs(w.conj().T @ v)[0]
        scan_powers[idx] = scan_power

    return scan_angles, 20 * log10(scan_powers)

def steering_matrix(steering_doa: tuple[float, float], positions: ndarray, wavelength: float):
    e = manifold_vector_doa(steering_doa[0], steering_doa[1], positions, wavelength)
    return diag(squeeze(e), k=0)

# covariance matrix functions
def sample_covariance_matrix(X: np.ndarray):
    N,L = X.shape
    return (1/L) * X @ X.conj().T

def subspace_decomposition(R: np.ndarray, threshold:float = 10)-> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    eigvals, eigvecs = np.linalg.eigh(R)
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:,idx]
    e_s = eigvals[eigvals > threshold]
    e_n = eigvals[eigvals <= threshold]
    E_s = eigvecs[:,eigvals > threshold]
    E_n = eigvecs[:,eigvals <= threshold]

    return (E_s, e_s), (E_n, e_n)


