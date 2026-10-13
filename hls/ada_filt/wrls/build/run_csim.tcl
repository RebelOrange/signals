open_project -reset wrls

add_files ../src/lib/wrls.cpp
add_files ../src/include/wrls.h

add_files -tb ../src/include/tb_helper.h
add_files -tb ../src/lib/wrls_tb.cpp

set_top weighted_rls_module

open_solution -reset solution1
set_part {xczu7ev-ffvc1156-2-e}
create_clock -period 5
set_clock_uncertainty 0.8

config_schedule -relax_ii_for_timing=true -effort high

#default parameters
set mu_val "0.9999"

foreach arg $argv {
    if { $arg != "-f" && ![string match "*.tcl" $arg]} {
        set mu_val $arg
        break
    }
}

puts "TCL Resolved parameter mu = $mu_val"
csim_design -clean -argv "$mu_val"

exit