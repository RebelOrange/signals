#include "../include/mlms.h"
#ifndef __SYNTHESIS__
#include <fstream>
#include <iomanip>
#include <iostream>
#endif




template <typename T_DIVISOR, typename T_DIVIDEND, typename T_OUT>
void div_round_pow2(T_DIVISOR divisor, T_DIVIDEND dividend, T_OUT& out) {
    #pragma HLS INLINE

    // 1. Guard against zero / underflow
    if (divisor == 0) {
        out = dividend; // Default to unscaled mu if energy is zero
        return;
    }

    // 2. Count leading zeros (Uses fast GCC/Clang built-in synthesizable by Vivado/Vitis)
    unsigned int leading_zeros = __builtin_clzll((unsigned long long)divisor);
    unsigned int msb_index     = 63 - leading_zeros;

    // 3. Round UP to next power of 2 (Ceiling Power of 2)
    T_DIVISOR msb  = (T_DIVISOR(1) << msb_index);
    bool round_up  = (divisor > msb);
    unsigned int shift = round_up ? (msb_index + 1) : msb_index;

    // 4. Shift dividend directly (Preserves fixed-point fractional bits)
    if (shift >= 64) {
        out = 0;
    } else {
        out = dividend >> shift;
    }
#define UNROLL_UPDATE 1
}

/*
void div_round_pow2(inner_prod divisor, inner_prod dividend, error_T& out){
    #pragma HLS INLINE
    #pragma HLS PIPELINE style=flp
    unsigned int leading_zeros = divisor.countLeadingZeros();
    unsigned int msb_index = 63-leading_zeros;
    inner_prod msb = (inner_prod(1) << msb_index);
    bool round_up = (divisor > msb);
    unsigned int shift = round_up ? (msb_index+1) : msb_index;
    if (shift >=64) out = inner_prod(0);
    out = dividend >> shift;
}*/

void normalize_lms(sc16* x, error_T mu, error_T &step_size){
    #pragma HLS INLINE
    inner_prod EPS = 1e-8;
    inner_prod innerP = 0+EPS;
    ip_loop: for(int i=0; i<NUM_WEIGHTS; i++){
        #pragma HLS UNROLL
        innerP+=x[i].real()*x[i].real() + x[i].imag()*x[i].imag();
    }
    //step_size = mu / innerP;
    div_round_pow2(innerP, mu, step_size);
}

error_cplx stap_filter(sc16* x, weight_cplx* w){
    #pragma HLS INLINE
    error_cplx y;

    // fir loop
    error_T a_r=0;
    error_T a_i=0;
    // use two for loops for area optimization options in header
    fir_loop: for (int t=0; t<FIR_ORDER; t++){
            TIME_UNROLL
            for (int c=0; c<NUM_X_IN_CHAN; c++){
            SPATIAL_UNROLL
            int i = c*FIR_ORDER + t;
            a_r += x[i].real()*w[i].real() - x[i].imag()*(-w[i].imag());
            a_i += x[i].real()*(-w[i].imag()) + x[i].imag()*w[i].real();
        }
    }
    y.real(a_r);
    y.imag(a_i);
    return y;
}

void update_weights(error_T e_r, error_T e_i, sc16* x, weight_cplx (&w)[NUM_WEIGHTS], error_T mu){
    #pragma HLS INLINE
    error_T mu_norm;
    normalize_lms(x, mu, mu_norm);
    update_weight_loop: for (int t=0; t<FIR_ORDER; t++){
            TIME_UNROLL
            for (int c=0; c<NUM_X_IN_CHAN; c++){
            SPATIAL_UNROLL
            int i = c*FIR_ORDER + t;
            weight_t w_delta_real = mu_norm*(x[i].real()*e_r + x[i].imag()*e_i);
            weight_t w_delta_imag = mu_norm*(x[i].imag()*e_r - x[i].real()*e_i);
            w[i].real(w[i].real()+w_delta_real);
            w[i].imag(w[i].imag()+w_delta_imag);
        }
    }
}

void multi_lms_module(axis_stream d_in,
                      axis_stream_multi X_in[NUM_X_IN_CHAN],
                      axis_stream output,
                     ap_ufixed<32,0,AP_TRN, AP_SAT> mu_in,
                    weight_cplx (&w_out)[NUM_WEIGHTS]){
PIPELINE

// port level variables
#pragma HLS INTERFACE mode=axis port=d_in
#pragma HLS INTERFACE mode=axis port=X_in
#pragma HLS INTERFACE mode=axis port=output
#pragma HLS INTERFACE mode=ap_none port=mu_in
#pragma HLS INTERFACE mode=ap_vld port=w_out
#pragma HLS ARRAY_PARTITION variable=w_out complete
#pragma HLS INTERFACE mode=ap_ctrl_none port=return

axis_packet d_tmp, out_tmp;
axis_packet X_tmp[NUM_X_IN_CHAN];
#pragma HLS ARRAY_PARTITION variable=X_tmp complete

// local variables
// shift register in matrix form
static sc16 X_shift[NUM_X_IN_CHAN][FIR_ORDER];
#pragma HLS ARRAY_PARTITION variable=X_shift complete dim=0

// vectorized input data
sc16 X[NUM_WEIGHTS];
#pragma HLS ARRAY_PARTITION variable=X complete
static weight_cplx w[NUM_WEIGHTS]={};
weight_cplx w_local[NUM_WEIGHTS];
#pragma HLS ARRAY_PARTITION variable=w complete
#pragma HLS DEPENDENCE variable=w inter false
#pragma HLS ARRAY_PARTITION variable=w_local complete
error_cplx y, e;
error_T mu=mu_in;

// read w into w_local: explicit read from static variable
w_read_loop: for(int i=0; i<NUM_WEIGHTS; i++){
    #pragma HLS UNROLL
    w_local[i]=w[i];
}

// read inputs
d_in.read(d_tmp);
for (int i=0; i<NUM_X_IN_CHAN; i++){
    #pragma HLS UNROLL
    X_in[i].read(X_tmp[i]);
}

// update shift register
for(int c=0; c<NUM_X_IN_CHAN; c++){
    #pragma HLS UNROLL
    for (int t=FIR_ORDER-1; t>0; t--){
        #pragma HLS UNROLL
        X_shift[c][t] = X_shift[c][t-1];
    }

    X_shift[c][0]=X_tmp[c].data;

    // vectorize shift register for stap algorithm
    for(int t=0; t<FIR_ORDER; t++){
        X[c*FIR_ORDER+t] = X_shift[c][t];
    }
    
}

// Algorithm: Algorithm function calls
y = stap_filter(X, w_local);
e.real(d_tmp.data.real()-y.real());
e.imag(d_tmp.data.imag()-y.imag());
update_weights(e.real(), e.imag(), X, w_local, mu);

// store w_local in w: explicit write to static variable
w_store_loop: for(int i=0; i<NUM_WEIGHTS; i++){
    #pragma HLS UNROLL
    w[i]=w_local[i];
    w_out[i] = w_local[i];
}

#ifndef __SYNTHESIS__
#endif

out_tmp.data.real(e.real());
out_tmp.data.imag(e.imag());

out_tmp.keep = d_tmp.keep;
out_tmp.strb = d_tmp.strb;
out_tmp.last = d_tmp.last;
output.write(out_tmp);


                     }