open_project -reset wrls

add_files ../src/lib/wrls.cpp
add_files ../src/include/wrls.h

add_files -tb ../src/include/tb_helper.h
add_files -tb ../src/lib/wrls_tb.cpp

set_top weighted_rls_module

open_solution -reset solution1
set_part {xczu7ev-ffvc1156-2-e}
create_clock -period 5ns
set_clock_uncertainty 10%

config_schedule -relax_ii_for_timing=true -effort high

# test settings
# 1. Force specific operations to bind to Fabric (LUTs) or DSPs
set_directive_bind_op -op mul -impl fabric complex_rls_stap_kernel
set_directive_bind_op -op add -impl fabric complex_rls_stap_kernel

# 2. Enforce hard limits on physical hardware instances (forces operator sharing)
set_directive_allocation -limit 4 -type operation complex_rls_stap_kernel mul
set_directive_allocation -limit 2 -type operation complex_rls_stap_kernel dsp

# 3. Allow scheduler to relax II to minimize logic and fit timing
config_schedule -relax_ii_for_timing true

# 4. Disable automatic loop unrolling blowup
config_compile -auto_unroll_max_size 0

csynth_design

# copy files to project directory
set target_dir "../syn"
if {[file exists $target_dir]} {
    file delete -force $target_dir
}

file mkdir $target_dir

file copy -force {*}[glob wrls/solution1/syn/*] $target_dir/


exit