//
// Copyright 2026 <author>
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

// Include our own header:
#include <rfnoc/ada_filt/ada_filt_block_control.hpp>

// These two includes are the minimum required to implement a block:
#include <uhd/rfnoc/defaults.hpp>
#include <uhd/rfnoc/registry.hpp>

using namespace rfnoc::ada_filt;
using namespace uhd::rfnoc;

// Define register addresses here:
//const uint32_t ada_filt_block_control::REG_NAME = 0x1234;

class ada_filt_block_control_impl : public ada_filt_block_control
{
public:
    RFNOC_BLOCK_CONSTRUCTOR(ada_filt_block_control) {}


private:
};

UHD_RFNOC_BLOCK_REGISTER_DIRECT(
    ada_filt_block_control, 874122000, "Ada_filt", CLOCK_KEY_GRAPH, "bus_clk");
