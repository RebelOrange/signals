//
// Copyright 2026 <author>
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#pragma once

#include <uhd/rfnoc/block_controller_factory_python.hpp>
#include <rfnoc/ada_filt/ada_filt_block_control.hpp>

using namespace rfnoc::ada_filt;

void export_ada_filt_block_control(py::module& m)
{
    py::class_<ada_filt_block_control, uhd::rfnoc::noc_block_base, ada_filt_block_control::sptr>(
        m, "ada_filt_block_control")
        .def(py::init(
            &uhd::rfnoc::block_controller_factory<ada_filt_block_control>::make_from))

        ;
}
