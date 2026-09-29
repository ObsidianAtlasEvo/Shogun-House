"""Architectural primitives: timber framing, verandas, stone work, lanterns,
torii, bridges, estate walls and the gable/bargeboard finishing of roofs."""
import math

from world import AIR, with_props, parse, is_air as is_air_state
from roofs import Roof, render_roofs, ridge_ornaments, TILE

POST = "stripped_dark_oak_log[axis=y]"
BEAM_X = "stripped_dark_oak_log[axis=x]"
BEAM_Z = "stripped_dark_oak_log[axis=z]"
PLASTER = "white_concrete"
DARK = "dark_oak_planks"
FLOOR = "spruce_planks"
TATAMI = "bamboo_mosaic"
SHOJI = "white_stained_glass_pane"


def beam(axis):
    return BEAM_X if axis == "x" else BEAM_Z


def stairs(mat, facing, half="bottom"):
    return f"{mat}_stairs[facing={facing},half={half}]"


def slab(mat, t="bottom"):
    return f"{mat}_slab[type={t}]"


# ------------------------------------------------------------------ walls
def timber_wall(w, x0, z0, x1, z1, y0, y1, bay=3, pattern="shoji", openings=(), koshi=True,
                nageshi=None, plaster=PLASTER, infill_override=None):
    """Straight axis-aligned timber-framed wall from (x0,z0) to (x1,z1) inclusive.

    pattern: 'shoji' (lattice windows), 'plaster', 'open' (engawa style), 'lattice' (dark grille),
             'fusuma' (solid pale panels), 'mixed'.
    openings: list of positions along the wall (offset from start) that become 2-high doorways.
    """
    axis = "x" if z0 == z1 else "z"
    n = (x1 - x0) if axis == "x" else (z1 - z0)
    step = 1 if n >= 0 else -1
    L = abs(n)
    if nageshi is None:
        nageshi = y0 + 3
    openings = set(openings)
    for i in range(L + 1):
        x = x0 + (i * step if axis == "x" else 0)
        z = z0 + (i * step if axis == "z" else 0)
        is_post = (i % bay == 0) or i == L
        opening = i in openings
        for y in range(y0, y1 + 1):
            if opening and y < nageshi:
                w.set(x, y, z, AIR)
            elif is_post:
                w.set(x, y, z, POST)
            elif y == y1 or y == nageshi:
                w.set(x, y, z, beam(axis))
            elif infill_override:
                w.set(x, y, z, infill_override(i, y))
            elif y == y0 and koshi and pattern != "open":
                w.set(x, y, z, DARK)
            elif y > nageshi:
                w.set(x, y, z, plaster if pattern in ("plaster", "kura") else "dark_oak_fence")
            elif pattern == "shoji":
                w.set(x, y, z, SHOJI)
            elif pattern in ("plaster", "kura"):
                w.set(x, y, z, plaster)
            elif pattern == "lattice":
                w.set(x, y, z, "dark_oak_fence")
            elif pattern == "fusuma":
                w.set(x, y, z, "birch_planks")
            elif pattern == "mixed":
                w.set(x, y, z, SHOJI if (i // bay) % 2 == 0 else plaster)
            else:
                w.set(x, y, z, AIR)


def box_walls(w, x0, z0, x1, z1, y0, y1, bay=3, pattern="shoji", openings=None, nageshi=None, plaster=PLASTER):
    """Four timber walls around a rectangle. openings: dict side->[offsets]."""
    openings = openings or {}
    timber_wall(w, x0, z1, x1, z1, y0, y1, bay, pattern if not isinstance(pattern, dict) else pattern.get("s"),
                openings.get("s", ()), nageshi=nageshi, plaster=plaster)
    timber_wall(w, x0, z0, x1, z0, y0, y1, bay, pattern if not isinstance(pattern, dict) else pattern.get("n"),
                openings.get("n", ()), nageshi=nageshi, plaster=plaster)
    timber_wall(w, x0, z0, x0, z1, y0, y1, bay, pattern if not isinstance(pattern, dict) else pattern.get("w"),
                openings.get("w", ()), nageshi=nageshi, plaster=plaster)
    timber_wall(w, x1, z0, x1, z1, y0, y1, bay, pattern if not isinstance(pattern, dict) else pattern.get("e"),
                openings.get("e", ()), nageshi=nageshi, plaster=plaster)


def engawa(w, x0, z0, x1, z1, y, inner=None, posts_every=3, post_top=None, floor=FLOOR, edge=True,
           post_grid_origin=None, rail_sides=()):
    """Veranda deck around/along a rectangle. inner: rectangle of the building to exclude from the edge posts."""
    w.fill(x0, y, z0, x1, y, z1, floor)
    if edge:
        # dark edge lip one below the deck
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                w.set(x, y - 1, z, stairs("dark_oak", "south" if z == z0 else "north", "top"))
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                w.set(x, y - 1, z, stairs("dark_oak", "east" if x == x0 else "west", "top"))
    if post_top:
        ox, oz = post_grid_origin or (x0, z0)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                on_edge = x in (x0, x1) or z in (z0, z1)
                if not on_edge:
                    continue
                corner = x in (x0, x1) and z in (z0, z1)
                if corner or (z in (z0, z1) and (x - ox) % posts_every == 0) or \
                        (x in (x0, x1) and (z - oz) % posts_every == 0):
                    w.fill(x, y + 1, z, x, post_top, z, POST)


def railing(w, pts, y, mat="dark_oak_fence", cap=None):
    for (x, z) in pts:
        w.set(x, y, z, mat)
        if cap:
            w.set(x, y + 1, z, cap)


def line(x0, z0, x1, z1):
    pts = []
    n = max(abs(x1 - x0), abs(z1 - z0))
    for i in range(n + 1):
        t = i / max(n, 1)
        pts.append((round(x0 + (x1 - x0) * t), round(z0 + (z1 - z0) * t)))
    return pts


def ceiling(w, x0, z0, x1, z1, y, mat="spruce_planks", grid=3, beam_mat=None):
    """Coffered ceiling: planks with dark beams on a grid."""
    w.fill(x0, y, z0, x1, y, z1, mat)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x - x0) % grid == 0 or (z - z0) % grid == 0:
                w.set(x, y, z, "dark_oak_planks")


def tatami_floor(w, x0, z0, x1, z1, y):
    """Tatami (bamboo mosaic) framed with dark borders every 3x6."""
    w.fill(x0, y, z0, x1, y, z1, TATAMI)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x - x0) % 4 == 3 or (z - z0) % 7 == 6:
                w.set(x, y, z, "bamboo_planks")


