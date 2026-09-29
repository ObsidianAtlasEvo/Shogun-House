"""Replay a command file onto a voxel grid and compare with the model (block-for-block)."""
import re
import sys

import numpy as np

from world import X0, Y0, Z0

FILL = re.compile(r"run (fill|setblock) ((?:~-?\d* ?){3,6})(\S+)$")


def replay(w, grid, path):
    n = 0
    for line in open(path):
        line = line.strip()
        m = FILL.search(line)
        if not m:
            continue
        nums = [int(t[1:] or 0) for t in m.group(2).split()]
        if m.group(1) == "setblock":
            nums = nums + nums
        x0, y0, z0, x1, y1, z1 = nums
        xa, xb = sorted((x0, x1)); ya, yb = sorted((y0, y1)); za, zb = sorted((z0, z1))
        assert (xb - xa + 1) * (yb - ya + 1) * (zb - za + 1) <= 32768, line
        grid[xa - X0:xb - X0 + 1, ya - Y0:yb - Y0 + 1, za - Z0:zb - Z0 + 1] = w.pid(m.group(3))
        n += 1
    return n


if __name__ == "__main__":
    import os
    import estate
    from finalize import finalize
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SAKURA_SHOGUN_ESTATE", "commands")
    w, t = estate.build()
    finalize(w)
    old, _ = estate.old_model_grid(w, os.path.join(os.path.dirname(os.path.abspath(__file__)), "data",
                                                   "estate_v1_as_built"))
    estate.compile_all(w, base=old)       # final model incl. light blocks
    region = estate.work_region(w)
    # 1) full build from the cleared site
    g = w.g.copy()
    g[:] = 0
    n = replay(w, g, os.path.join(root, "sakura_estate_full.txt"))
    bad = (g != w.g) & region
    print(f"full build : {n} placements, mismatching blocks: {int(bad.sum())}")
    # 2) repair on top of the as-built first release
    g = old.copy()
    n = replay(w, g, os.path.join(root, "sakura_estate_fix_v2.txt"))
    bad = (g != w.g) & region
    print(f"repair     : {n} placements, mismatching blocks: {int(bad.sum())}")
    for c in np.argwhere(bad)[:10]:
        print("   ", tuple(int(v) for v in c + (X0, Y0, Z0)), w.palette[g[tuple(c)]], "->", w.palette[w.g[tuple(c)]])
    sys.exit(1 if bad.any() else 0)
