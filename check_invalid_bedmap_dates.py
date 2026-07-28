from pathlib import Path
import pandas as pd
from tqdm import tqdm

base = Path("./data/bedmap_csv/").resolve()

paths = list(base.iterdir())
invalid_paths = []

for path in tqdm(paths):
    csv_metadata = pd.read_csv(path, nrows=18, sep = ': ', engine='python', header= None)
    start = int(csv_metadata[csv_metadata[0] == "#time_coverage_start"][1].iloc[0])
    end = int(csv_metadata[csv_metadata[0] == "#time_coverage_end"][1].iloc[0])
    df = pd.read_csv(path,skiprows=18,low_memory = False)
    date = df["date"]
    valid_date = date[date != -9999]
    valid_prop = len(valid_date) / len(date)
    if valid_prop != 1:
        invalid_paths.append(path)
        tqdm.write(f"{end} - {start} = {start - end}")

# print(len(invalid_paths) / len(paths))