# ------------------------------------------------------------------ roofs finishing
def roof_group(w, roofs, mat=TILE, others=None, gable_mat=PLASTER, lantern_corners=False, ornaments=True,
               barge="dark_oak", gable_crest=None):
    """Render merged roofs, then finish irimoya / gable ends with plaster faces and bargeboards."""
    H, S, owner = render_roofs(w, roofs, mat=mat)
    for r in roofs:
        if ornaments and r.kind in ("irimoya", "gable"):
            ridge_ornaments(w, r, S, H, mat)
        for (ax, c, sgn) in r.gable_info():
            finish_gable(w, r, ax, c, sgn, S, H, owner, others or [], gable_mat, barge, gable_crest)
    return H, S, owner


def finish_gable(w, r, ax, c, sgn, S, H, owner, others, gable_mat, barge, crest):
    """Fill the triangular gable face at plane coordinate c and add a bargeboard just outside it."""
    if ax == "x":
        cols = [(c, z) for z in range(r.z0, r.z1 + 1)]
        out = lambda x, z: (x + sgn, z)
    else:
        cols = [(x, c) for x in range(r.x0, r.x1 + 1)]
        out = lambda x, z: (x, z + sgn)
    face = []
    for (x, z) in cols:
        if (x, z) not in S or owner[(x, z)] is not r:
            continue
        ys, kind, f = S[(x, z)]
        o = out(x, z)
        # height of whatever lies just outside (skirt roof, other roof, or nothing)
        if o in S:
            base = S[o][0] + (1 if S[o][1] != "slab" else 1)
        else:
            base = r.eave
        if r.kind in ("gable", "kara"):
            base = r.eave
        if ys - 1 < base:
            continue
        face.append((x, z, base, ys))
    if not face:
        return
    mid = sum((x if ax == "z" else z) for (x, z, _, _) in face) / len(face)
    for (x, z, base, ys) in face:
        for y in range(base, ys):
            along = (x if ax == "z" else z)
            if y == base:
                st = beam("z" if ax == "x" else "x")
            elif abs(along - mid) < 0.6:
                st = POST
            else:
                st = gable_mat
            w.set(x, y, z, st)
        # bargeboard outside the face, mirroring the tile surface
        o = out(x, z)
        yb = ys
        if o in S and S[o][0] >= yb:
            continue
        st = w.get(x, ys, z)
        n, p = parse(st)
        if n.endswith("_stairs"):
            w.set(o[0], yb, o[1], with_props(f"{barge}_stairs", facing=p["facing"], half="bottom"))
        elif n.endswith("_slab"):
            w.set(o[0], yb, o[1], f"{barge}_slab[type={p.get('type', 'bottom')}]")
        else:
            w.set(o[0], yb, o[1], f"{barge}_planks")
    # crest ornament (gegyo) at the apex
    top = max(face, key=lambda t: t[3])
    x, z, base, ys = top
    if ys - base >= 3:
        w.set(x, ys - 1, z, crest or "chiseled_quartz_block")


