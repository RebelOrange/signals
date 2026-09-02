//
// Reusable RFNoC CSV File I/O Helper Package
//
package rfnoc_csv_io_pkg;

  class RfnocCsvIO #(int ITEM_W = 32);

    typedef logic [ITEM_W-1:0] item_t;

    // ------------------------------------------------------------------------
    // Read 8-channel CSV into RFNoC CHDR Item Queues
    // ------------------------------------------------------------------------
    static function void read_input_csv(
      input string filename,
      ref item_t ch_queues[8][$]
    );
      int file, status;
      string header_line;
      int r[8], i[8];
      item_t sample;

      file = $fopen(filename, "r");
      if (!file) begin
        $fatal(1, "[CSV ERROR] Could not open input file: %s", filename);
      end

      // Skip CSV header line
      status = $fgets(header_line, file);

      // Read row-by-row (ch0_r, ch0_i, ch1_r, ch1_i, ..., ch7_r, ch7_i)
      while (!$feof(file)) begin
        status = $fscanf(file, "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
          r[0], i[0], r[1], i[1], r[2], i[2], r[3], i[3],
          r[4], i[4], r[5], i[5], r[6], i[6], r[7], i[7]
        );

        if (status == 16) begin
          for (int ch = 0; ch < 8; ch++) begin
            // Pack Real (31:16) and Imag (15:0) into 32-bit RFNoC item
            sample = {16'(r[ch]), 16'(i[ch])};
            ch_queues[ch].push_back(sample);
          end
        end
      end

      $fclose(file);
      $display("[CSV IO] Loaded %0d samples across 8 channels from '%s'", 
               ch_queues[0].size(), filename);
    endfunction

    // ------------------------------------------------------------------------
    // Write RFNoC Output Queue to CSV
    // ------------------------------------------------------------------------
    static function void write_output_csv(
      input string filename,
      ref item_t out_queue[$],
      input int spp
    );
      int file;
      int packet_id = 0;
      int sample_in_pkt = 0;
      int total_samples;
      item_t item;
      logic signed [15:0] out_r, out_i;
      bit is_last;

      file = $fopen(filename, "w");
      if (!file) begin
        $fatal(1, "[CSV ERROR] Could not open output file: %s", filename);
      end

      // Output Header
      $fdisplay(file, "packet_id,sample_in_pkt,output_r,output_i,tlast");

      total_samples = out_queue.size();

      for (int k = 0; k < total_samples; k++) begin
        item  = out_queue[k];
        out_r = item[31:16]; // Unpack Real
        out_i = item[15:0];  // Unpack Imag

        is_last = ((sample_in_pkt == spp - 1) || (k == total_samples - 1));

        $fdisplay(file, "%0d,%0d,%0d,%0d,%0d", 
                  packet_id, sample_in_pkt, out_r, out_i, is_last);

        sample_in_pkt++;
        if (is_last) begin
          packet_id++;
          sample_in_pkt = 0;
        end
      end

      $fclose(file);
      $display("[CSV IO] Exported %0d output samples (%0d packets) to '%s'", 
               total_samples, packet_id, filename);
    endfunction

  endclass

endpackage : rfnoc_csv_io_pkg