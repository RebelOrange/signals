#include <iostream>
#include <vector>
#include "../include/tb_helper.h"
#include "../include/mlms.h"

int main(int argc, char* argv[]) {
    std::cout << "CSIM INFO argc = " <<argc<<std::endl;
    for (int i=0; i<argc; ++i){
        std::cout<< "CSIM INFO argv["<<i<<"] = '"<<argv[i] << "'" <<std::endl;
    }

    ap_ufixed<32,0,AP_TRN,AP_SAT> mu = 0.01f;
    if (argc>1){
        try{
            mu = std::stof(argv[1]);
        } catch(const std::invalid_argument& e){
            std::cerr <<"CSIM WARNING Invalid float arg '" << argv[1]
                        << "'. Falling back to default mu = " << mu <<std::endl;
        } catch(const std::out_of_range& e){
            std::cerr <<"CSIM WARNING Float out of range  '" << argv[1]
                        << "'. Falling back to default mu = " << mu <<std::endl;
        }
    }

    // load input data from CSV
    std::string folder_path = "/opt/rfdev-envs/sim_data/signals_app/";
    std::string input_csv = folder_path + "input_iq.csv";
    std::string output_csv = folder_path + "/vitis/csim_iq_output.csv";

    std::cout << "CSIM Starting simulation..." <<std::endl;
    std::cout << "CSIM Executing with parameter mu = " << mu << std::endl;
    
    std::vector<SampleRow> dataset = HLS_CSV_Handler::load_csv(input_csv);
    size_t num_samples = dataset.size();
    size_t SAMPLES_PER_PACKET = 64;

    if(num_samples == 0){
        std::cerr << "CSIM FATAL No samples loaded. Aborting testbench." << std::endl;
        return 1;
    }

    axis_stream_multi aux_in[8];
    axis_stream_multi output;
    
    HLS_CSV_Handler::populate_streams(dataset, aux_in, SAMPLES_PER_PACKET);

    std::cout << "CSIM Passing data to module..." << std::endl;

    weight_cplx w[NUM_WEIGHTS];
    for (size_t k=0; k<num_samples; ++k){
        multi_lms_module(aux_in[0], &aux_in[1], output, mu,w);
    }

    HLS_CSV_Handler::save_output_csv(output_csv, output, num_samples, SAMPLES_PER_PACKET);

    std::cout << "CSIM C-Simulation complete." << std::endl;

    return 0;
}