"""Compile the voxel model into an ordered list of relative Minecraft commands.

Every placement is written relative to the estate centre as
    /execute positioned {C} run fill ~x1 ~y1 ~z1 ~x2 ~y2 ~z2 <block>
and the runner substitutes {C} with the centre coordinate chosen in the .bat.
"""
import math

import numpy as np

from world import X0, Y0, Z0, parse, is_plant, is_thin, PLANT_NAMES

MAXVOL = 32768
PFX = "/execute positioned {C} run "


def rel(v):
    return "~" if v == 0 else f"~{v}"


def fill_cmd(x0, y0, z0, x1, y1, z1, state):
    if (x0, y0, z0) == (x1, y1, z1):
        return f"{PFX}setblock {rel(x0)} {rel(y0)} {rel(z0)} {state}"
    return f"{PFX}fill {rel(x0)} {rel(y0)} {rel(z0)} {rel(x1)} {rel(y1)} {rel(z1)} {state}"


def chunked(x0, y0, z0, x1, y1, z1, state):
    """Split a big region into fills that respect the vanilla 32768-block limit."""
    out = []
    h = y1 - y0 + 1
    if h > 32:
        for ya in range(y0, y1 + 1, 32):
            out += chunked(x0, ya, z0, x1, min(y1, ya + 31), z1, state)
        return out
    side = int(math.sqrt(MAXVOL / h))
    for xa in range(x0, x1 + 1, side):
        for za in range(z0, z1 + 1, side):
            out.append(fill_cmd(xa, y0, za, min(x1, xa + side - 1), y1, min(z1, za + side - 1), state))
    return out


ATTACH_EXTRA = {"lantern", "soul_lantern", "torch", "wall_torch", "sea_pickle", "glow_lichen", "lily_pad",
                "vine", "bell", "ladder", "snow", "flower_pot", "cake", "redstone_wire", "rail",
                "spore_blossom", "hanging_roots", "moss_carpet", "pointed_dripstone"}


def klass(state):
    n, p = parse(state)
    if n == "light":
        return 6
    if n == "air":
        return 0
    if n == "water":
        return 2
    if n in ("iron_chain", "chain"):
        return 3
    if (n in PLANT_NAMES or n in ATTACH_EXTRA or n.endswith("_carpet") or n.endswith("candle")
            or n.endswith("_button") or n.endswith("_pressure_plate") or n.endswith("_banner")
            or n.endswith("_sapling") or n.endswith("_tulip") or n.startswith("potted_")
            or n.endswith("_torch")):
        return 5 if p.get("hanging") == "true" else 4
    return 1


def greedy_boxes(final, must, allowed_id, covered, order=("x", "z", "y")):
    """Grow axis-aligned boxes over cells whose final id == allowed_id covering every `must` cell."""
    allowed = final == allowed_id
    boxes = []
    pts = np.argwhere(must & ~covered)
    # sort by y, z, x so boxes grow bottom-up
    if len(pts) == 0:
        return boxes
    pts = pts[np.lexsort((pts[:, 0], pts[:, 2], pts[:, 1]))]
    nx, ny, nz = final.shape
    for (x, y, z) in pts:
        if covered[x, y, z]:
            continue
        best = None
        for od in (("x", "z", "y"), ("z", "x", "y"), ("y", "x", "z")):
            lo = [x, y, z]
            hi = [x, y, z]
            for ax in od:
                a = {"x": 0, "y": 1, "z": 2}[ax]
                while True:
                    if hi[a] + 1 >= final.shape[a]:
                        break
                    vol = (hi[0] - lo[0] + 1) * (hi[1] - lo[1] + 1) * (hi[2] - lo[2] + 1)
                    extent = hi[a] - lo[a] + 1
                    if vol // extent * (extent + 1) > MAXVOL:
                        break
                    sl = [slice(lo[0], hi[0] + 1), slice(lo[1], hi[1] + 1), slice(lo[2], hi[2] + 1)]
                    sl[a] = slice(hi[a] + 1, hi[a] + 2)
                    if not allowed[tuple(sl)].all():
                        break
                    hi[a] += 1
            sl = (slice(lo[0], hi[0] + 1), slice(lo[1], hi[1] + 1), slice(lo[2], hi[2] + 1))
            gain = int((must[sl] & ~covered[sl]).sum())
            if best is None or gain > best[0]:
                best = (gain, tuple(lo), tuple(hi))
        _, lo, hi = best
        covered[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1] = True
        boxes.append((lo, hi))
    return boxes


BASE_GROUP = {"dirt", "stone", "mud", "clay", "gravel", "grass_block", "sand", "coarse_dirt", "moss_block",
              "stone_bricks", "cobblestone", "packed_mud", "white_concrete_powder", "deepslate_tiles"}


def rank_key(state):
    n, p = parse(state)
    k = klass(state)
    if k != 1:
        return (k, 0, state)
    if n in BASE_GROUP:
        g = 0
    elif n.endswith("_leaves"):
        g = 1
    elif n.endswith("_stairs") or n.endswith("_slab") or n.endswith("_fence") or n.endswith("_wall") \
            or n.endswith("_pane") or n.endswith("_trapdoor") or n.endswith("_gate"):
        g = 3
    else:
        g = 2
    return (k, g, state)


def compile_model(world, baseline, region):
    """Painter's-order compilation: each state's boxes may also sweep over cells that a
    LATER command will overwrite anyway, which collapses leaves, roofs and pond beds
    into far fewer fills.  Returns ([(class, cmd)], pair_cmds)."""
    G = world.g
    diff = (G != baseline) & region
    pair_mask = np.zeros(G.shape, dtype=bool)
    for parts in world.pairs:
        for (x, y, z, s) in parts:
            pair_mask[x - X0, y - Y0, z - Z0] = True
    ids = [int(i) for i in np.unique(G[diff | pair_mask])]
    order = sorted(ids, key=lambda i: rank_key(world.palette[i]))
    rank = np.full(len(world.palette), 10 ** 6, dtype=np.int64)
    for r, i in enumerate(order):
        rank[i] = r
    R = rank[G]
    R[pair_mask] = 10 ** 7
    covered = np.zeros(G.shape, dtype=bool)
    out = []
    for r, i in enumerate(order):
        st = world.palette[i]
        must = diff & (G == i) & ~pair_mask
        if not must.any():
            continue
        final = np.where(((G == i) & region) | (diff & (R > r)) | (pair_mask & region), i, -1)
        cov = np.zeros(G.shape, dtype=bool)
        k = klass(st)
        for (lo, hi) in greedy_boxes(final, must, i, cov):
            cmd = fill_cmd(lo[0] + X0, lo[1] + Y0, lo[2] + Z0, hi[0] + X0, hi[1] + Y0, hi[2] + Z0, st)
            out.append((r, lo[1] + Y0, lo[2] + Z0, lo[0] + X0, k, cmd))
    # keep painter order between states; inside a state go bottom-up (top-down for hanging things)
    out.sort(key=lambda t: (t[0], t[1] if t[4] != 5 else -t[1], t[2], t[3]))
    cmds = [(k, c) for (_, _, _, _, k, c) in out]
    pair_cmds = []
    for parts in world.pairs:
        for (x, y, z, s) in parts:
            pair_cmds.append(fill_cmd(x, y, z, x, y, z, s))
    return cmds, pair_cmds
