#include "../include/mlms.h"
#ifndef __SYNTHESIS__
#include <fstream>
#include <iomanip>
#include <iostream>
#endif

void multi_lms_module(axis_stream d_in,
                      axis_stream_multi X_in[NUM_IN_CHAN-1],
                      axis_stream output,
                     ap_ufixed<32,0,AP_TRN, AP_SAT> mu_in){
#pragma HLS PIPELINE style=flp II=1

#pragma HLS INTERFACE mode=axis port=d_in
#pragma HLS INTERFACE mode=axis port=X_in
#pragma HLS INTERFACE mode=axis port=output
#pragma HLS INTERFACE mode=ap_ctrl_none port=return

axis_packet d_tmp, out_tmp;
axis_packet X_tmp[NUM_IN_CHAN-1];
#pragma HLS ARRAY_PARTITION variable=X_tmp complete

sc16 X[7];


// read inputs
d_in.read(d_tmp);
for (int i=0; i<NUM_IN_CHAN-1; i++){
    #pragma HLS UNROLL
    X_in[i].read(X_tmp[i]);
    X[i] = X_tmp[i].data;
}

#ifndef __SYNTHESIS__
#endif

out_tmp.data.real(d_tmp.data.real()-X[0].real());
out_tmp.data.imag(d_tmp.data.imag()-X[0].imag());

out_tmp.keep = d_tmp.keep;
out_tmp.strb = d_tmp.strb;
out_tmp.last = d_tmp.last;
output.write(out_tmp);


                     }