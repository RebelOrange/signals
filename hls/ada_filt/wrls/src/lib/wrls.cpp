#include "../include/wrls.h"
#ifndef __SYNTHESIS__
#include <fstream>
#include <iomanip>
#include <iostream>
#endif




template <typename T_DIVISOR, typename T_DIVIDEND, typename T_OUT>
void div_round_pow2(T_DIVISOR divisor, T_DIVIDEND dividend, T_OUT& out) {
    #pragma HLS INLINE

    if (divisor == 0) {
        out = dividend;
        return;
    }

    unsigned int leading_zeros = __builtin_clzll((unsigned long long)divisor);
    unsigned int msb_index     = 63 - leading_zeros;

    T_DIVISOR msb  = (T_DIVISOR(1) << msb_index);
    bool round_up  = (divisor > msb);
    unsigned int shift = round_up ? (msb_index + 1) : msb_index;

    if (shift >= 64) {
        out = 0;
    } else {
        out = dividend >> shift;
    }
#define UNROLL_UPDATE 1
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

// Update weight vector: w = w + k * conj(e)
void update_weights(error_cplx e, weight_cplx* k, weight_cplx* w) {
    #pragma HLS INLINE
    update_weight_loop: for (int i = 0; i < NUM_WEIGHTS; i++) {
        #pragma HLS UNROLL
        weight_t dw_r = k[i].real() * e.real() + k[i].imag() * e.imag();
        weight_t dw_i = k[i].imag() * e.real() - k[i].real() * e.imag();
        w[i].real(w[i].real() + dw_r);
        w[i].imag(w[i].imag() + dw_i);
    }
}

void compute_pi(sc16* x, weight_cplx P[NUM_WEIGHTS][NUM_WEIGHTS], weight_cplx* pi) {
    #pragma HLS INLINE
    pi_row_loop: for (int r = 0; r < NUM_WEIGHTS; r++) {
        #pragma HLS UNROLL
        weight_t sum_r = 0;
        weight_t sum_i = 0;
        pi_col_loop: for (int c = 0; c < NUM_WEIGHTS; c++) {
            #pragma HLS UNROLL
            weight_t pr_r = P[r][c].real();
            weight_t pr_i = P[r][c].imag();
            weight_t xr   = x[c].real();
            weight_t xi   = x[c].imag();

            sum_r += pr_r * xr - pr_i * xi;
            sum_i += pr_r * xi + pr_i * xr;
        }
        pi[r].real(sum_r);
        pi[r].imag(sum_i);
    }
}

// Compute gain vector: k = pi / (mu + x^H * pi)
void compute_gain(sc16* x, weight_cplx* pi, error_T mu, weight_cplx* k) {
    #pragma HLS INLINE
    error_T u_pi_quad = 0;
    quad_loop: for (int i = 0; i < NUM_WEIGHTS; i++) {
        #pragma HLS UNROLL
        u_pi_quad += x[i].real() * pi[i].real() + x[i].imag() * pi[i].imag();
    }

    error_T denom = mu + u_pi_quad;
    if (denom == error_T(0)) {
        denom = error_T(1e-8); // Safeguard against zero division
    }

    gain_loop: for (int i = 0; i < NUM_WEIGHTS; i++) {
        #pragma HLS UNROLL
        weight_t div_r, div_i;
        div_round_pow2(pi[i].real(), denom, div_r);
        div_round_pow2(pi[i].imag(), denom, div_i);
        k[i].real(div_r);
        k[i].imag(div_i);
    }
}

void update_p_matrix(weight_cplx* k, weight_cplx* pi, error_T mu, weight_cplx P[NUM_WEIGHTS][NUM_WEIGHTS]) {
    #pragma HLS INLINE
    p_row_loop: for (int r = 0; r < NUM_WEIGHTS; r++) {
        #pragma HLS UNROLL
        p_col_loop: for (int c = 0; c < NUM_WEIGHTS; c++) {
            #pragma HLS UNROLL
            weight_t outer_r = k[r].real() * pi[c].real() + k[r].imag() * pi[c].imag();
            weight_t outer_i = k[r].imag() * pi[c].real() - k[r].real() * pi[c].imag();

            weight_t p_new_r; 
            weight_t p_new_i;
            div_round_pow2((P[r][c].real() - outer_r), mu, p_new_r);
            div_round_pow2((P[r][c].imag() - outer_i), mu, p_new_i);
            
            P[r][c].real(p_new_r);
            P[r][c].imag(p_new_i);
        }
    }
}

void weighted_rls_module(axis_stream d_in,
                      axis_stream_multi X_in[NUM_X_IN_CHAN],
                      axis_stream output,
                     ap_ufixed<32,0,AP_TRN, AP_SAT> lambda_in,
                    weight_cplx (&w_out)[NUM_WEIGHTS]){
PIPELINE

// port level variables
#pragma HLS INTERFACE mode=axis port=d_in
#pragma HLS INTERFACE mode=axis port=X_in
#pragma HLS INTERFACE mode=axis port=output
#pragma HLS INTERFACE mode=ap_none port=lambda_in
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

// algorithm variables
// weight vector
static weight_cplx w[NUM_WEIGHTS]={};
weight_cplx w_local[NUM_WEIGHTS];
#pragma HLS ARRAY_PARTITION variable=w complete
#pragma HLS DEPENDENCE variable=w inter false
#pragma HLS ARRAY_PARTITION variable=w_local complete

// RLS inverse cov matrix
static weight_cplx P[NUM_WEIGHTS][NUM_WEIGHTS];
weight_cplx P_local[NUM_WEIGHTS][NUM_WEIGHTS];
#pragma HLS ARRAY_PARTITION variable=P complete
#pragma HLS DEPENDENCE variable=P inter false
#pragma HLS ARRAY_PARTITION variable=P_local complete
const float REG_PARAM = 10.0;
const weight_t del_inv = weight_t(1.0 / REG_PARAM);
static bool P_init = false;
if (!P_init) {
    init_p_r: for (int r = 0; r < NUM_WEIGHTS; r++) {
        #pragma HLS UNROLL
        init_p_c: for (int c = 0; c < NUM_WEIGHTS; c++) {
            #pragma HLS UNROLL
            if (r == c) {
                P[r][c] = weight_cplx(del_inv, weight_t(0));
            } else {
                P[r][c] = weight_cplx(weight_t(0), weight_t(0));
            }
        }
    }
    P_init = true;
}


// RLS pi and gain k
weight_cplx pi[NUM_WEIGHTS];
weight_cplx k[NUM_WEIGHTS];

error_cplx y, e;
error_T lambda=lambda_in;




// read w into w_local: explicit read from static variable
w_read_loop: for(int i=0; i<NUM_WEIGHTS; i++){
    #pragma HLS UNROLL
    w_local[i]=w[i];
}
P_read_r: for (int r = 0; r < NUM_WEIGHTS; r++) {
    #pragma HLS UNROLL
    P_read_c: for (int c = 0; c < NUM_WEIGHTS; c++) {
        #pragma HLS UNROLL
        P_local[r][c] = P[r][c];
    }
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

// Algorithm function calls
// filter estimate
y = stap_filter(X, w_local); 
// error
e.real(d_tmp.data.real()-y.real());
e.imag(d_tmp.data.imag()-y.imag());

// WRLS weight update
compute_pi(X, P_local, pi);
compute_gain(X, pi, lambda, k);
update_weights(e, k, w_local);
update_p_matrix(k, pi, lambda, P_local);

// store w_local and P_local in static variables and outputs
w_store_loop: for (int i = 0; i < NUM_WEIGHTS; i++) {
    #pragma HLS UNROLL
    w[i]       = w_local[i];
    w_out[i]   = w_local[i];
}

P_store_r: for (int r = 0; r < NUM_WEIGHTS; r++) {
    #pragma HLS UNROLL
    P_store_c: for (int c = 0; c < NUM_WEIGHTS; c++) {
        #pragma HLS UNROLL
        P[r][c] = P_local[r][c];
    }
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