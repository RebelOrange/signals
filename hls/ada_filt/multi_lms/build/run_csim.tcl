open_project -reset multi_lms

add_files ../src/lib/mlms.cpp
add_files ../src/include/mlms.h

add_files -tb ../src/lib/mlms_tb.cpp
add_files -tb ../src/include/tb_helper.h

set_top multi_lms_module

open_solution -reset solution1
set_part {xczu7ev-ffvc1156-2-e}
create_clock -period 5
set_clock_uncertainty 0.8

config_schedule -relax_ii_for_timing=true -effort high

#default parameters
set mu_val "0.1"
#foreach arg $argv{
#    if { $arg != "-f" && ![string match "*.tcl" $arg]} {
#        set mu_val $arg
#        break
#    }
#}

puts "TCL Resolved parameter mu = $mu_val"
csim_design -clean -argv "$mu_val"

exit