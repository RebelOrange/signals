from core.dsp.analog_to_digital.adc import ADC
from core.vitis.pyap_fixed import ap_fixed, ap_complex
import numpy as np
from core.dsp.algorithms.canceller_algorithms.providers.LMS import nlms
import matplotlib.pyplot as plt


def main():
    # AP fixed types from vitis
    int16_t_zero = ap_fixed(16,16,mode="AP_RND_ZERO",overflow="AP_SAT")
    int16_t_conv = ap_fixed(16,16,mode="AP_RND_CONV",overflow="AP_SAT")


    # random data
    N = 8096
    x = (100.0*(np.random.normal(size=N)+1j*np.random.normal(size=N)))[np.newaxis,:]
    x_shift = 3*np.exp(1j*0.75*np.pi)*x
    x_shift_2 = 6 * np.exp(1j * -0.75 * np.pi) * x

    X = np.vstack((x_shift))
    R = X@X.conj().T
    np.linalg.matrix_rank(R)
    print(f"R:")
    print(R)
    print(f"rank: {np.linalg.matrix_rank(R)}")
    print(np.shape(x))
    print(np.shape(X))

    #print(x)
    #print(np.round(x))


    lms = nlms(X=X, d=x[0,:], mu=0.1, order=2)

    iq_int16 = ap_fixed(x).typedef(int16_t_zero)
    iq_sc16 = ap_fixed(x).typedef(int16_t_conv)

    #print(iq_int16)
    print(np.mean(x))
    print(np.mean(iq_int16.to_float()))
    print(np.mean(iq_sc16.to_float()))

    e, y, W = lms.run_ap_fixed()

    plt.figure()
    plt.plot(np.real(e))
    plt.plot(np.imag(e))

    plt.figure()
    plt.plot(np.real(W[0,:]),"b-")
    plt.plot(np.imag(W[0,:]),"r-")
    plt.plot(np.real(W[1,:]),"b--")
    plt.plot(np.imag(W[1,:]),"r--")

    print(np.mean(np.real(W[0,200:])))


    plt.show()
    plt.figure()
    plt.plot(np.real(W[0,:]),"b-")
    plt.plot(np.imag(W[0,:]),"r-")
    plt.plot(np.real(W[1,:]),"b--")
    plt.plot(np.imag(W[1,:]),"r--")

    print(np.mean(np.real(W[0,200:])))


    plt.show()

    pass

if __name__ == '__main__':
    main()