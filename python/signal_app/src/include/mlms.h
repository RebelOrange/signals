#ifndef MLMS_MLMS_H
#define MLMS_MLMS_H

#include "rfnoc_hls/rfnoc_hls.h"
#include "hls_math.h"

#define FIR_ORDER 1

// fixed point types
//fir weight types
typedef ap_fixed<64,32,AP_TRN> weight_t;
typedef std::complex<weight_t> weight_cplx;
typedef ap_ufixed<1,1> bit_flag;

//error types
typedef ap_fixed<64,32,AP_TRN> error_T;
typedef std::complex<error_T> error_cplx_long;
typedef ap_ufixed<60, 32> divi;
typedef ap_ufixed<32, 32> accum;
typedef ap_ufixed<33, 1> rem;

#endif //MLMS_MLMS_H

/*

// RFNoC SC16 types
// **16 bit integer
// **round to zero 
// **saturate bit overflow
typedef ap_fixed<16,16,AP_RND_ZERO,AP_SAT> int16;
typedef std::complex<int16> sc16;

// RFNoC Payload axis interface
// ** packets are sc16
// ** helper reference type for readability
typedef hls::axis<sc16,0,0,0> axis_packet;
typedef hls::stream<axis_packet>& axis_stream;
*/
