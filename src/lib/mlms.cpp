//
// Created by user on 8/27/26.
//
#include "../include/mlms.h"

error_cplx_long spatial_filter(sc16* x, weight_cplx* w){
    error_cplx_long y;
    // fir
    error_T a_r;
    error_T a_i;
    for (int i=0; i<7; i++){
        a_r += x[i].real()*w[i].real() - x[i].imag()*(-w[i].imag());
        a_i += x[i].real()*(-w[i].imag()) + x[i].imag()*w[i].real();
    }
    y.real(a_r);
    y.imag(a_i);
    return y;
}

void update_weights(error_T e_r, error_T e_i, sc16* x, weight_cplx (&w)[7]){
    error_T mu = 1;

    for (int i = 0; i<7; i++){
        weight_t w_delta_real = mu*(x[i].real()*e_r + x[i].imag()*e_i);
        weight_t w_delta_imag = mu*(x[i].imag()*e_r - x[i].real()*e_i);
        w[i].real(w[i].real()+w_delta_real);
        w[i].imag(w[i].imag()+w_delta_imag);
    }
}

// TODO: maybe use struct on interface?
void mlms_module(axis_stream main_in,
                 axis_stream a0_in,
                 axis_stream a1_in,
                 axis_stream a2_in,
                 axis_stream a3_in,
                 axis_stream a4_in,
                 axis_stream a5_in,
                 axis_stream a6_in,
                 axis_stream output){
#pragma HLS PIPELINE style=flp

#pragma HLS INTERFACE mode=axis port=main_in
#pragma HLS INTERFACE mode=axis port=a0_in
#pragma HLS INTERFACE mode=axis port=a1_in
#pragma HLS INTERFACE mode=axis port=a2_in
#pragma HLS INTERFACE mode=axis port=a3_in
#pragma HLS INTERFACE mode=axis port=a4_in
#pragma HLS INTERFACE mode=axis port=a5_in
#pragma HLS INTERFACE mode=axis port=a6_in
#pragma HLS INTERFACE mode=axis port=output
#pragma HLS INTERFACE mode=ap_ctrl_none port=return

    // axis packet declaration
    axis_packet main_tmp, output_tmp;
    axis_packet a0_tmp,a1_tmp,a2_tmp,a3_tmp,a4_tmp,a5_tmp,a6_tmp;

    // local variables
    error_cplx_long y;
    error_cplx_long e;
    static weight_cplx w[7]={};

    main_in.read(main_tmp);
    a0_in.read(a0_tmp);
    a1_in.read(a1_tmp);
    a2_in.read(a2_tmp);
    a3_in.read(a3_tmp);
    a4_in.read(a4_tmp);
    a5_in.read(a5_tmp);
    a6_in.read(a6_tmp);

    // data vector
    sc16 X[7] = {a0_tmp.data, a1_tmp.data, a2_tmp.data, a3_tmp.data, a4_tmp.data,
                 a5_tmp.data, a6_tmp.data};

    y = spatial_filter(X, w);
    e.real(main_tmp.data.real()-y.real());
    e.imag(main_tmp.data.imag()-y.imag());
    update_weights(e.real(), e.imag(), X, w);


    output_tmp.data.real(e.real());
    output_tmp.data.imag(e.imag());
    output_tmp.last = main_tmp.last;
    output.write(output_tmp);
}
