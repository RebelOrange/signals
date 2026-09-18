#include <ap_axi_sdata.h>
#include <hls_stream.h>
#include <complex>
#include <ap_fixed.h>

#ifndef RFNOC_HLS_H
#define RFNOC_HLS_H

typedef ap_fixed<16, 16, AP_RND_ZERO, AP_SAT> int16;
typedef std::complex<int16> sc16;

typedef hls::axis<sc16, 0, 0, 0> axis_packet;
typedef hls::stream<axis_packet> &axis_stream;

#endif