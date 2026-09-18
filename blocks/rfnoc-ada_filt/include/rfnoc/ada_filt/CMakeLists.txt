#
# Copyright 2019 Ettus Research, a National Instruments Brand
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# List all header files here
install(
    FILES
    ada_filt_block_control.hpp
    config.hpp
    #my_block_control.hpp
    DESTINATION include/rfnoc/ada_filt
    COMPONENT headers
)
