"""Japanese roof generator.

Each roof is described as a continuous height field H(x, z) (concave pitch,
upturned corners, optional irimoya gables, karahafu undulation) and is then
quantised into tile stairs / slabs / full blocks.  Several roofs can be merged
into one field (max) so valleys between intersecting roofs resolve naturally.
"""
import math

from world import AIR, with_props

TILE = {"full": "deepslate_tiles", "stairs": "deepslate_tile_stairs", "slab": "deepslate_tile_slab",
        "ridge": "polished_deepslate", "ridge_wall": "deepslate_tile_wall", "soffit": "dark_oak_planks",
        "fascia": "stripped_dark_oak_log", "barge": "dark_oak", "gable": "white_concrete",
        "gable_timber": "stripped_dark_oak_log"}
WOOD_SHINGLE = dict(TILE, full="spruce_planks", stairs="spruce_stairs", slab="spruce_slab", ridge="dark_oak_planks",
                    ridge_wall=None)
CAP_TILE = dict(TILE)


class Roof:
    """A single roof volume.

    kind: 'hip' | 'irimoya' | 'gable' | 'pyramid' | 'kara'
    rect: eave outline (x0, x1, z0, z1) inclusive.
    axis: 'x' or 'z' -> direction of the ridge.
    """

    def __init__(self, rect, eave_y, kind="irimoya", axis="x", s0=0.5, s1=1.15, lift=1.2, lift_len=None,
                 setback=None, hole=None, walls=None, cap=None, height_scale=1.0, max_rise=None):
        self.x0, self.x1, self.z0, self.z1 = rect
        self.eave = eave_y
        self.kind = kind
        self.axis = axis
        self.s0, self.s1 = s0, s1
        self.lift = lift
        self.hole = hole
        self.walls = walls
        self.hs = height_scale
        self.max_rise = max_rise
        L = (self.x1 - self.x0) if axis == "x" else (self.z1 - self.z0)
        S = (self.z1 - self.z0) if axis == "x" else (self.x1 - self.x0)
        self.halfdepth = S / 2.0
        self.lift_len = lift_len if lift_len is not None else max(3.0, min(L, S) * 0.3)
        if setback is None:
            setback = max(2, int(round(self.halfdepth * 0.55)))
        self.setback = setback

    def p(self, d):
        D = max(self.halfdepth, 1e-3)
        t = min(d, D)
        v = t * (self.s0 + (self.s1 - self.s0) * t / (2 * D)) * self.hs
        if self.max_rise is not None:
            v = min(v, self.max_rise)
        return v

    def contains(self, x, z):
        if not (self.x0 <= x <= self.x1 and self.z0 <= z <= self.z1):
            return False
        if self.hole:
            hx0, hx1, hz0, hz1 = self.hole
            if hx0 <= x <= hx1 and hz0 <= z <= hz1:
                return False
        return True

    def dists(self, x, z):
        dx = min(x - self.x0, self.x1 - x)
        dz = min(z - self.z0, self.z1 - z)
        if self.axis == "x":
            return dx, dz  # (along-ridge distance to end, across distance to eave)
        return dz, dx

    def height(self, x, z):
        """Height above y=0 (float) or None outside."""
        if not self.contains(x, z):
            return None
        da, dc = self.dists(x, z)  # da: to the short (end) edges, dc: to the long eaves
        if self.kind == "hip":
            base = self.p(min(da, dc))
        elif self.kind == "pyramid":
            base = self.p(min(da, dc))
        elif self.kind == "gable":
            base = self.p(dc)
        elif self.kind == "irimoya":
            if da < self.setback:
                base = min(self.p(dc), self.p(da))
            else:
                base = self.p(dc)
        elif self.kind == "kara":
            D = max(self.halfdepth, 1e-3)
            t = min(dc / D, 1.0)
            # cusped gable: flared edges, rounded crown
            base = self.hs * (D * 0.75) * (t * t * (3 - 2 * t)) + 0.35 * dc
        else:
            raise ValueError(self.kind)
        # upturned corners: closeness to the ends along each eave, fading inward
        lift = 0.0
        if self.lift:
            R = self.lift_len
            ca = max(0.0, 1 - da / R) ** 2
            cc = max(0.0, 1 - dc / R) ** 2
            ea = max(0.0, 1 - da / 2.5)
            ec = max(0.0, 1 - dc / 2.5)
            if self.kind in ("gable", "kara"):
                lift = self.lift * ca * ec * 0.6
            else:
                lift = self.lift * max(ca * ec, cc * ea)
        return self.eave + base + lift

    def gable_info(self):
        """For irimoya/gable roofs: list of gable planes (fixed coordinate on ridge axis, outward sign)."""
        if self.kind == "irimoya":
            s = self.setback
        elif self.kind in ("gable", "kara"):
            s = 0
        else:
            return []
        if self.axis == "x":
            return [("x", self.x0 + s, -1), ("x", self.x1 - s, +1)]
        return [("z", self.z0 + s, -1), ("z", self.z1 - s, +1)]