# ------------------------------------------------------------------ stone & garden structures
def stone_lantern(w, x, y, z, kind="kasuga", moss=False, rng=None):
    """y = ground surface level + 1 (the first air block)."""
    st = "mossy_stone_brick" if moss else "stone_brick"
    if kind == "kasuga":
        w.set(x, y, z, "chiseled_stone_bricks")
        w.set(x, y + 1, z, f"{st}_wall")
        w.set(x, y + 2, z, "lantern")
        # 3x3 hipped cap
        cy = y + 3
        w.set(x, cy, z, slab("stone_brick"))
        for f, dx, dz in (("south", 0, -1), ("north", 0, 1), ("east", -1, 0), ("west", 1, 0)):
            w.set(x + dx, cy, z + dz, stairs(st, f))
        for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            w.set(x + dx, cy, z + dz, slab(st))
        w.set(x, cy + 1, z, "stone_button[face=floor,facing=north]")
        w.set(x, cy, z, "stone_bricks")
    elif kind == "oki":  # small low lantern
        w.set(x, y, z, f"{st}_wall")
        w.set(x, y + 1, z, "lantern")
        w.set(x, y + 2, z, slab(st))
    elif kind == "post":  # slim lantern on a timber post
        w.set(x, y, z, "dark_oak_fence")
        w.set(x, y + 1, z, "dark_oak_fence")
        w.set(x, y + 2, z, "lantern")
        w.set(x, y + 3, z, "dark_oak_slab[type=bottom]")
    elif kind == "yukimi":  # snow-viewing lantern: legs + wide umbrella
        for dx, dz in ((-1, -1), (1, 1), (-1, 1), (1, -1)):
            pass
        w.set(x, y, z, "stone_brick_wall")
        w.set(x, y + 1, z, "lantern")
        cy = y + 2
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                w.set(x + dx, cy, z + dz, slab(st))
        for f, dx, dz in (("south", 0, -2), ("north", 0, 2), ("east", -2, 0), ("west", 2, 0)):
            w.set(x + dx, cy, z + dz, stairs(st, OPPOSITE[f], "top"))
        w.set(x, cy, z, "stone_bricks")
        w.set(x, cy + 1, z, "stone_button[face=floor,facing=north]")


OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}


def hanging_lantern(w, x, y_top, z, chain=1, kind="lantern"):
    """Hang a lantern below the block at y_top+1: chain from y_top down, lantern below."""
    for i in range(chain):
        w.set(x, y_top - i, z, "iron_chain[axis=y]")
    w.set(x, y_top - chain, z, f"{kind}[hanging=true]")


