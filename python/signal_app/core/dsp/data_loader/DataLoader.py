import numpy as np
import pandas as pd

def export_to_csv(datamatrix: np.ndarray, filename: str="export_data.csv"):
    num_chan, num_samp = np.shape(datamatrix)

    df_dict = {}
    for ch in range(num_chan):
        df_dict[f"chan_{ch}_I"] = np.real(datamatrix[ch,:]).astype(np.int16)
        df_dict[f"chan_{ch}_Q"] = np.imag(datamatrix[ch,:]).astype(np.int16)

    df = pd.DataFrame(df_dict)
    df.to_csv(filename, index=False)