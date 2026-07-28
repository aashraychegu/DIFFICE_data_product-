from pathlib import Path

def len_files(path: Path):
    ctr = 0
    for item in path.iterdir():
        if item.is_file():
            ctr += 1
    return ctr