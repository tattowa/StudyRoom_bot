import pandas as pd

def append_log(file_path, entry):
    df = pd.DataFrame([entry])
    df.to_csv(file_path, mode='a', header=not pd.io.common.file_exists(file_path), index=False)