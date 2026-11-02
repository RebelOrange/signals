import numpy as np
from core.vitis.pyap_fixed  import ap_fixed, ap_complex


def test_instantiation_paradigms():
    """Verify all 5 syntax styles yield bit-exact identical ap_fixed and ap_complex objects."""
    print("--- 1. Testing Type Instantiation & Typedef Paradigms ---")

    # Define type templates (archetypes)
    a_t = ap_fixed(16, 3, mode='AP_TRN', overflow='AP_SAT')
    c_t = ap_complex(16, 3, mode='AP_TRN', overflow='AP_SAT')

    real_data = [[0.7853, 1.25], [-0.5, 2.0]]
    complex_data = [[0.5 + 0.5j, 1.25 - 1.0j]]

    # 1. Callable Factory Pattern: a_t(data)
    r1 = a_t(real_data)
    c1 = c_t(complex_data)

    # 2. Positional Template: ap_fixed(a_t, data)
    r2 = ap_fixed(a_t, real_data)
    c2 = ap_complex(a_t, complex_data)  # Shares ap_fixed template for real & imag

    # 3. Keyword Template: ap_fixed(data, template=a_t)
    r3 = ap_fixed(real_data, template=a_t)
    c3 = ap_complex(complex_data, template=c_t)

    # 4. Fluid Chain Method: ap_fixed(data).typedef(a_t)
    r4 = ap_fixed(real_data).typedef(a_t)
    c4 = ap_complex(complex_data).typedef(c_t)

    # 5. Classic Signature (Backward Compatibility)
    r5 = ap_fixed(16, 3, real_data, mode='AP_TRN', overflow='AP_SAT')
    c5 = ap_complex(16, 3, complex_data, mode='AP_TRN', overflow='AP_SAT')

    # Assert exact binary equality across all paradigms
    assert np.array_equal(r1.raw(), r2.raw()) and np.array_equal(r2.raw(), r3.raw()) and np.array_equal(r3.raw(), r4.raw()) and np.array_equal(r4.raw(), r5.raw())
    assert np.array_equal(c1.raw()['real'], c2.raw()['real']) and np.array_equal(c2.raw()['real'], c5.raw()['real'])

    print("  [PASSED] All 5 instantiation paradigms match bit-for-bit.")


def test_real_matmul_and_bit_growth():
    """Verify matrix multiplication (@) and automatic accumulator bit-growth tracking."""
    print("\n--- 2. Testing Real Matrix Multiplication & Hardware Bit-Growth ---")

    in_t = ap_fixed(16, 3, mode='AP_TRN', overflow='AP_WRAP')

    A = in_t([[0.5, 1.25], [-0.5, 2.0]])  # Shape (2, 2), ap_fixed<16, 3>
    B = in_t([[0.5], [-1.0]])            # Shape (2, 1), ap_fixed<16, 3>

    # Matrix multiplication: 2x2 @ 2x1 -> Inner dimension K = 2
    # Accumulator Growth: W = W1 + W2 + ceil(log2(K)) = 16 + 16 + 1 = 33
    # Integer Growth:     I = I1 + I2 + ceil(log2(K)) = 3 + 3 + 1 = 7
    C = A @ B

    print(f"  Input  A Type: {A}")
    print(f"  Input  B Type: {B}")
    print(f"  Output C Type: {C}")

    assert C.W == 33
    assert C.I == 7
    assert C.shape == (2, 1)
    print("  [PASSED] Real matmul bit-growth correctly calculated (ap_fixed<33, 7>).")


def test_implicit_streaming_casting():
    """Verify C++ style implicit casting on assignment via the <<= operator."""
    print("\n--- 3. Testing Implicit Streaming Assignment (<<=) & Saturation ---")

    in_t = ap_fixed(16, 3, mode='AP_TRN', overflow='AP_WRAP')
    A = in_t([[0.7853, 1.25], [-0.5, 2.0]])
    B = in_t([[0.5], [-1.0]])

    # Target destination output register with saturation enabled
    # Preset to ap_fixed<16, 2, AP_TRN, AP_SAT>
    C_out = ap_fixed(16, 2, mode='AP_TRN', overflow='AP_SAT')

    # Stream matrix result directly into C_out (implicitly casts & saturates)
    C_out <<= A @ B

    print(f"  Target Destination Type: {C_out}")

    assert C_out.W == 16
    assert C_out.I == 2
    assert C_out.overflow == 'AP_SAT'
    print("  [PASSED] Implicit casting (<<=) correctly saturated result into target register.")


def test_complex_matmul_and_casting():
    """Verify complex fixed-point math, complex bit-growth (+1 bit for cross-products), and casting."""
    print("\n--- 4. Testing Complex Matrix Multiplication (ap_complex) ---")

    c_t = ap_complex(16, 3, mode='AP_TRN', overflow='AP_WRAP')

    A_c = c_t([[0.5 + 0.5j, 1.0 - 0.25j]])  # Shape (1, 2)
    B_c = c_t([[0.25 - 0.5j], [0.5 + 1.0j]])  # Shape (2, 1)

    # Complex Accumulator Growth:
    # W = W1 + W2 + 1 (complex cross-product) + ceil(log2(K)) = 16 + 16 + 1 + 1 = 34
    # I = I1 + I2 + 1 + ceil(log2(K)) = 3 + 3 + 1 + 1 = 8
    C_c = A_c @ B_c

    print(f"  Complex Matmul Result: {C_c}")

    assert C_c.W == 34
    assert C_c.I == 8

    # Test implicit streaming cast into saturated 16-bit complex container
    C_c_out = ap_complex(16, 3, mode='AP_TRN', overflow='AP_SAT')
    C_c_out <<= C_c

    print(f"  Saturated 16-bit Target: {C_c_out}")

    assert C_c_out.W == 16
    assert C_c_out.I == 3
    print("  [PASSED] Complex matmul bit-growth and streaming cast verified.")


if __name__ == '__main__':
    test_instantiation_paradigms()
    test_real_matmul_and_bit_growth()
    test_implicit_streaming_casting()
    test_complex_matmul_and_casting()
    print("\n=== ALL TESTS PASSED SUCCESSFULLY ===")