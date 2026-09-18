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


csynth_design

# copy files to project directory
set target_dir "../syn"
if {[file exists $target_dir]} {
    file delete -force $target_dir
}

file mkdir $target_dir

file copy -force {*}[glob multi_lms/solution1/syn/*] $target_dir/


exit