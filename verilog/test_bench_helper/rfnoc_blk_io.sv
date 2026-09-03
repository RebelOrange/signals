package rfnoc_blk_io:
  // ------------------------------------------------------------------------
  // Receive All Expected Packets from RFNoC BFM
  // ------------------------------------------------------------------------
  task automatic recv_all_items(
    input RfnocBlockCtrlBfm #(CHDR_W, ITEM_W) blk_ctrl,
    input int          port,
    input int          total_samples,
    input int          spp,
    output item_queue_t out_queue
  );
    item_queue_t  pkt_items;
    chdr_word_t   rx_metadata[$];
    packet_info_t rx_pkt_info;
    int num_packets = total_samples / spp;

    out_queue.delete();

    for (int p = 0; p < num_packets; p++) begin
      pkt_items.delete();
      blk_ctrl.recv_items(port, pkt_items, rx_metadata, rx_pkt_info);
      
      foreach (pkt_items[i]) begin
        out_queue.push_back(pkt_items[i]);
      end
    end
    
    // Print summary to terminal command line
    $display("[RFNoC BFM] Port %0d: Received %0d packets (%0d total samples | SPP = %0d)", 
             port, num_packets, out_queue.size(), spp);
  endtask
endpackage : rfnoc_blk_io