def torii(w, x, z, y, half_width=4, height=10, axis="x", color="red", beam_over=2):
    """Torii facing along the path. axis 'x' => crossbars run along x (path runs along z)."""
    pillar = {"red": "red_concrete", "stone": "stone_bricks", "wood": "stripped_dark_oak_log[axis=y]"}[color]
    kasagi = "polished_blackstone" if color == "red" else "stone_bricks"
    nuki = "red_concrete" if color == "red" else ("stone_bricks" if color == "stone" else DARK)
    base = "polished_blackstone"
    def P(i, j):  # i along crossbar, j along path
        return (x + i, z + j) if axis == "x" else (x + j, z + i)
    for s in (-half_width, half_width):
        px, pz = P(s, 0)
        w.set(px, y, pz, base)
        w.fill(px, y + 1, pz, px, y + height - 2, pz, pillar)
    # nuki (tie beam)
    ny = y + height - 4
    for i in range(-half_width - 1, half_width + 2):
        px, pz = P(i, 0)
        w.set(px, ny, pz, nuki if abs(i) <= half_width else slab("stone_brick" if color != "red" else "red_nether_brick"))
    # gakuzuka (centre strut)
    px, pz = P(0, 0)
    w.set(px, ny + 1, pz, nuki)
    # shimaki + kasagi with upturned ends
    ky = y + height - 2
    for i in range(-half_width - beam_over, half_width + beam_over + 1):
        px, pz = P(i, 0)
        w.set(px, ky, pz, nuki)
        w.set(px, ky + 1, pz, kasagi)
    for sgn in (-1, 1):
        i = sgn * (half_width + beam_over + 1)
        px, pz = P(i, 0)
        if axis == "x":
            f = "west" if sgn > 0 else "east"
        else:
            f = "north" if sgn > 0 else "south"
        w.set(px, ky + 1, pz, with_props("polished_blackstone_stairs", facing=OPPOSITE[f], half="top"))
        px2, pz2 = P(sgn * (half_width + beam_over + 1), 0)
        w.set(px2, ky + 2, pz2, with_props("polished_blackstone_stairs", facing=OPPOSITE[f], half="bottom"))
        w.set(px, ky, pz, AIR)


