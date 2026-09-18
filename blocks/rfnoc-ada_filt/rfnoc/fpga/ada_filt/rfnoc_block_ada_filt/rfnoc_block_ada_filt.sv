//
// Copyright 2026 <author>
//
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Module: rfnoc_block_ada_filt
//
// Description:
//
//   <Add block description here>
//
// Parameters:
//
//   THIS_PORTID : Control crossbar port to which this block is connected
//   CHDR_W      : AXIS-CHDR data bus width
//   MTU         : Maximum transmission unit (i.e., maximum packet size in
//                 CHDR words is 2**MTU).
//

`default_nettype none

module rfnoc_block_ada_filt #(
  parameter [9:0] THIS_PORTID     = 10'd0,
  parameter       CHDR_W          = 64,
  parameter [5:0] MTU             = 10,
  parameter       IN_PORTS        = 8
)(
  // RFNoC Framework Clocks and Resets
  input  wire                   rfnoc_chdr_clk,
  input  wire                   rfnoc_ctrl_clk,
  input  wire                   radio_clk,
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
  // AXIS-Ctrl Input Port (from framework)
  input  wire [31:0]            s_rfnoc_ctrl_tdata,
  input  wire                   s_rfnoc_ctrl_tlast,
  input  wire                   s_rfnoc_ctrl_tvalid,
  output wire                   s_rfnoc_ctrl_tready,
  // AXIS-Ctrl Output Port (to framework)
  output wire [31:0]            m_rfnoc_ctrl_tdata,
  output wire                   m_rfnoc_ctrl_tlast,
  output wire                   m_rfnoc_ctrl_tvalid,
  input  wire                   m_rfnoc_ctrl_tready,
  // RFNoC Backend Interface
  input  wire [511:0]           rfnoc_core_config,
  output wire [511:0]           rfnoc_core_status
);

  //---------------------------------------------------------------------------
  // Signal Declarations
  //---------------------------------------------------------------------------

  // Clocks and Resets
  wire               ctrlport_clk;
  wire               ctrlport_rst;
  wire               axis_data_clk;
  wire               axis_data_rst;
  // CtrlPort Master
  wire               m_ctrlport_req_wr;
  wire               m_ctrlport_req_rd;
  wire [19:0]        m_ctrlport_req_addr;
  wire [31:0]        m_ctrlport_req_data;
  wire               m_ctrlport_resp_ack;
  wire [31:0]        m_ctrlport_resp_data;
  // Data Stream to User Logic: in
  wire [IN_PORTS*32*1-1:0]   m_in_axis_tdata;
  wire [IN_PORTS*1-1:0]      m_in_axis_tkeep;
  wire [IN_PORTS-1:0]        m_in_axis_tlast;
  wire [IN_PORTS-1:0]        m_in_axis_tvalid;
  wire [IN_PORTS-1:0]        m_in_axis_tready;
  wire [IN_PORTS*64-1:0]     m_in_axis_ttimestamp;
  wire [IN_PORTS-1:0]        m_in_axis_thas_time;
  wire [IN_PORTS*16-1:0]     m_in_axis_tlength;
  wire [IN_PORTS-1:0]        m_in_axis_teov;
  wire [IN_PORTS-1:0]        m_in_axis_teob;
  // Data Stream from User Logic: out_0
  wire [32*1-1:0]    s_out_0_axis_tdata;
  wire [0:0]         s_out_0_axis_tkeep;
  wire               s_out_0_axis_tlast;
  wire               s_out_0_axis_tvalid;
  wire               s_out_0_axis_tready;
  wire [63:0]        s_out_0_axis_ttimestamp;
  wire               s_out_0_axis_thas_time;
  wire [15:0]        s_out_0_axis_tlength;
  wire               s_out_0_axis_teov;
  wire               s_out_0_axis_teob;
  // Data Stream from User Logic: out_1
  wire [7*32*1-1:0]   s_out_1_axis_tdata;
  wire [7*1-1:0]      s_out_1_axis_tkeep;
  wire [7-1:0]        s_out_1_axis_tlast;
  wire [7-1:0]        s_out_1_axis_tvalid;
  wire [7-1:0]        s_out_1_axis_tready;
  wire [7*64-1:0]     s_out_1_axis_ttimestamp;
  wire [7-1:0]        s_out_1_axis_thas_time;
  wire [7*16-1:0]     s_out_1_axis_tlength;
  wire [7-1:0]        s_out_1_axis_teov;
  wire [7-1:0]        s_out_1_axis_teob;

  //---------------------------------------------------------------------------
  // NoC Shell
  //---------------------------------------------------------------------------

  noc_shell_ada_filt #(
    .CHDR_W              (CHDR_W),
    .THIS_PORTID         (THIS_PORTID),
    .MTU                 (MTU),
    .IN_PORTS            (IN_PORTS)
  ) noc_shell_ada_filt_i (
    //---------------------
    // Framework Interface
    //---------------------

    // Clock Inputs
    .rfnoc_chdr_clk      (rfnoc_chdr_clk),
    .rfnoc_ctrl_clk      (rfnoc_ctrl_clk),
    .radio_clk           (radio_clk),
    // Reset Outputs
    .rfnoc_chdr_rst      (),
    .rfnoc_ctrl_rst      (),
    .radio_rst           (),
    // CHDR Input Ports  (from framework)
    .s_rfnoc_chdr_tdata  (s_rfnoc_chdr_tdata),
    .s_rfnoc_chdr_tlast  (s_rfnoc_chdr_tlast),
    .s_rfnoc_chdr_tvalid (s_rfnoc_chdr_tvalid),
    .s_rfnoc_chdr_tready (s_rfnoc_chdr_tready),
    // CHDR Output Ports (to framework)
    .m_rfnoc_chdr_tdata  (m_rfnoc_chdr_tdata),
    .m_rfnoc_chdr_tlast  (m_rfnoc_chdr_tlast),
    .m_rfnoc_chdr_tvalid (m_rfnoc_chdr_tvalid),
    .m_rfnoc_chdr_tready (m_rfnoc_chdr_tready),
    // AXIS-Ctrl Input Port (from framework)
    .s_rfnoc_ctrl_tdata  (s_rfnoc_ctrl_tdata),
    .s_rfnoc_ctrl_tlast  (s_rfnoc_ctrl_tlast),
    .s_rfnoc_ctrl_tvalid (s_rfnoc_ctrl_tvalid),
    .s_rfnoc_ctrl_tready (s_rfnoc_ctrl_tready),
    // AXIS-Ctrl Output Port (to framework)
    .m_rfnoc_ctrl_tdata  (m_rfnoc_ctrl_tdata),
    .m_rfnoc_ctrl_tlast  (m_rfnoc_ctrl_tlast),
    .m_rfnoc_ctrl_tvalid (m_rfnoc_ctrl_tvalid),
    .m_rfnoc_ctrl_tready (m_rfnoc_ctrl_tready),

    //---------------------
    // Client Interface
    //---------------------

    // CtrlPort Clock and Reset
    .ctrlport_clk              (ctrlport_clk),
    .ctrlport_rst              (ctrlport_rst),
    // CtrlPort Master
    .m_ctrlport_req_wr         (m_ctrlport_req_wr),
    .m_ctrlport_req_rd         (m_ctrlport_req_rd),
    .m_ctrlport_req_addr       (m_ctrlport_req_addr),
    .m_ctrlport_req_data       (m_ctrlport_req_data),
    .m_ctrlport_resp_ack       (m_ctrlport_resp_ack),
    .m_ctrlport_resp_data      (m_ctrlport_resp_data),

    // AXI-Stream Clock and Reset
    .axis_data_clk (axis_data_clk),
    .axis_data_rst (axis_data_rst),
    // Data Stream to User Logic: in
    .m_in_axis_tdata      (m_in_axis_tdata),
    .m_in_axis_tkeep      (m_in_axis_tkeep),
    .m_in_axis_tlast      (m_in_axis_tlast),
    .m_in_axis_tvalid     (m_in_axis_tvalid),
    .m_in_axis_tready     (m_in_axis_tready),
    .m_in_axis_ttimestamp (m_in_axis_ttimestamp),
    .m_in_axis_thas_time  (m_in_axis_thas_time),
    .m_in_axis_tlength    (m_in_axis_tlength),
    .m_in_axis_teov       (m_in_axis_teov),
    .m_in_axis_teob       (m_in_axis_teob),
    // Data Stream from User Logic: out_0
    .s_out_0_axis_tdata      (s_out_0_axis_tdata),
    .s_out_0_axis_tkeep      (s_out_0_axis_tkeep),
    .s_out_0_axis_tlast      (s_out_0_axis_tlast),
    .s_out_0_axis_tvalid     (s_out_0_axis_tvalid),
    .s_out_0_axis_tready     (s_out_0_axis_tready),
    .s_out_0_axis_ttimestamp (s_out_0_axis_ttimestamp),
    .s_out_0_axis_thas_time  (s_out_0_axis_thas_time),
    .s_out_0_axis_tlength    (s_out_0_axis_tlength),
    .s_out_0_axis_teov       (s_out_0_axis_teov),
    .s_out_0_axis_teob       (s_out_0_axis_teob),
    // Data Stream from User Logic: out_1
    .s_out_1_axis_tdata      (s_out_1_axis_tdata),
    .s_out_1_axis_tkeep      (s_out_1_axis_tkeep),
    .s_out_1_axis_tlast      (s_out_1_axis_tlast),
    .s_out_1_axis_tvalid     (s_out_1_axis_tvalid),
    .s_out_1_axis_tready     (s_out_1_axis_tready),
    .s_out_1_axis_ttimestamp (s_out_1_axis_ttimestamp),
    .s_out_1_axis_thas_time  (s_out_1_axis_thas_time),
    .s_out_1_axis_tlength    (s_out_1_axis_tlength),
    .s_out_1_axis_teov       (s_out_1_axis_teov),
    .s_out_1_axis_teob       (s_out_1_axis_teob),

    //---------------------------
    // RFNoC Backend Interface
    //---------------------------
    .rfnoc_core_config   (rfnoc_core_config),
    .rfnoc_core_status   (rfnoc_core_status)
  );

  //---------------------------------------------------------------------------
  // User Logic
  //---------------------------------------------------------------------------

  // < Replace this section with your logic >


  // Nothing to do yet, so just drive control signals to default values
  assign m_ctrlport_resp_ack = 1'b0;
  assign m_in_axis_tready = {IN_PORTS{1'b0}};
  assign s_out_0_axis_tvalid = {1{1'b0}};
  assign s_out_1_axis_tvalid = {7{1'b0}};

endmodule // rfnoc_block_ada_filt

`default_nettype wire
