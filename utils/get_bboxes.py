from pathlib import Path
from read_exp import read_exp

cwd = Path(".").resolve()
adjoint_dir = cwd / "../../adjoint-ISSM"

for shelf_name in ["Amery", "RnFlch", "LarsenC", "LarsenD", "Ross"]:
    exp_dir = adjoint_dir / "out" / shelf_name / "Geometry" / f"{shelf_name}_Outline.exp"
    floating_domain = read_exp(exp_dir)[0]
    maxx, minx, maxy, miny = max(floating_domain["x"]), min(floating_domain["x"]), max(floating_domain["y"]), min(floating_domain["y"])
    print(f"[{shelf_name}]\nbbox = [{maxx},{minx},{maxy},{miny},]")