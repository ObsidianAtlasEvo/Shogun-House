"""Recompute neighbour-dependent block states (stair corners, fence / wall / pane
connections) exactly the way the game would, so /fill never leaves half-connected
fences or wrong stair corners behind."""
import numpy as np

from world import X0, Y0, Z0, parse, fmt, is_full_cube, is_leaves, base_name

DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
CCW = {"north": "west", "west": "south", "south": "east", "east": "north"}
OPPO = {"north": "south", "south": "north", "east": "west", "west": "east"}


def _stair_shape(get, x, y, z, st):
    n, p = parse(st)
    f = p.get("facing", "north")
    half = p.get("half", "bottom")

    def stair(s):
        nn, pp = parse(s)
        return nn.endswith("_stairs"), pp

    def can_take(face):
        dx, dz = DIRS[face]
        o = get(x + dx, y, z + dz)
        isst, pp = stair(o)
        return (not isst) or pp.get("facing", "north") != f or pp.get("half", "bottom") != half

    dx, dz = DIRS[f]
    isst, fp = stair(get(x + dx, y, z + dz))
    if isst and fp.get("half", "bottom") == half:
        fd = fp.get("facing", "north")
        if (fd in ("north", "south")) != (f in ("north", "south")) and can_take(OPPO[fd]):
            return "outer_left" if fd == CCW[f] else "outer_right"
    isst, bp = stair(get(x - dx, y, z - dz))
    if isst and bp.get("half", "bottom") == half:
        bd = bp.get("facing", "north")
        if (bd in ("north", "south")) != (f in ("north", "south")) and can_take(bd):
            return "inner_left" if bd == CCW[f] else "inner_right"
    return "straight"


def _sturdy_side(st, side_from_neighbor):
    """Does block `st` present a full sturdy face toward the neighbour?"""
    n, p = parse(st)
    if is_leaves(st) or n in ("barrier", "pumpkin", "carved_pumpkin", "jack_o_lantern", "melon"):
        return False
    if n.endswith("_stairs"):
        # back face is full
        return p.get("facing", "north") == OPPO[side_from_neighbor]
    if n.endswith("_slab"):
        return p.get("type") == "double"
    return is_full_cube(st)


WOODEN = ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "bamboo",
          "crimson", "warped", "pale_oak")


def _fence_family(n):
    if n == "nether_brick_fence":
        return "nether"
    return "wood"


def finalize(world):
    G = world.g
    P = world.palette
    names = [parse(s)[0] for s in P]
    targets = [i for i, n in enumerate(names) if n.endswith("_stairs") or n.endswith("_fence")
               or n.endswith("_wall") or n.endswith("_pane") or n in ("iron_bars",)]
    if not targets:
        return
    mask = np.isin(G, targets)
    coords = np.argwhere(mask)

    def get(x, y, z):
        if 0 <= x < G.shape[0] and 0 <= y < G.shape[1] and 0 <= z < G.shape[2]:
            return P[G[x, y, z]]
        return "air"

    # stairs first (they affect nothing else here), then connections
    updates = []
    for (x, y, z) in coords:
        st = P[G[x, y, z]]
        n, p = parse(st)
        if n.endswith("_stairs"):
            p = dict(p)
            p["shape"] = _stair_shape(get, x, y, z, st)
            updates.append((x, y, z, fmt(n, p)))
    for (x, y, z, s) in updates:
        G[x, y, z] = world.pid(s)
    P = world.palette
    updates = []
    for (x, y, z) in coords:
        st = P[G[x, y, z]]
        n, p = parse(st)
        if n.endswith("_stairs"):
            continue
        p = dict(p)
        con = {}
        for d, (dx, dz) in DIRS.items():
            o = get(x + dx, y, z + dz)
            on, op = parse(o)
            c = False
            if n.endswith("_fence"):
                if on.endswith("_fence") and _fence_family(on) == _fence_family(n):
                    c = True
                elif on.endswith("_fence_gate"):
                    c = (op.get("facing", "north") in ("east", "west")) == (d in ("north", "south"))
                else:
                    c = _sturdy_side(o, d)
            elif n.endswith("_wall"):
                if on.endswith("_wall") or on.endswith("_pane") or on == "iron_bars":
                    c = True
                elif on.endswith("_fence_gate"):
                    c = (op.get("facing", "north") in ("east", "west")) == (d in ("north", "south"))
                else:
                    c = _sturdy_side(o, d)
            else:  # pane / bars
                if on.endswith("_pane") or on == "iron_bars" or on.endswith("_wall"):
                    c = True
                else:
                    c = _sturdy_side(o, d)
            con[d] = c
        if n.endswith("_wall"):
            above = get(x, y + 1, z)
            an, ap = parse(above)
            covers = is_full_cube(above) or (an.endswith("_slab") and ap.get("type", "bottom") in ("bottom", "double")) \
                or (an.endswith("_stairs") and ap.get("half", "bottom") == "bottom")
            for d in DIRS:
                if not con[d]:
                    p[d] = "none"
                else:
                    tall = covers or (an.endswith("_wall") and ap.get(d, "none") != "none")
                    p[d] = "tall" if tall else "low"
            nN, sN, eN, wN = (p["north"] == "none", p["south"] == "none", p["east"] == "none", p["west"] == "none")
            if an.endswith("_wall") and ap.get("up", "true") == "true":
                up = True
            elif (nN and sN and wN and eN) or nN != sN or wN != eN:
                up = True
            elif (p["north"] == "tall" and p["south"] == "tall") or (p["east"] == "tall" and p["west"] == "tall"):
                up = False
            else:
                up = an.endswith("torch") or an.endswith("_sign") or an.endswith("banner") or \
                    an.endswith("pressure_plate") or is_full_cube(above) or an in ("lantern", "soul_lantern")
            p["up"] = "true" if up else "false"
        else:
            for d in DIRS:
                p[d] = "true" if con[d] else "false"
        updates.append((x, y, z, fmt(n, p)))
    for (x, y, z, s) in updates:
        G[x, y, z] = world.pid(s)


def check_water(world, allow=()):
    """Report water/waterlogged cells that would spill once ticks resume."""
    G = world.g
    P = world.palette
    wet = np.array([parse(s)[0] == "water" or parse(s)[1].get("waterlogged") == "true" for s in P])
    # what stops flowing water: solid blocks or waterloggable containers
    def stops(s):
        n, p = parse(s)
        if n == "water" or p.get("waterlogged") == "true":
            return True
        if n in ("air", "cave_air", "light"):
            return False
        if "waterlogged" in p or n in ("campfire", "soul_campfire"):
            return True
        from world import is_solid
        if is_solid(s):
            return True
        return n in ("lily_pad",) and False
    stop = np.array([stops(s) for s in P])
    W = wet[G]
    S = stop[G]
    allow = set(allow)
    bad = []
    wc = np.argwhere(W)
    for d in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0)):
        nb = wc + np.array(d)
        ok = (nb[:, 0] >= 0) & (nb[:, 0] < G.shape[0]) & (nb[:, 1] >= 0) & (nb[:, 1] < G.shape[1]) & \
             (nb[:, 2] >= 0) & (nb[:, 2] < G.shape[2])
        nb = nb[ok]
        leak = ~S[nb[:, 0], nb[:, 1], nb[:, 2]]
        for c in nb[leak]:
            rel = (int(c[0]) + X0, int(c[1]) + Y0, int(c[2]) + Z0)
            if rel not in allow:
                bad.append((rel, P[G[c[0], c[1], c[2]]]))
    return bad
