#ifndef MLMS_H
#define MLMS_H

//TODO: include rfnoc_hls definitions from rfdev-envs
#include "rfnoc_hls.h"
#include "hls_math.h"


// Algorithm Config
#define FIR_ORDER 1
#define NUM_IN_CHAN 8
#define NUM_OUT_CHAN 1

// algorithm typing
typedef hls::stream<axis_packet> axis_stream_multi;

typedef ap_fixed<64,32,AP_TRN> weight_t;
typedef std::complex<weight_t> weight_cplx;

typedef ap_fixed<64,32, AP_TRN> error_T;
typedef std::complex<error_T> error_cplx;
typedef ap_ufixed<64,32> inner_prod;

void multi_lms_module(axis_stream d_in,
                      axis_stream_multi X_in[NUM_IN_CHAN-1],
                      axis_stream output,
                     ap_ufixed<32,0,AP_TRN, AP_SAT> mu_in);

#endif