DIRS4 = (("east", 1, 0), ("west", -1, 0), ("south", 0, 1), ("north", 0, -1))


def render_roofs(world, roofs, mat=TILE, ridge=True, gables=True, soffit=True, gable_fill=None,
                 lanterns=None, protect=True):
    """Merge several Roof objects (max) and quantise them into blocks."""
    H = {}
    owner = {}
    xs = [r.x0 for r in roofs] + [r.x1 for r in roofs]
    zs = [r.z0 for r in roofs] + [r.z1 for r in roofs]
    for r in roofs:
        for x in range(r.x0, r.x1 + 1):
            for z in range(r.z0, r.z1 + 1):
                h = r.height(x, z)
                if h is None:
                    continue
                if (x, z) not in H or h > H[(x, z)]:
                    H[(x, z)] = h
                    owner[(x, z)] = r
    h2 = {k: int(math.floor(v * 2 + 0.5)) for k, v in H.items()}

    def surf_block(k):
        """Return (y, kind, facing) of the surface element for a column."""
        v = h2[k]
        x, z = k
        cands = [(h2[(x + dx, z + dz)], H[(x + dx, z + dz)], f) for (f, dx, dz) in DIRS4
                 if (x + dx, z + dz) in h2 and h2[(x + dx, z + dz)] > v]
        best = max(cands) if cands else None
        if v % 2 == 1:
            yb = v // 2
            if best is not None and best[0] >= v + 3:
                return yb, "stairs", best[2]
            return yb, "slab", None
        yt = v // 2
        if best is not None:
            return yt - 1, "stairs", best[2]
        return yt - 1, "full", None

    S = {k: surf_block(k) for k in h2}
    placed_top = {}
    for k, (y, kind, f) in S.items():
        x, z = k
        if kind == "slab":
            st = mat["slab"]
        elif kind == "stairs":
            st = with_props(mat["stairs"], facing=f, half="bottom")
        else:
            st = mat["full"]
        world.set(x, y, z, st)
        placed_top[k] = y
        # close vertical faces toward lower neighbours
        low = y
        for (_, dx, dz) in DIRS4:
            n = (x + dx, z + dz)
            if n in S:
                low = min(low, S[n][0] + 1)
            else:
                low = min(low, y)
        for yy in range(low, y):
            world.set(x, yy, z, mat["full"])
        bottom = min(low, y)
        r = owner[k]
        inside = False
        if r.walls:
            wx0, wx1, wz0, wz1 = r.walls
            inside = wx0 <= x <= wx1 and wz0 <= z <= wz1
        da, dc = r.dists(x, z)
        if soffit and not inside and min(da, dc) <= 1:
            world.set(x, bottom - 1, z, with_props("dark_oak_slab", type="top") if kind != "full" else mat["soffit"])
    # peaks: top slabs become full so the ridge cap sits flush
    if ridge:
        for k, (y, kind, f) in S.items():
            x, z = k
            if kind == "slab" and not any((x + dx, z + dz) in h2 and h2[(x + dx, z + dz)] > h2[k]
                                          for (_, dx, dz) in DIRS4):
                world.set(x, y, z, with_props(mat["slab"], type="double"))
    return H, S, owner


def ridge_ornaments(world, roof, S, H, mat=TILE):
    """Curl the ridge ends upward (onigawara) and cap the ridge line."""
    if roof.kind not in ("irimoya", "gable", "hip"):
        return
    # ridge line along the axis through the middle of the short dimension
    if roof.axis == "x":
        zc = (roof.z0 + roof.z1) / 2.0
        zs = [int(math.floor(zc)), int(math.ceil(zc))]
        cols = [(x, z) for z in set(zs) for x in range(roof.x0, roof.x1 + 1) if (x, z) in S]
        key = lambda c: c[0]
    else:
        xc = (roof.x0 + roof.x1) / 2.0
        xs = [int(math.floor(xc)), int(math.ceil(xc))]
        cols = [(x, z) for x in set(xs) for z in range(roof.z0, roof.z1 + 1) if (x, z) in S]
        key = lambda c: c[1]
    if not cols:
        return
    top = max(S[c][0] for c in cols)
    ridge_cols = [c for c in cols if S[c][0] == top]
    if not ridge_cols:
        return
    lo = min(key(c) for c in ridge_cols)
    hi = max(key(c) for c in ridge_cols)
    for c in ridge_cols:
        x, z = c
        world.set(x, top + 1, z, mat["ridge"])
    # end ornaments: raise the last block and curl
    for end, sgn in ((lo, -1), (hi, +1)):
        for c in ridge_cols:
            if key(c) != end:
                continue
            x, z = c
            if roof.axis == "x":
                f = "east" if sgn < 0 else "west"
                ox, oz = x, z
            else:
                f = "south" if sgn < 0 else "north"
                ox, oz = x, z
            world.set(ox, top + 2, oz, with_props("polished_deepslate_stairs", facing=f, half="bottom"))
            world.set(ox, top + 1, oz, "chiseled_deepslate")
