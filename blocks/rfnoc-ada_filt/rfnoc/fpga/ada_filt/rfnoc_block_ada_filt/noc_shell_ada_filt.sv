//
// Copyright 2026 Ettus Research, a National Instruments Brand
//
// SPDX-License-Identifier: LGPL-3.0-or-later
//
// Module: noc_shell_ada_filt
//
// Description:
//
//   This is a tool-generated NoC-shell for the ada_filt block.
//   See the RFNoC specification for more information about NoC shells.
//
// Parameters:
//
//   THIS_PORTID  : Control crossbar port to which this block is connected
//   CHDR_W       : AXIS-CHDR data bus width
//   CTRL_CLK_IDX : The index of the control clock for this block. This is used
//                  to populate the backend interface, from where UHD can query
//                  the clock index and thus auto-deduct which clock is used.
//   TB_CLK_IDX   : The index of the timebase clock for this block. This is used
//                  to populate the backend interface, from where UHD can query
//                  the clock index and thus auto-deduct which clock is used.
//   MTU          : Maximum transmission unit (i.e., maximum packet size in
//                  CHDR words is 2**MTU).
//

`default_nettype none


module noc_shell_ada_filt #(
  parameter [9:0] THIS_PORTID     = 10'd0,
  parameter       CHDR_W          = 64,
  parameter [5:0] CTRL_CLK_IDX    = 6'h3F,
  parameter [5:0] TB_CLK_IDX      = 6'h3F,
  parameter [5:0] MTU             = 10,
  parameter       IN_PORTS        = 8
) (
  //---------------------
  // Framework Interface
  //---------------------

  // RFNoC Framework Clocks
  input  wire rfnoc_chdr_clk,
  input  wire rfnoc_ctrl_clk,
  input  wire radio_clk,

  // NoC Shell Generated Resets
  output wire rfnoc_chdr_rst,
  output wire rfnoc_ctrl_rst,
  output wire radio_rst,

  // AXIS-CHDR Input Ports (from framework)
  input  wire [(0+IN_PORTS)*CHDR_W-1:0] s_rfnoc_chdr_tdata,
  input  wire [(0+IN_PORTS)-1:0]        s_rfnoc_chdr_tlast,
  input  wire [(0+IN_PORTS)-1:0]        s_rfnoc_chdr_tvalid,
  output wire [(0+IN_PORTS)-1:0]        s_rfnoc_chdr_tready,
  // AXIS-CHDR Output Ports (to framework)
  output wire [(8)*CHDR_W-1:0] m_rfnoc_chdr_tdata,
  output wire [(8)-1:0]        m_rfnoc_chdr_tlast,
  output wire [(8)-1:0]        m_rfnoc_chdr_tvalid,
  input  wire [(8)-1:0]        m_rfnoc_chdr_tready,

  // AXIS-Ctrl Control Input Port (from framework)
  input  wire [31:0]           s_rfnoc_ctrl_tdata,
  input  wire                  s_rfnoc_ctrl_tlast,
  input  wire                  s_rfnoc_ctrl_tvalid,
  output wire                  s_rfnoc_ctrl_tready,
  // AXIS-Ctrl Control Output Port (to framework)
  output wire [31:0]           m_rfnoc_ctrl_tdata,
  output wire                  m_rfnoc_ctrl_tlast,
  output wire                  m_rfnoc_ctrl_tvalid,
  input  wire                  m_rfnoc_ctrl_tready,

  //---------------------
  // Client Interface
  //---------------------

  // CtrlPort Clock and Reset
  output wire               ctrlport_clk,
  output wire               ctrlport_rst,
  // CtrlPort Master
  output wire               m_ctrlport_req_wr,
  output wire               m_ctrlport_req_rd,
  output wire [19:0]        m_ctrlport_req_addr,
  output wire [31:0]        m_ctrlport_req_data,
  input  wire               m_ctrlport_resp_ack,
  input  wire [31:0]        m_ctrlport_resp_data,


  // AXI-Stream Data Clock and Reset
  output wire               axis_data_clk,
  output wire               axis_data_rst,
  // Data Stream to User Logic: in
  output wire [IN_PORTS*32*1-1:0]   m_in_axis_tdata,
  output wire [IN_PORTS*1-1:0]      m_in_axis_tkeep,
  output wire [IN_PORTS-1:0]        m_in_axis_tlast,
  output wire [IN_PORTS-1:0]        m_in_axis_tvalid,
  input  wire [IN_PORTS-1:0]        m_in_axis_tready,
  output wire [IN_PORTS*64-1:0]     m_in_axis_ttimestamp,
  output wire [IN_PORTS-1:0]        m_in_axis_thas_time,
  output wire [IN_PORTS*16-1:0]     m_in_axis_tlength,
  output wire [IN_PORTS-1:0]        m_in_axis_teov,
  output wire [IN_PORTS-1:0]        m_in_axis_teob,
  // Data Stream from User Logic: out_0
  input  wire [32*1-1:0]    s_out_0_axis_tdata,
  input  wire [0:0]         s_out_0_axis_tkeep,
  input  wire               s_out_0_axis_tlast,
  input  wire               s_out_0_axis_tvalid,
  output wire               s_out_0_axis_tready,
  input  wire [63:0]        s_out_0_axis_ttimestamp,
  input  wire               s_out_0_axis_thas_time,
  input  wire [15:0]        s_out_0_axis_tlength,
  input  wire               s_out_0_axis_teov,
  input  wire               s_out_0_axis_teob,
  // Data Stream from User Logic: out_1
  input  wire [7*32*1-1:0]   s_out_1_axis_tdata,
  input  wire [7*1-1:0]      s_out_1_axis_tkeep,
  input  wire [7-1:0]        s_out_1_axis_tlast,
  input  wire [7-1:0]        s_out_1_axis_tvalid,
  output wire [7-1:0]        s_out_1_axis_tready,
  input  wire [7*64-1:0]     s_out_1_axis_ttimestamp,
  input  wire [7-1:0]        s_out_1_axis_thas_time,
  input  wire [7*16-1:0]     s_out_1_axis_tlength,
  input  wire [7-1:0]        s_out_1_axis_teov,
  input  wire [7-1:0]        s_out_1_axis_teob,

  // RFNoC Backend Interface
  input  wire [511:0]       rfnoc_core_config,
  output wire [511:0]       rfnoc_core_status
);

  localparam CTRL_FIFO_SIZE_LOG2     = $clog2(32);
  localparam CTRL_OUT_FIFO_SIZE_LOG2 = $clog2(2);

  //---------------------------------------------------------------------------
  //  Backend Interface
  //---------------------------------------------------------------------------
  wire         data_i_flush_en;
  wire [31:0]  data_i_flush_timeout;
  wire [63:0]  data_i_flush_active;
  wire [63:0]  data_i_flush_done;
  wire         data_o_flush_en;
  wire [31:0]  data_o_flush_timeout;
  wire [63:0]  data_o_flush_active;
  wire [63:0]  data_o_flush_done;

  backend_iface #(
    .NOC_ID        (32'h341A0B10),
    .NUM_DATA_I    (0+IN_PORTS),
    .NUM_DATA_O    (8),
    .CTRL_FIFOSIZE (CTRL_FIFO_SIZE_LOG2),
    .MTU           (MTU)
  ) backend_iface_i (
    .rfnoc_chdr_clk       (rfnoc_chdr_clk),
    .rfnoc_chdr_rst       (rfnoc_chdr_rst),
    .rfnoc_ctrl_clk       (rfnoc_ctrl_clk),
    .rfnoc_ctrl_rst       (rfnoc_ctrl_rst),
    .data_i_flush_en      (data_i_flush_en),
    .data_i_flush_timeout (data_i_flush_timeout),
    .data_i_flush_active  (data_i_flush_active),
    .data_i_flush_done    (data_i_flush_done),
    .data_o_flush_en      (data_o_flush_en),
    .data_o_flush_timeout (data_o_flush_timeout),
    .data_o_flush_active  (data_o_flush_active),
    .data_o_flush_done    (data_o_flush_done),
    .rfnoc_core_config    (rfnoc_core_config),
    .rfnoc_core_status    (rfnoc_core_status)
  );

  //---------------------------------------------------------------------------
  //  Reset Generation
  //---------------------------------------------------------------------------

  wire radio_rst_pulse;

  pulse_synchronizer #(.MODE ("POSEDGE")) pulse_synchronizer_radio (
    .clk_a(rfnoc_chdr_clk), .rst_a(1'b0), .pulse_a (rfnoc_chdr_rst), .busy_a (),
    .clk_b(radio_clk), .pulse_b (radio_rst_pulse)
  );

  pulse_stretch_min #(.LENGTH(32)) pulse_stretch_min_radio (
    .clk(radio_clk), .rst(1'b0),
    .pulse_in(radio_rst_pulse), .pulse_out(radio_rst)
  );

  //---------------------------------------------------------------------------
  //  Control Path
  //---------------------------------------------------------------------------

  assign ctrlport_clk = axis_data_clk;
  assign ctrlport_rst = axis_data_rst;

  ctrlport_endpoint #(
    .THIS_PORTID        (THIS_PORTID),
    .SYNC_CLKS          (0),
    .AXIS_CTRL_MST_EN   (0),
    .AXIS_CTRL_SLV_EN   (1),
    .SLAVE_FIFO_SIZE    (CTRL_FIFO_SIZE_LOG2),
    .CTRL_OUT_FIFO_SIZE (CTRL_OUT_FIFO_SIZE_LOG2)
  ) ctrlport_endpoint_i (
    .rfnoc_ctrl_clk            (rfnoc_ctrl_clk),
    .rfnoc_ctrl_rst            (rfnoc_ctrl_rst),
    .ctrlport_clk              (ctrlport_clk),
    .ctrlport_rst              (ctrlport_rst),
    .s_rfnoc_ctrl_tdata        (s_rfnoc_ctrl_tdata),
    .s_rfnoc_ctrl_tlast        (s_rfnoc_ctrl_tlast),
    .s_rfnoc_ctrl_tvalid       (s_rfnoc_ctrl_tvalid),
    .s_rfnoc_ctrl_tready       (s_rfnoc_ctrl_tready),
    .m_rfnoc_ctrl_tdata        (m_rfnoc_ctrl_tdata),
    .m_rfnoc_ctrl_tlast        (m_rfnoc_ctrl_tlast),
    .m_rfnoc_ctrl_tvalid       (m_rfnoc_ctrl_tvalid),
    .m_rfnoc_ctrl_tready       (m_rfnoc_ctrl_tready),
    .m_ctrlport_req_wr         (m_ctrlport_req_wr),
    .m_ctrlport_req_rd         (m_ctrlport_req_rd),
    .m_ctrlport_req_addr       (m_ctrlport_req_addr),
    .m_ctrlport_req_data       (m_ctrlport_req_data),
    .m_ctrlport_req_byte_en    (),
    .m_ctrlport_req_has_time   (),
    .m_ctrlport_req_time       (),
    .m_ctrlport_resp_ack       (m_ctrlport_resp_ack),
    .m_ctrlport_resp_status    (2'b0),
    .m_ctrlport_resp_data      (m_ctrlport_resp_data),
    .s_ctrlport_req_wr         (1'b0),
    .s_ctrlport_req_rd         (1'b0),
    .s_ctrlport_req_addr       (20'b0),
    .s_ctrlport_req_portid     (10'b0),
    .s_ctrlport_req_rem_epid   (16'b0),
    .s_ctrlport_req_rem_portid (10'b0),
    .s_ctrlport_req_data       (32'b0),
    .s_ctrlport_req_byte_en    (4'hF),
    .s_ctrlport_req_has_time   (1'b0),
    .s_ctrlport_req_time       (64'b0),
    .s_ctrlport_resp_ack       (),
    .s_ctrlport_resp_status    (),
    .s_ctrlport_resp_data      ()
  );

  //---------------------------------------------------------------------------
  //  Data Path
  //---------------------------------------------------------------------------

  genvar i;

  assign axis_data_clk = radio_clk;
  assign axis_data_rst = radio_rst;

  //---------------------
  // Input Data Paths
  //---------------------

  for (i = 0; i < IN_PORTS; i = i + 1) begin: gen_input_in
    chdr_to_axis_data #(
      .CHDR_W         (CHDR_W),
      .ITEM_W         (32),
      .NIPC           (1),
      .SYNC_CLKS      (0),
      .INFO_FIFO_SIZE ($clog2(2)),
      .PYLD_FIFO_SIZE ($clog2(32))
    ) chdr_to_axis_data_in_in (
      .axis_chdr_clk      (rfnoc_chdr_clk),
      .axis_chdr_rst      (rfnoc_chdr_rst),
      .axis_data_clk      (axis_data_clk),
      .axis_data_rst      (axis_data_rst),
      .s_axis_chdr_tdata  (s_rfnoc_chdr_tdata[((0+i)*CHDR_W)+:CHDR_W]),
      .s_axis_chdr_tlast  (s_rfnoc_chdr_tlast[0+i]),
      .s_axis_chdr_tvalid (s_rfnoc_chdr_tvalid[0+i]),
      .s_axis_chdr_tready (s_rfnoc_chdr_tready[0+i]),
      .m_axis_tdata       (m_in_axis_tdata[(32*1)*i+:(32*1)]),
      .m_axis_tkeep       (m_in_axis_tkeep[1*i+:1]),
      .m_axis_tlast       (m_in_axis_tlast[i]),
      .m_axis_tvalid      (m_in_axis_tvalid[i]),
      .m_axis_tready      (m_in_axis_tready[i]),
      .m_axis_ttimestamp  (m_in_axis_ttimestamp[64*i+:64]),
      .m_axis_thas_time   (m_in_axis_thas_time[i]),
      .m_axis_tlength     (m_in_axis_tlength[16*i+:16]),
      .m_axis_teov        (m_in_axis_teov[i]),
      .m_axis_teob        (m_in_axis_teob[i]),
      .flush_en           (data_i_flush_en),
      .flush_timeout      (data_i_flush_timeout),
      .flush_active       (data_i_flush_active[0+i]),
      .flush_done         (data_i_flush_done[0+i])
    );
  end

  //---------------------
  // Output Data Paths
  //---------------------

  axis_data_to_chdr #(
    .CHDR_W          (CHDR_W),
    .ITEM_W          (32),
    .NIPC            (1),
    .SYNC_CLKS       (0),
    .INFO_FIFO_SIZE  ($clog2(2)),
    .PYLD_FIFO_SIZE  ($clog2(32)),
    .MTU             (MTU),
    .SIDEBAND_AT_END (1)
  ) axis_data_to_chdr_out_out_0 (
    .axis_chdr_clk      (rfnoc_chdr_clk),
    .axis_chdr_rst      (rfnoc_chdr_rst),
    .axis_data_clk      (axis_data_clk),
    .axis_data_rst      (axis_data_rst),
    .m_axis_chdr_tdata  (m_rfnoc_chdr_tdata[(0)*CHDR_W+:CHDR_W]),
    .m_axis_chdr_tlast  (m_rfnoc_chdr_tlast[0]),
    .m_axis_chdr_tvalid (m_rfnoc_chdr_tvalid[0]),
    .m_axis_chdr_tready (m_rfnoc_chdr_tready[0]),
    .s_axis_tdata       (s_out_0_axis_tdata),
    .s_axis_tkeep       (s_out_0_axis_tkeep),
    .s_axis_tlast       (s_out_0_axis_tlast),
    .s_axis_tvalid      (s_out_0_axis_tvalid),
    .s_axis_tready      (s_out_0_axis_tready),
    .s_axis_ttimestamp  (s_out_0_axis_ttimestamp),
    .s_axis_thas_time   (s_out_0_axis_thas_time),
    .s_axis_tlength     (s_out_0_axis_tlength),
    .s_axis_teov        (s_out_0_axis_teov),
    .s_axis_teob        (s_out_0_axis_teob),
    .flush_en           (data_o_flush_en),
    .flush_timeout      (data_o_flush_timeout),
    .flush_active       (data_o_flush_active[0]),
    .flush_done         (data_o_flush_done[0])
  );

  for (i = 0; i < 7; i = i + 1) begin: gen_output_out_1
    axis_data_to_chdr #(
      .CHDR_W          (CHDR_W),
      .ITEM_W          (32),
      .NIPC            (1),
      .SYNC_CLKS       (0),
      .INFO_FIFO_SIZE  ($clog2(2)),
      .PYLD_FIFO_SIZE  ($clog2(32)),
      .MTU             (MTU),
      .SIDEBAND_AT_END (1)
    ) axis_data_to_chdr_out_out_1 (
      .axis_chdr_clk      (rfnoc_chdr_clk),
      .axis_chdr_rst      (rfnoc_chdr_rst),
      .axis_data_clk      (axis_data_clk),
      .axis_data_rst      (axis_data_rst),
      .m_axis_chdr_tdata  (m_rfnoc_chdr_tdata[(1+i)*CHDR_W+:CHDR_W]),
      .m_axis_chdr_tlast  (m_rfnoc_chdr_tlast[1+i]),
      .m_axis_chdr_tvalid (m_rfnoc_chdr_tvalid[1+i]),
      .m_axis_chdr_tready (m_rfnoc_chdr_tready[1+i]),
      .s_axis_tdata       (s_out_1_axis_tdata[(32*1)*i+:(32*1)]),
      .s_axis_tkeep       (s_out_1_axis_tkeep[1*i+:1]),
      .s_axis_tlast       (s_out_1_axis_tlast[i]),
      .s_axis_tvalid      (s_out_1_axis_tvalid[i]),
      .s_axis_tready      (s_out_1_axis_tready[i]),
      .s_axis_ttimestamp  (s_out_1_axis_ttimestamp[64*i+:64]),
      .s_axis_thas_time   (s_out_1_axis_thas_time[i]),
      .s_axis_tlength     (s_out_1_axis_tlength[16*i+:16]),
      .s_axis_teov        (s_out_1_axis_teov[i]),
      .s_axis_teob        (s_out_1_axis_teob[i]),
      .flush_en           (data_o_flush_en),
      .flush_timeout      (data_o_flush_timeout),
      .flush_active       (data_o_flush_active[1+i]),
      .flush_done         (data_o_flush_done[1+i])
    );
  end

endmodule // noc_shell_ada_filt


`default_nettype wire
