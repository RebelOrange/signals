#ifndef MLMS_TB_HELPER_H
#define MLMS_TB_HELPER_H

#include <iostream>
#include <sstream>
#include <fstream>
#include <vector>
#include <string>
#include "mlms.h"

struct SampleRow{
    sc16 aux[8];
};

class HLS_CSV_Handler {
    public:
        static std::vector<SampleRow> load_csv(const std::string& filepath) {
            std::vector<SampleRow> dataset;
            std::ifstream file(filepath);

            if (!file.is_open()){
                std::cerr << "CSIM ERROR: could not open file  for reading: " << filepath << std::endl;
                return dataset;
            }

            std::string line;
            std::getline(file,line);

            while(std::getline(file, line)){
                if (line.empty()) continue;
                std::stringstream ss(line);
                std::string token;
                SampleRow row;

                for (int i=0; i <8; ++i){
                    std::getline(ss, token, ','); int ar = std::stoi(token);
                    std::getline(ss, token, ','); int ai = std::stoi(token);
                    row.aux[i] = sc16(ar, ai);
                }
                dataset.push_back(row);
            }
            file.close();
            std::cout << "CSIM INFO Loaded " << dataset.size() << " samples from " << filepath << std::endl;
            return dataset;
        }

        static void populate_streams(const std::vector<SampleRow>& dataset,
                                    axis_stream_multi aux_in[8],
                                    size_t samples_per_packet){
            size_t n = dataset.size();

            for (size_t k=0; k<n; ++k){
                bool is_last = ((k+1)%samples_per_packet) || (k== n-1);
                for (int i=0; i < 8; ++i){
                    axis_packet a_pkt;
                    a_pkt.data = dataset[k].aux[i];
                    a_pkt.last = is_last ? 1:0;
                    a_pkt.keep = -1;
                    a_pkt.strb = -1;
                    aux_in[i].write(a_pkt);
                }
            }
        }

        static void save_output_csv(const std::string& filepath,
                                    axis_stream& output,
                                    size_t sample_count,
                                    size_t samples_per_packet){
            std::ofstream file(filepath);
            if(!file.is_open()){
                std::cerr << "CSIM ERROR: could not open file for writing: " << filepath << std::endl;
                return;
            }

            file << "csim_r,csim_i\n";
            for (size_t k=0; k<sample_count; ++k){    
                axis_packet pkt;
                output.read(pkt);

                file << pkt.data.real().to_int() << ","
                    << pkt.data.imag().to_int() << "\n";
            }
            file.close();
            std::cout <<"[CSIM INFO] Wrote" << sample_count << " output samples to " << filepath <<std::endl;
        }       
};

#endif