def arched_bridge(w, axis, a0, a1, c, width, base_y, rise, deck="dark_oak", rail="dark_oak_fence",
                  post="red_concrete", support=True, water_y=None, rail_post=None, lanterns=False):
    """Curved (drum) bridge spanning a0..a1 along `axis` centred on cross coordinate c.
    Deck follows a sine arch from base_y to base_y+rise using stairs/slabs."""
    L = a1 - a0
    # walkable arch: ends flush with the ground, every cell rises by at most half a block
    raw = [int(math.floor((base_y + rise * math.sin(math.pi * i / max(L, 1))) * 2 + 0.5)) for i in range(L + 1)]
    raw[0] = raw[-1] = 2 * base_y
    for i in range(1, L + 1):
        raw[i] = min(raw[i], raw[i - 1] + 1)
    for i in range(L - 1, -1, -1):
        raw[i] = min(raw[i], raw[i + 1] + 1)
    prof = {a0 + i: raw[i] / 2.0 for i in range(L + 1)}
    half = width // 2
    for a in range(a0, a1 + 1):
        h2 = raw[a - a0]
        for k in range(-half, half + 1):
            x, z = (a, c + k) if axis == "x" else (c + k, a)
            if h2 % 2 == 1:
                yy = h2 // 2
                st = slab(deck, "bottom")
            else:
                yy = h2 // 2 - 1
                st = slab(deck, "top")
            w.set(x, yy, z, st)
            for y in range(yy + 1, yy + 4):
                if not is_air_state(w.get(x, y, z)):
                    w.set(x, y, z, AIR)
            # stringer beneath
            w.set(x, yy - 1, z, slab(deck, "top") if h2 % 2 == 1 else "dark_oak_planks" if deck == "dark_oak"
                  else f"{deck}s" if deck.endswith("brick") else "dark_oak_planks")
        # rails
        ry = (h2 + 1) // 2
        for k in (-half - 1, half + 1):
            x, z = (a, c + k) if axis == "x" else (c + k, a)
            w.set(x, ry - 1, z, "dark_oak_planks" if (a - a0) % 4 else (post or "dark_oak_planks"))
            w.set(x, ry, z, rail if (a - a0) % 4 else (post or rail))
            if (a - a0) % 4 == 0 and lanterns and 0 < a - a0 < L:
                w.set(x, ry + 1, z, "lantern")
    # end posts with giboshi caps
    for a in (a0, a1):
        for k in (-half - 1, half + 1):
            x, z = (a, c + k) if axis == "x" else (c + k, a)
            yy = raw[a - a0] // 2
            w.fill(x, yy - 1, z, x, yy + 1, z, post or "dark_oak_planks")
            w.set(x, yy + 2, z, "lantern" if lanterns else "stone_button[face=floor,facing=north]")
    if support and water_y is not None:
        for a in (a0 + L // 4, a1 - L // 4):
            for k in (-half - 1, half + 1):
                x, z = (a, c + k) if axis == "x" else (c + k, a)
                yy = raw[a - a0] // 2
                for y in range(water_y - 3, yy - 1):
                    w.set(x, y, z, "stripped_dark_oak_log[axis=y]")
    return prof


def tsuijibei(w, pts, y0, h=4, axis=None, cap_mat="deepslate_tile", base="stone_bricks", plaster="white_concrete",
              post_every=6, lines=0):
    """Estate wall along a list of (x, z) points forming straight axis-aligned runs.
    Base stone (1), plaster body, dark timber posts, small tiled cap roof."""
    pts = list(pts)
    for idx, (x, z) in enumerate(pts):
        w.set(x, y0, z, base)
        w.set(x, y0 + 1, z, base if idx % 2 == 0 else "mossy_stone_bricks" if (x * 7 + z * 3) % 5 == 0 else base)
        for y in range(y0 + 2, y0 + h):
            w.set(x, y, z, plaster)
        if idx % post_every == 0:
            for y in range(y0 + 2, y0 + h):
                w.set(x, y, z, POST)
        w.set(x, y0 + h, z, "stripped_dark_oak_log[axis=y]" if idx % post_every == 0 else DARK)
    # cap roof: along each point, stairs to both sides + ridge
    S = set(pts)
    for (x, z) in pts:
        yy = y0 + h + 1
        horiz = (x - 1, z) in S or (x + 1, z) in S
        vert = (x, z - 1) in S or (x, z + 1) in S
        w.set(x, yy, z, f"{cap_mat}s" if cap_mat.endswith("tile") else cap_mat)
        w.set(x, yy + 1, z, slab(cap_mat))
        if horiz:
            w.set(x, yy, z - 1, stairs(cap_mat, "south"))
            w.set(x, yy, z + 1, stairs(cap_mat, "north"))
            w.set(x, yy - 1, z - 1, slab("dark_oak", "top"))
            w.set(x, yy - 1, z + 1, slab("dark_oak", "top"))
        if vert:
            w.set(x - 1, yy, z, stairs(cap_mat, "east"))
            w.set(x + 1, yy, z, stairs(cap_mat, "west"))
            w.set(x - 1, yy - 1, z, slab("dark_oak", "top"))
            w.set(x + 1, yy - 1, z, slab("dark_oak", "top"))


def steps(w, x0, x1, z0, z1, y_top, direction, mat="stone_brick", count=None):
    """Descending stairs from y_top outward in `direction` (north/south/east/west) over the given span."""
    n = count or 3
    dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[direction]
    face = OPPOSITE[direction]
    for i in range(n):
        y = y_top - i
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                xx, zz = x + dx * i, z + dz * i
                w.set(xx, y, zz, stairs(mat, face))
                for yy in range(y - 1, y_top - n - 1, -1):
                    w.set(xx, yy, zz, f"{mat}s" if not mat.endswith("s") else mat)
