import pandas as pd
import numpy as np
import subprocess


def run_vitis_csim(exe_path:str, exe_filename:str, arg_val:float):
    cmd = ["vitis_hls", "-f", exe_path+exe_filename, str(arg_val)]
    print(f"[Python] Executing {' '.join(cmd)}\n"+ "-"*50)

    process = subprocess.Popen(
        cmd,
        cwd=exe_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1)

    for line in process.stdout:
        print(line, end="")

    process.wait()
    print("-"*50)

    if process.returncode != 0:
        raise RuntimeError(f"Testbench exited with error code {process.returncode}")



