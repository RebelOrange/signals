//
// Created by user on 8/27/26.
//
#include "../include/mlms.h"

error_cplx_long spatial_filter(sc16* x, weight_cplx* w){
#pragma HLS INLINE
    error_cplx_long y;
    // fir
    error_T a_r=0;
    error_T a_i=0;
    for (int i=0; i<7; i++){
#pragma HLS UNROLL
        a_r += x[i].real()*w[i].real() - x[i].imag()*(-w[i].imag());
        a_i += x[i].real()*(-w[i].imag()) + x[i].imag()*w[i].real();
    }
    y.real(a_r);
    y.imag(a_i);
    return y;
}

void update_weights(error_T e_r, error_T e_i, sc16* x, weight_cplx (&w)[7]){
#pragma HLS INLINE
    error_T mu = 1;

    for (int i = 0; i<7; i++){
#pragma HLS UNROLL
        weight_t w_delta_real = mu*(x[i].real()*e_r + x[i].imag()*e_i);
        weight_t w_delta_imag = mu*(x[i].imag()*e_r - x[i].real()*e_i);
        w[i].real(w[i].real()+w_delta_real);
        w[i].imag(w[i].imag()+w_delta_imag);
    }
}

// TODO: maybe use struct on interface?
void mlms_module(axis_stream main_in,
                 axis_stream aux_in[7],
                 axis_stream output){
#pragma HLS PIPELINE style=flp

#pragma HLS INTERFACE mode=axis port=main_in
#pragma HLS INTERFACE mode=axis port=aux_in
#pragma HLS INTERFACE mode=axis port=output
#pragma HLS INTERFACE mode=ap_ctrl_none port=return

    // axis packet declaration
    axis_packet main_tmp, output_tmp;
    axis_packet aux_tmp[7];

    // local variables
    sc16 X[7];
    error_cplx_long y;
    error_cplx_long e;
    static weight_cplx w[7]={};

    // read channels
    main_in.read(main_tmp);
    for (int i=0; i<7; i++){
#pragma HLS UNROLL
        aux_in[i].read(aux_tmp[i]);
        X[i] = aux_tmp[i].data;
    }


    y = spatial_filter(X, w);
    e.real(main_tmp.data.real()-y.real());
    e.imag(main_tmp.data.imag()-y.imag());
    update_weights(e.real(), e.imag(), X, w);


    output_tmp.data.real(e.real());
    output_tmp.data.imag(e.imag());

    // sideband signals
    output_tmp.keep = main_tmp.keep;
    output_tmp.strb = main_tmp.strb;
    output_tmp.last = main_tmp.last;
    output.write(output_tmp);
}
