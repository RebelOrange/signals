#ifndef MLMS_H
#define MLMS_H

#define PRAGMA_STR(x) #x
#define PRAGMA(x) _Pragma(PRAGMA_STR(x))

//TODO: include rfnoc_hls definitions from rfdev-envs
#include "rfnoc_hls.h"
#include "hls_math.h"

// HLS config (performance options)
#define TARGET_II 0


#define UNROLL_SPATIAL 1
#define SPATIAL_FACTOR 0
#define UNROLL_TIME 1
#define TIME_FACTOR 3

#if TARGET_II == 0
    #define PIPELINE PRAGMA(HLS PIPELINE style=flp)
#elif TARGET_II >=1
    #define PIPELINE PRAGMA(HLS PIPELINE style=flp II=TARGET_II)
#else
    #define PIPELINE
#endif

#if UNROLL_SPATIAL
    #if SPATIAL_FACTOR == 0
        #define SPATIAL_UNROLL PRAGMA(HLS UNROLL)
    #elif SPATIAL_FACTOR >= 1
        #define SPATIAL_UNROLL PRAGMA(HLS UNROLL factor=SPATIAL_FACTOR)
    #else
        #define SPATIAL_UNROLL
    #endif
#else
    #define SPATIAL_UNROLL
#endif

#if UNROLL_TIME
    #if TIME_FACTOR == 0
        #define TIME_UNROLL PRAGMA(HLS UNROLL)
    #elif TIME_FACTOR >= 1
        #define TIME_UNROLL PRAGMA(HLS UNROLL factor=TIME_FACTOR)
    #else
        #define TIME_UNROLL
    #endif
#else
    #define TIME_UNROLL
#endif

// Algorithm Config
#define FIR_ORDER 3
#define NUM_D_IN_CHAN 1
#define NUM_X_IN_CHAN 7
#define NUM_WEIGHTS (NUM_X_IN_CHAN * FIR_ORDER)
#define NUM_OUT_CHAN 1

// algorithm typing
typedef hls::stream<axis_packet> axis_stream_multi;

typedef ap_fixed<64,32,AP_TRN> weight_t;
typedef std::complex<weight_t> weight_cplx;

typedef ap_fixed<64,32, AP_TRN> error_T;
typedef std::complex<error_T> error_cplx;
typedef ap_ufixed<64,32> inner_prod;

void multi_lms_module(axis_stream d_in,
                      axis_stream_multi X_in[NUM_X_IN_CHAN],
                      axis_stream output,
                     ap_ufixed<32,0,AP_TRN, AP_SAT> mu_in);

#endif