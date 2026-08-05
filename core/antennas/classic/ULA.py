import numpy as np

from core.antennas.array import AntennaArray


class ULA(AntennaArray):
    def __init__(self, num_elements: int = 10, wavelength: float = 1.0, element_spacing: float = None):
        if element_spacing is None:
            element_spacing = wavelength / 2 # default to half-wavelength spacing
        # define positions on x axis with uniform spacing
        p_x = np.arange(num_elements) * element_spacing - num_elements * element_spacing / 2
        p = []
        for i in range(num_elements):
            p.append(np.array([p_x[i], 0, 0]))
        p = np.matrix(p).T
        super().__init__(positions=p, wavelength=wavelength)
        self.w = np.ones((self.num_elements, 1))/self.num_elements
        self.dx = element_spacing


