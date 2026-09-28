"""Everything outside the manor: estate walls & gate, nagaya (retainer quarters),
the arrival approach, forecourt, Moon Garden, shrine, dojo & archery range,
tea house garden, bath house / hot spring and the service quarter."""
import math

from world import AIR, is_air, parse, with_props, rock
from arch import (POST, BEAM_X, BEAM_Z, PLASTER, DARK, FLOOR, TATAMI, SHOJI, timber_wall, box_walls, engawa,
                  ceiling, tatami_floor, roof_group, stone_lantern, hanging_lantern, stairs, slab, arched_bridge,
                  torii, tsuijibei, line)
from roofs import Roof, TILE, WOOD_SHINGLE
from site_manor import hang, close_to_roof, perimeter, andon
import site_terrain as T
import nature as N


def ground(w, x, z, ymax=20):
    return N.surface_y(w, x, z, ymax)


def pave(w, x, z, mat, ymax=12):
    """Replace the ground surface block at (x,z) with mat (keeps height)."""
    y = ground(w, x, z, ymax)
    if y is None:
        return None
    w.set(x, y, z, mat)
    if not is_air(w.get(x, y + 1, z)) and parse(w.get(x, y + 1, z))[0] in ("short_grass", "fern", "pink_petals"):
        w.set(x, y + 1, z, AIR)
    return y


def path_along(w, pts, width, rng, mats=("smooth_stone", "polished_andesite", "andesite"), edge="gravel",
               ymax=12, stepping=False):
    cells = {}
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    for x in range(min(xs) - width - 2, max(xs) + width + 3):
        for z in range(min(zs) - width - 2, max(zs) + width + 3):
            d = T.poly_dist(x, z, pts)
            if d <= width / 2.0:
                cells[(x, z)] = "core"
            elif d <= width / 2.0 + 1.0 and edge:
                cells.setdefault((x, z), "edge")
    for (x, z), kind in cells.items():
        if (x, z) in T_WATER:
            continue
        if kind == "core":
            if stepping and rng.random() < 0.35:
                pave(w, x, z, "moss_block", ymax)
            else:
                pave(w, x, z, rng.choice(mats), ymax)
        else:
            s = parse(w.get(x, ground(w, x, z, ymax) or 0, z))[0]
            if s in ("grass_block", "moss_block", "dirt"):
                pave(w, x, z, edge, ymax)
    return cells


T_WATER = {}


# ================================================================ estate walls + gate
def estate_walls(w, rng):
    south = [(x, 62) for x in range(-62, 63) if not (-6 <= x <= 6) and not (-37 <= x <= -9)]
    west = [(-62, z) for z in range(-46, 62)]
    east = [(62, z) for z in range(-43, 62) if not (19 <= z <= 23)]
    # foundation course one lower on the outside
    for (x, z) in south + west + east:
        w.set(x, -1, z, "stone_bricks")
    runs = []
    cur = []
    for p in south:
        if cur and p[0] != cur[-1][0] + 1:
            runs.append(cur)
            cur = []
        cur.append(p)
    runs.append(cur)
    for r in runs + [west, [p for p in east if p[1] < 19], [p for p in east if p[1] > 23]]:
        tsuijibei(w, r, 0, h=4)
    # corner caps
    for (x, z) in ((-62, 62), (62, 62)):
        w.set(x, 6, z, "deepslate_tile_slab[type=bottom]")
    # service gate posts (east, into the stable yard)
    for z in (18, 24):
        w.fill(62, 0, z, 62, 6, z, POST)
    for z in range(18, 25):
        w.set(62, 6, z, BEAM_Z)
        w.set(61, 7, z, stairs("deepslate_tile", "east"))
        w.set(63, 7, z, stairs("deepslate_tile", "west"))
        w.set(62, 7, z, "deepslate_tiles")
        w.set(62, 8, z, slab("deepslate_tile"))
    for z in range(19, 24):
        w.set(62, 0, z, "cobblestone")
    hang(w, 61, 21, 4)


def main_gate(w, rng):
    """Yakuimon-style gate in the south wall: modest, deep-roofed, doors folded open."""
    for x in range(-6, 7):
        w.set(x, -1, 62, "stone_bricks")
        w.set(x, 0, 62, "stone_bricks")
    # threshold paving
    for x in range(-3, 4):
        for z in range(58, 67):
            pave(w, x, z, "polished_andesite" if (x + z) % 2 else "smooth_stone")
    # posts: main pair on the wall line and a rear pair
    for x in (-4, 4):
        w.fill(x, 0, 62, x, 7, 62, POST)
        w.fill(x, 1, 59, x, 7, 59, POST)
        w.set(x, 0, 59, "polished_andesite")
        w.fill(x, 7, 59, x, 7, 62, BEAM_Z)
    # stub walls to meet the estate wall
    for x in (-6, -5, 5, 6):
        w.set(x, 1, 62, "stone_bricks")
        w.fill(x, 2, 62, x, 4, 62, PLASTER)
        w.set(x, 5, 62, DARK)
    w.fill(-5, 7, 62, 5, 7, 62, BEAM_X)
    w.fill(-5, 7, 59, 5, 7, 59, BEAM_X)
    w.fill(-3, 6, 62, 3, 6, 62, stairs("dark_oak", "south", "top"))
    w.set(0, 6, 62, "chiseled_quartz_block")
    # door leaves folded open against the inside (dark oak with blackstone studs)
    for x in (-3, 3):
        for z in (60, 61):
            w.fill(x, 1, z, x, 5, z, "dark_oak_planks")
            w.set(x, 3, z, "polished_blackstone")
    # roof
    r = Roof((-7, 7, 56, 68), 8, kind="gable", axis="x", s0=0.55, s1=1.2, lift=1.2, lift_len=3.5)
    roof_group(w, [r], gable_crest="gold_block")
    # soffit fill between beams and roof
    close_to_roof(w, [(x, 62) for x in range(-5, 6)] + [(x, 59) for x in range(-5, 6)], 8, mat=DARK, limit=3)
    for (x, z) in ((-2, 64), (2, 64), (-2, 58), (2, 58)):
        hang(w, x, z, 5)


def nagaya(w, rng):
    """Retainers' row house forming part of the south wall (villager quarters)."""
    x0, x1, z0, z1 = -37, -9, 56, 62
    w.fill(x0, 0, z0, x1, 0, z1, "stone_bricks")
    w.fill(x0 + 1, 1, z0 + 1, x1 - 1, 1, z1 - 1, "spruce_planks")
    w.fill(x0, 1, z0, x1, 1, z0, "stone_bricks")
    w.fill(x0, 1, z1, x1, 1, z1, "stone_bricks")
    y0, y1 = 2, 6
    # outer (south) face: plaster with barred windows (musha-mado)
    def south_face(i, y):
        return "dark_oak_fence" if (y in (3, 4) and i % 4 in (1, 2)) else PLASTER
    timber_wall(w, x0, z1, x1, z1, y0, y1, 4, "plaster", infill_override=south_face, nageshi=5)
    timber_wall(w, x0, z0, x1, z0, y0, y1, 4, "shoji", openings=(2, 9, 16, 23), nageshi=5)
    timber_wall(w, x0, z0, x0, z1, y0, y1, 3, "plaster", nageshi=5)
    timber_wall(w, x1, z0, x1, z1, y0, y1, 3, "plaster", nageshi=5)
    # namako base course outside
    for x in range(x0, x1 + 1):
        w.set(x, 1, z1 + 0, "polished_andesite" if x % 2 else "stone_bricks")
    # partitions into 4 rooms
    rooms = [(-36, -30), (-29, -23), (-22, -16), (-15, -10)]
    for (a, b) in rooms[1:]:
        w.fill(a - 1, 2, z0 + 1, a - 1, 5, z1 - 1, "birch_planks")
        w.fill(a - 1, 2, z0 + 1, a - 1, 5, z0 + 1, POST)
    work = ["lectern[facing=north]", "composter", "barrel[facing=up]", "brewing_stand"]
    colours = ["white", "light_gray", "white", "brown"]
    for (a, b), ws, c in zip(rooms, work, colours):
        w.pair([(b - 1, 2, 60, f"{c}_bed[facing=south,part=foot]"), (b - 1, 2, 61, f"{c}_bed[facing=south,part=head]")])
        w.set(a, 2, 61, ws)
        andon(w, a, 2, 58)
    ceiling(w, x0 + 1, z0 + 1, x1 - 1, z1 - 1, 7, grid=4)
    r = Roof((x0 - 2, x1 + 2, z0 - 3, z1 + 3), 7, kind="gable", axis="x", s0=0.5, s1=1.0, lift=1.0, lift_len=4)
    roof_group(w, [r])
    close_to_roof(w, perimeter(x0, z0, x1, z1), 7, limit=4)
    for x in range(x0 + 2, x1, 7):
        hang(w, x, z0 - 1, 4)


# ================================================================ approach (outside the south wall)
APP_PATH = [(-34, 108), (-28, 105), (-20, 101), (-11, 98), (-4, 96), (0, 94), (0, 86)]


def approach(w, rng):
    # rice paddies either side of the lantern avenue
    for side in (-1, 1):
        for (a, b) in ((10, 17), (19, 26), (28, 35), (37, 43)):
            for (c, d) in ((65, 71), (73, 79), (81, 85)):
                xa, xb = (a, b) if side > 0 else (-b, -a)
                flooded = ((a + c) // 3 + (1 if side > 0 else 0)) % 3 == 0
                paddy(w, xa, xb, c, d, flooded, rng)
    # main path
    cells = path_along(w, APP_PATH, 3, rng, mats=("polished_andesite", "smooth_stone", "stone", "andesite"))
    for z in range(63, 87):
        for x in range(-1, 2):
            pave(w, x, z, "smooth_stone" if (z % 3) else "polished_andesite")
        for x in (-2, 2):
            pave(w, x, z, "stone_bricks" if z % 2 else "mossy_stone_bricks")
        for x in (-3, 3):
            pave(w, x, z, "gravel")
    # vermilion drum bridge over the stream
    arched_bridge(w, "z", 85, 95, 0, 3, 0, 2.6, deck="dark_oak", rail="dark_oak_fence", post="red_concrete",
                  water_y=T.APP_WATER_Y, lanterns=True)
    # lantern avenue
    for z in (75, 79, 83):
        for x in (-4, 4):
            stone_lantern(w, x, 0, z, "kasuga", moss=(z % 8 == 0))
    # the torii threshold
    torii(w, 0, 72, 0, half_width=4, height=11, axis="x", color="red")
    # stone markers at the path start
    stone_lantern(w, -31, 0, 104, "kasuga", moss=True)
    stone_lantern(w, -25, 0, 99, "oki")
    stone_lantern(w, -14, 0, 95, "oki")


def paddy(w, x0, x1, z0, z1, flooded, rng):
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if (x, z) in T_WATER:
                continue
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            if edge:
                w.set(x, -1, z, "grass_block")
                if rng.random() < 0.05:
                    w.set(x, 0, z, "firefly_bush")
                elif rng.random() < 0.15:
                    w.set(x, 0, z, "short_grass")
                continue
            if flooded:
                w.set(x, -2, z, "mud")
                w.set(x, -1, z, "water")
                if rng.random() < 0.08:
                    w.set(x, 0, z, "lily_pad")
            else:
                zc = (z0 + z1) // 2
                if z == zc:
                    w.set(x, -2, z, "mud")
                    w.set(x, -1, z, "water")
                else:
                    w.set(x, -1, z, "farmland[moisture=7]")
                    w.set(x, 0, z, "wheat[age=7]")


# ================================================================ forecourt
def forecourt(w, rng):
    # formal stone path from the gate to the porch steps
    for z in range(14, 59):
        if (0, z) in T_WATER:
            continue
        for x in range(-2, 3):
            pave(w, x, z, "smooth_stone" if abs(x) <= 1 else "polished_andesite")
        for x in (-3, 3):
            pave(w, x, z, "stone_bricks")
    # stone arch bridge over the stream
    arched_bridge(w, "z", 33, 41, 0, 5, 1, 1.6, deck="stone_brick", rail="stone_brick_wall", post="stone_bricks",
                  water_y=T.WATER_Y, lanterns=False)
    # raked gravel gardens (karesansui) either side of the path, between stream and podium
    for side in (-1, 1):
        xa, xb = (4, 16) if side > 0 else (-16, -4)
        rocks = [(side * 10, 22, 2.2), (side * 13, 26, 1.4), (side * 7, 27, 1.1)]
        for x in range(xa, xb + 1):
            for z in range(15, 31):
                if (x, z) in T_WATER or T.poly_dist(x, z, T.STREAM) < 2.6:
                    continue
                dmin = min(math.hypot(x - rx, z - rz) - rr for (rx, rz, rr) in rocks)
                ring = int(dmin) % 2 == 0 and dmin < 4.5
                if dmin > 4.5:
                    ring = z % 2 == 0
                w.set(x, 0, z, "white_concrete_powder" if not ring else "light_gray_concrete_powder")
                w.set(x, -1, z, "stone")
        for (rx, rz, rr) in rocks:
            N.boulder(w, rx, 0, rz, rr, rng, mats=("stone", "andesite", "tuff", "cobblestone"), sink=0)
    # cloud-pruned pines flanking the steps
    N.pine(w, -8, 1, 17, rng, height=6, pads=5, spread=3.5, lean=(-0.1, 0.05))
    N.pine(w, 9, 1, 18, rng, height=7, pads=5, spread=4, lean=(0.12, 0.0))
    # path lanterns
    for z in (20, 29, 45, 53):
        for x in (-5, 5):
            stone_lantern(w, x, 1, z, "kasuga", moss=(z > 40))
    for z in (57,):
        for x in (-6, 6):
            stone_lantern(w, x, 1, z, "oki")
    # stream-side lanterns (small, low)
    for (x, z) in ((10, 34), (-10, 40), (-15, 31), (18, 35), (-20, 18)):
        y = ground(w, x, z)
        if y is not None and (x, z) not in T_WATER:
            stone_lantern(w, x, y + 1, z, "oki", moss=True)


# ================================================================ moon garden
def moon_garden(w, rng):
    # stone shoreline: rocks around the pond edge, pebble beaches in places
    for (x, z), (ws, bed) in list(T_WATER.items()):
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n in T_WATER:
                continue
            y = ground(w, *n)
            if y is None or y < 0 or y > 3:
                continue
            s = parse(w.get(n[0], y, n[1]))[0]
            if s not in ("grass_block", "moss_block", "dirt"):
                continue
            r = rng.random()
            if r < 0.28:
                w.set(n[0], y, n[1], rock(n[0], y, n[1], ("mossy_cobblestone", "stone")))
                if rng.random() < 0.3 and is_air(w.get(n[0], y + 1, n[1])):
                    w.set(n[0], y + 1, n[1], rock(n[0], y, n[1], ("mossy_cobblestone", "stone")))
            elif r < 0.4:
                w.set(n[0], y, n[1], "gravel")
    # island rim stones + the ancient tree comes later (trees module)
    # turtle island: yukimi (snow viewing) lantern
    stone_lantern(w, 15, 1, -41, "yukimi", moss=True)
    # waterfall: rock face, source pool on the mound, lip, plunge
    fx0, fx1 = 6, 9
    for x in range(fx0 - 3, fx1 + 4):
        for z in range(-60, -53):
            top = T_H(x, z)
            for y in range(-4, max(top, 7) + 1):
                if z >= -55 and y <= 7:
                    w.set(x, y, z, rock(x, y, z, ("stone", "mossy_cobblestone", "andesite")))
    # source channel on top
    for x in range(fx0 + 1, fx1):
        for z in range(-58, -53):
            w.set(x, 6, z, "stone")
            w.set(x, 7, z, "water")
            w.set(x, 8, z, AIR)
        w.set(x, 7, -59, "stone")
    for z in range(-58, -53):
        w.set(fx0, 7, z, "mossy_cobblestone")
        w.set(fx1, 7, z, "mossy_cobblestone")
        w.set(fx0, 8, z, "mossy_cobblestone" if z % 2 else "moss_block")
        w.set(fx1, 8, z, "mossy_cobblestone" if z % 2 else "moss_block")
    # the plunge space in front of the lip must be open to the pond
    for x in range(fx0 + 1, fx1):
        for y in range(0, 8):
            w.set(x, y, -53, AIR)
        w.set(x, -1, -53, "water")
    for x in (fx0, fx1):
        for y in range(-1, 8):
            w.set(x, y, -53, rock(x, y, -53))
    # moon pavilion (azumaya) on the west lobe
    pavilion(w, rng)
    # sugar cane & irises at a few pond margins
    for (x, z) in ((-44, -38), (-45, -39), (22, -34), (23, -34), (-50, -44), (-49, -52), (26, -44)):
        y = ground(w, x, z)
        if y is not None and (x, z) not in T_WATER and any((x + a, z + b) in T_WATER for a, b in
                                                            ((1, 0), (-1, 0), (0, 1), (0, -1))):
            # cane must stand on a block that touches water at its own level
            w.set(x, -1, z, "sand")
            for k in range(0, 3):
                w.set(x, k, z, "sugar_cane")


def T_H(x, z):
    return TERRAIN.H(x, z) if TERRAIN else 0


TERRAIN = None


def pavilion(w, rng):
    """Moon pavilion: square open azumaya with a pyramidal roof and finial, deck over the water."""
    x0, x1, z0, z1 = -58, -52, -56, -50
    w.fill(x0 - 1, -1, z0 - 1, x1 + 1, 1, z1 + 1, "stone_bricks")
    w.fill(x0, 2, z0, x1, 2, z1, "dark_oak_planks")
    w.fill(x1 + 2, 1, z0 + 2, x1 + 5, 1, z1 - 2, "dark_oak_slab[type=top]")
    for x in range(x1 + 2, x1 + 6):
        w.set(x, 2, z0 + 2, "dark_oak_fence")
        w.set(x, 2, z1 - 2, "dark_oak_fence")
    w.set(x1 + 5, 2, z0 + 3, "dark_oak_fence")
    w.set(x1 + 5, 2, z0 + 4, "dark_oak_fence")
    for (x, z) in ((x1 + 5, z0 + 2), (x1 + 5, z1 - 2)):
        w.fill(x, -4, z, x, 0, z, "stripped_dark_oak_log[axis=y]")
        w.set(x, 3, z, "lantern")
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        w.fill(x, 3, z, x, 6, z, POST)
    for x in range(x0, x1 + 1):
        w.set(x, 7, z0, BEAM_X)
        w.set(x, 7, z1, BEAM_X)
    for z in range(z0, z1 + 1):
        w.set(x0, 7, z, BEAM_Z)
        w.set(x1, 7, z, BEAM_Z)
    # benches (koshikake) along two sides
    for x in range(x0 + 1, x1):
        w.set(x, 3, z0, "dark_oak_slab[type=bottom]")
    for z in range(z0 + 1, z1):
        w.set(x0, 3, z, "dark_oak_slab[type=bottom]")
    r = Roof((x0 - 3, x1 + 3, z0 - 3, z1 + 3), 8, kind="pyramid", s0=0.55, s1=1.3, lift=1.4, lift_len=3.5)
    H, S, owner = roof_group(w, [r], ornaments=False)
    top = max(v[0] for v in S.values())
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    w.set(cx, top + 1, cz, "polished_deepslate")
    w.set(cx, top + 2, cz, "lightning_rod")
    hang(w, cx, cz, 5, maxup=6)


# ================================================================ shrine
def shrine(w, rng):
    # terrace retaining wall + stairs
    for x in range(34, 62):
        for z in range(-61, -43):
            edge = x == 34 or z == -44
            if edge:
                for y in range(0, 5):
                    w.set(x, y, z, rng.choice(("stone_bricks", "mossy_stone_bricks", "stone_bricks", "cracked_stone_bricks")))
                w.set(x, 4, z, "polished_andesite")
            else:
                w.set(x, 4, z, "gravel" if rng.random() < 0.9 else "moss_block")
    # stairs up from the south at x 39..41
    for i in range(5):
        for x in range(39, 42):
            w.set(x, 4 - i, -44 + i, stairs("stone_brick", "north"))
            w.fill(x, -1, -44 + i, x, 3 - i, -44 + i, "stone_bricks")
    # sando: path north from the East Wing to the stairs
    for z in range(-40, -12):
        for x in range(39, 42):
            if (x, z) not in T_WATER:
                pave(w, x, z, "polished_andesite" if x == 40 else "smooth_stone")
    # senbon torii tunnel
    for z in range(-38, -13, 3):
        torii(w, 40, z, 1, half_width=2, height=6, axis="x", color="red", beam_over=1)
    for z in (-42,):
        torii(w, 40, z, 3, half_width=2, height=6, axis="x", color="red", beam_over=1)
    torii(w, 40, -47, 5, half_width=3, height=8, axis="x", color="red", beam_over=1)
    # stone-paved worship path on the terrace to the hall
    for z in range(-52, -44):
        for x in range(39, 42):
            w.set(x, 4, z, "polished_andesite")
    for x in range(41, 49):
        for z in range(-50, -47):
            w.set(x, 4, z, "polished_andesite")
    # honden: nagare-zukuri hall
    x0, x1, z0, z1 = 44, 54, -59, -52
    w.fill(x0 - 1, 5, z0 - 1, x1 + 1, 5, z1 + 3, "stone_bricks")
    w.fill(x0, 6, z0, x1, 6, z1 + 2, "dark_oak_planks")
    box_walls(w, x0, z0, x1, z1, 7, 11, bay=5, pattern={"s": "lattice", "n": "plaster", "w": "plaster", "e": "plaster"},
              openings={"s": (4, 5, 6)}, nageshi=10)
    for x in range(x0, x1 + 1, 5):
        w.fill(x, 7, z1 + 2, x, 11, z1 + 2, "red_concrete")
    for x in range(x0, x1 + 1):
        w.set(x, 12, z1 + 2, BEAM_X)
        w.set(x, 12, z1, BEAM_X)
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        w.fill(x, 7, z, x, 11, z, "red_concrete")
    # steps to the hall
    for x in range(47, 52):
        w.set(x, 5, z1 + 4, stairs("stone_brick", "north"))
    r = Roof((x0 - 2, x1 + 2, z0 - 3, z1 + 6), 12, kind="gable", axis="x", s0=0.45, s1=1.05, lift=1.2, lift_len=3)
    H, S, owner = roof_group(w, [r], gable_crest="gold_block")
    close_to_roof(w, perimeter(x0, z0, x1, z1), 12, limit=6)
    # interior: mirror altar
    w.set(49, 7, z0 + 1, "chiseled_quartz_block")
    w.set(49, 8, z0 + 1, "gold_block")
    w.set(48, 7, z0 + 1, "white_candle[candles=4,lit=true]")
    w.set(50, 7, z0 + 1, "white_candle[candles=4,lit=true]")
    # shimenawa rope + bell + offering box
    for x in range(x0 + 2, x1 - 1):
        w.set(x, 11, z1 + 3, "iron_chain[axis=x]")
    w.set(49, 11, z1 + 3, "stripped_dark_oak_log[axis=x]")
    w.set(49, 10, z1 + 3, "bell[attachment=ceiling,facing=north]")
    w.set(49, 7, z1 + 3, "barrel[facing=up]")
    # stone lanterns + komainu-like guardians
    for x in (38, 43):
        stone_lantern(w, x, 5, -49, "kasuga", moss=True)
    for x in (46, 52):
        stone_lantern(w, x, 6, -48, "oki", moss=True)


# ================================================================ dojo & archery
def dojo(w, rng):
    x0, x1, z0, z1 = -46, -26, 24, 39
    fy = 2
    w.fill(x0 - 1, 0, z0 - 1, x1 + 1, 1, z1 + 1, "stone_bricks")
    w.fill(x0, fy, z0, x1, fy, z1, "oak_planks")
    w.fill(x0 - 1, fy, z0 - 1, x1 + 1, fy, z0 - 1, FLOOR)
    w.fill(x0 - 1, fy, z1 + 1, x1 + 1, fy, z1 + 1, FLOOR)
    y0, y1 = 3, 8
    timber_wall(w, x0, z1, x1, z1, y0, y1, 4, "shoji", openings=(9, 10, 11), nageshi=6)
    timber_wall(w, x0, z0, x1, z0, y0, y1, 4, "plaster", nageshi=6)
    timber_wall(w, x0, z0, x0, z1, y0, y1, 3, "mixed", nageshi=6)
    timber_wall(w, x1, z0, x1, z1, y0, y1, 3, "mixed", openings=(7, 8), nageshi=6)
    ceiling(w, x0 + 1, z0 + 1, x1 - 1, z1 - 1, 9, grid=4)
    # kamiza (master's platform) at the north
    w.fill(x0 + 5, fy + 1, z0 + 1, x1 - 5, fy + 1, z0 + 3, "dark_oak_planks")
    for x in range(x0 + 5, x1 - 4):
        w.set(x, fy + 1, z0 + 4, stairs("dark_oak", "north"))
    w.set(-36, fy + 2, z0 + 1, "dark_oak_slab[type=bottom]")
    w.set(-36, fy + 3, z0 + 1, "potted_cherry_sapling")
    for x in (-40, -32):
        w.set(x, fy + 5, z0 + 1, "red_wall_banner[facing=south]")
    for x in (-42, -30):
        andon(w, x, fy + 1, z0 + 2)
    # weapon wall + storage along the west side
    for z in range(z0 + 2, z1 - 1, 2):
        w.set(x0 + 1, fy + 1, z, "barrel[facing=east]")
    w.set(x0 + 1, fy + 1, z1 - 1, "chest[facing=east,type=single]")
    w.set(x1 - 1, fy + 1, z1 - 2, "smithing_table")
    w.set(x1 - 1, fy + 1, z1 - 4, "grindstone[face=floor,facing=west]")
    for (x, z) in ((x0 + 2, z1 - 1), (x1 - 2, z0 + 6), (x0 + 2, z0 + 6)):
        andon(w, x, fy + 1, z)
    r = Roof((x0 - 4, x1 + 4, z0 - 4, z1 + 4), 9, kind="irimoya", axis="x", s0=0.45, s1=1.05, lift=1.3, lift_len=5,
             walls=(x0, x1, z0, z1))
    roof_group(w, [r], gable_crest="gold_block")
    close_to_roof(w, perimeter(x0, z0, x1, z1), 9, limit=4)
    for x in range(x0 - 1, x1 + 2, 5):
        hang(w, x, z1 + 2, 5)
        hang(w, x, z0 - 2, 5)
    # training yard
    for x in range(-46, -23):
        for z in range(43, 56):
            w.set(x, 0, z, "sand" if (x + z) % 5 else "gravel")
            w.set(x, -1, z, "stone")
    for (x, z) in ((-43, 47), (-38, 47), (-33, 47), (-28, 47)):
        w.set(x, 1, z, "hay_block")
        w.set(x, 2, z, "dark_oak_fence")
        w.set(x, 3, z, "hay_block")
    # weapon rack
    for x in range(-44, -39):
        w.set(x, 1, 54, "dark_oak_fence")
        w.set(x, 2, 54, "dark_oak_slab[type=bottom]")
    stone_lantern(w, -24, 1, 44, "kasuga", moss=True)
    stone_lantern(w, -46, 1, 42, "oki")
    # archery range (kyudojo) along the west wall
    ax0, ax1 = -61, -51
    for x in range(ax0, ax1 + 1):
        for z in range(18, 57):
            w.set(x, 0, z, "grass_block")
    # shajo (shooting hall) at the south end
    w.fill(ax0, 0, 49, ax1, 1, 56, "stone_bricks")
    w.fill(ax0, 2, 49, ax1, 2, 56, "oak_planks")
    for (x, z) in ((ax0, 49), (ax1, 49), (ax0, 56), (ax1, 56), (-56, 49), (-56, 56)):
        w.fill(x, 3, z, x, 6, z, POST)
    timber_wall(w, ax0, 56, ax1, 56, 3, 7, 5, "plaster", nageshi=6)
    for x in range(ax0, ax1 + 1):
        w.set(x, 7, 49, BEAM_X)
    r = Roof((ax0 - 2, ax1 + 2, 46, 58), 8, kind="gable", axis="x", s0=0.5, s1=1.0, lift=1.0, lift_len=3)
    roof_group(w, [r])
    close_to_roof(w, [(x, 56) for x in range(ax0, ax1 + 1)], 8, limit=3)
    hang(w, -56, 49, 5)
    # azuchi: sand mound with targets under a small roof at the north end
    for x in range(ax0, ax1 + 1):
        for z in range(18, 23):
            hgt = 3 - (z - 18) // 2
            for y in range(1, hgt + 1):
                w.set(x, y, z, "sand" if y < hgt else "sand")
            w.set(x, 0, z, "stone")
    for x in (-58, -56, -54):
        w.set(x, 1, 22, "target")
    r2 = Roof((ax0 - 1, ax1 + 1, 16, 22), 5, kind="gable", axis="x", s0=0.4, s1=0.8, lift=0.6, lift_len=2)
    roof_group(w, [r2])
    for x in (ax0, ax1):
        w.fill(x, 1, 21, x, 4, 21, POST)
    stone_lantern(w, -50, 1, 23, "oki")


# ================================================================ tea house
def tea_house(w, rng):
    x0, x1, z0, z1 = 40, 50, 31, 41
    fy = 1
    # piers in the water and stone base on land
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if (x, z) in T_WATER:
                if (x - x0) % 3 == 0 and (z - z0) % 3 == 0 or x in (x0 - 1,) and z in (z0 - 1, z1 + 1):
                    w.fill(x, T.WATER_Y - 3, z, x, 0, z, "stripped_dark_oak_log[axis=y]")
            else:
                w.fill(x, -1, z, x, 0, z, "stone_bricks")
    w.fill(x0 - 1, fy, z0 - 1, x1 + 1, fy, z1 + 1, FLOOR)
    tatami_floor(w, x0 + 1, z0 + 1, x1 - 1, z1 - 1, fy)
    # engawa over the water on the west side (wider)
    w.fill(x0 - 4, fy, z0 + 1, x0 - 1, fy, z1 - 1, FLOOR)
    for z in range(z0 + 1, z1):
        w.set(x0 - 4, fy - 1, z, stairs("dark_oak", "east", "top"))
    for z in (z0 + 1, z1 - 1):
        w.fill(x0 - 4, T.WATER_Y - 3, z, x0 - 4, fy - 1, z, "stripped_dark_oak_log[axis=y]")
    y0, y1 = fy + 1, fy + 5
    box_walls(w, x0, z0, x1, z1, y0, y1, bay=5,
              pattern={"w": "shoji", "e": "plaster", "n": "mixed", "s": "mixed"},
              openings={"w": (3, 4, 6, 7), "s": (8,)}, nageshi=fy + 4)
    ceiling(w, x0 + 1, z0 + 1, x1 - 1, z1 - 1, y1 + 1, mat="bamboo_planks", grid=5)
    # irori hearth, low table, flowers
    cx, cz = 45, 36
    w.set(cx, fy, cz, "campfire[lit=true,signal_fire=false]")
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        w.set(cx + dx, fy, cz + dz, "polished_andesite")
    w.set(cx, fy + 4, cz, "iron_chain[axis=y]")
    w.set(cx, fy + 3, cz, "iron_chain[axis=y]")
    w.set(cx, fy + 2, cz, AIR)
    w.set(x1 - 1, fy + 1, z0 + 1, "decorated_pot")
    w.set(x1 - 1, fy + 1, z1 - 1, "potted_pink_tulip")
    w.set(x0 + 1, fy + 1, z0 + 1, "potted_lily_of_the_valley")
    for x in range(x1 - 3, x1):
        w.set(x, fy + 1, z0 + 1, "spruce_slab[type=bottom]")
    # tokonoma
    w.set(x1 - 1, fy + 2, cz, "potted_cherry_sapling")
    w.set(x1 - 1, fy + 1, cz, "dark_oak_planks")
    r = Roof((x0 - 4, x1 + 3, z0 - 3, z1 + 3), y1 + 1, kind="irimoya", axis="z", s0=0.42, s1=0.85, lift=1.2,
             lift_len=4, walls=(x0, x1, z0, z1))
    roof_group(w, [r], mat=WOOD_SHINGLE, gable_crest="stripped_bamboo_block[axis=y]", barge="dark_oak")
    close_to_roof(w, perimeter(x0, z0, x1, z1), y1 + 1, limit=4)
    for (x, z) in ((x0 - 3, z0 + 1), (x0 - 3, z1 - 1), (x1 + 2, z0 - 2), (x1 + 2, z1 + 2)):
        hang(w, x, z, fy + 3, maxup=6)
    # roji: stepping stones from the forecourt through a middle gate to the tea house
    stones = [(8, 20), (10, 21), (12, 22), (14, 21), (16, 22), (18, 24), (20, 25), (22, 24), (24, 26), (27, 27),
              (30, 27), (33, 28), (36, 29), (38, 31), (39, 33)]
    for (x, z) in stones:
        if (x, z) in T_WATER:
            continue
        y = ground(w, x, z)
        if y is not None:
            w.set(x, y, z, "polished_andesite")
            for dx, dz in ((1, 0), (0, 1)):
                if rng.random() < 0.5 and (x + dx, z + dz) not in T_WATER:
                    yy = ground(w, x + dx, z + dz)
                    if yy == y:
                        w.set(x + dx, yy, z + dz, "moss_block")
    # tsukubai (water basin) + lantern by the path
    w.set(35, 1, 26, "water_cauldron[level=3]")
    w.set(35, 0, 26, "stone")
    for (x, z) in ((34, 26), (36, 26), (35, 25)):
        w.set(x, 1, z, rng.choice(("mossy_cobblestone", "stone")))
    stone_lantern(w, 33, 1, 24, "kasuga", moss=True)
    # bamboo fence enclosing the roji with a small roofed middle gate
    for x in range(20, 32):
        if x in (21, 22):
            continue
        if (x, 23) not in T_WATER:
            w.set(x, 1, 23, "bamboo_fence")
    for (x, z) in ((20, 23), (23, 23)):
        w.fill(x, 1, z, x, 3, z, "stripped_bamboo_block[axis=y]")
    for x in range(19, 25):
        w.set(x, 4, 23, "bamboo_mosaic_slab[type=bottom]")
    # zig-zag plank bridge (yatsuhashi) across the koi pond
    zz = [(28, 48, 34, 48), (34, 48, 34, 52), (34, 52, 40, 52)]
    for (ax, az, bx, bz) in zz:
        for (x, z) in line(ax, az, bx, bz):
            w.set(x, 0, z, "dark_oak_slab[type=top]")
            if (x + z) % 3 == 0:
                w.set(x, -1, z, "stripped_dark_oak_log[axis=y]")
    # iris beds along the bridge
    for (x, z) in ((30, 47), (32, 49), (35, 50), (37, 53), (33, 47)):
        if (x, z) in T_WATER:
            w.set(x, T.WATER_Y, z, "water")
    stone_lantern(w, 26, 1, 51, "yukimi", moss=True)


# ================================================================ bath house + hot spring
def bath(w, rng):
    x0, x1, z0, z1 = -60, -50, -33, -24
    fy = 1
    w.fill(x0 - 1, 0, z0 - 1, x1 + 1, 0, z1 + 1, "stone_bricks")
    w.fill(x0, fy, z0, x1, fy, z1, "spruce_planks")
    # hinoki tub inside
    w.fill(-58, fy, -31, -53, fy, -28, "stripped_spruce_wood[axis=y]")
    w.fill(-57, fy - 1, -30, -54, fy, -29, "water")
    w.fill(-57, fy - 2, -30, -54, fy - 2, -29, "stripped_spruce_wood[axis=y]")
    y0, y1 = fy + 1, fy + 5
    box_walls(w, x0, z0, x1, z1, y0, y1, bay=5,
              pattern={"n": "plaster", "w": "plaster", "s": "shoji", "e": "shoji"},
              openings={"e": (4, 5), "s": (4, 5, 6)}, nageshi=fy + 4)
    ceiling(w, x0 + 1, z0 + 1, x1 - 1, z1 - 1, y1 + 1, mat="stripped_spruce_wood[axis=x]", grid=5)
    w.set(-51, fy + 1, -32, "barrel[facing=up]")
    w.set(-52, fy + 1, -32, "barrel[facing=up]")
    for (x, z) in ((-59, -25), (-51, -25)):
        andon(w, x, fy + 1, z)
    r = Roof((x0 - 3, x1 + 3, z0 - 3, z1 + 3), y1 + 1, kind="irimoya", axis="x", s0=0.5, s1=1.1, lift=1.2,
             lift_len=4, walls=(x0, x1, z0, z1))
    roof_group(w, [r], gable_crest="gold_block")
    close_to_roof(w, perimeter(x0, z0, x1, z1), y1 + 1, limit=4)
    # covered walkway from the West Wing veranda to the bath house
    for x in range(-49, -41):
        for z in (-29, -28, -27):
            w.set(x, 1, z, "stone_bricks")
            w.set(x, 2, z, "spruce_planks")
        for z in (-30, -26):
            w.set(x, 1, z, "stone_bricks")
            w.set(x, 2, z, "spruce_slab[type=top]")
        if x % 3 == 0:
            for z in (-30, -26):
                w.fill(x, 3, z, x, 5, z, POST)
    for x in range(-49, -41):
        for z in (-30, -26):
            w.set(x, 6, z, BEAM_X)
    wr = Roof((-50, -40, -32, -24), 7, kind="gable", axis="x", s0=0.45, s1=0.9, lift=0.5, lift_len=2)
    roof_group(w, [wr], ornaments=False)
    w.fill(-43, 3, -29, -41, 3, -27, "spruce_planks")
    for x in (-45, -48):
        hang(w, x, -28, 4, maxup=5)
    # outdoor rotenburo: rock-rimmed pool, underwater warm glow, steam from hidden campfires
    for x in range(-62, -43):
        for z in range(-22, -2):
            v = T.in_union(x, z, T.BATH_POOL, jitter=1.0, seed=6.0)
            if v <= 1.0:
                w.fill(x, -3, z, x, -3, z, "stone")
                w.fill(x, -2, z, x, 0, z, "water")
                w.set(x, 1, z, AIR)
            elif v <= 1.6:
                w.set(x, 0, z, rock(x, 0, z, ("stone", "mossy_cobblestone", "tuff")))
                if v <= 1.3 and rng.random() < 0.55:
                    w.set(x, 1, z, rock(x, 1, z, ("stone", "mossy_cobblestone", "moss_block")))
                if rng.random() < 0.2:
                    w.set(x, -1, z, "stone")
    for (x, z) in ((-55, -15), (-52, -11), (-56, -9)):
        w.set(x, -3, z, "campfire[lit=true,signal_fire=false]")
    for (x, z) in ((-53, -16), (-57, -12), (-50, -8)):
        w.set(x, -2, z, "sea_pickle[pickles=3,waterlogged=true]")
    stone_lantern(w, -46, 1, -18, "oki", moss=True)
    stone_lantern(w, -60, 1, -4, "kasuga", moss=True)


# ================================================================ service quarter (east strip)
def service(w, rng):
    # kitchen (daidokoro) with an earthen floor, irori, smokers and a raised smoke roof
    x0, x1, z0, z1 = 46, 58, -10, 2
    w.fill(x0, 0, z0, x1, 0, z1, "stone_bricks")
    w.fill(x0 + 1, 1, z0 + 1, x1 - 1, 1, z1 - 1, "packed_mud")
    w.fill(x0, 1, z0, x1, 1, z1, "stone_bricks", replace=["air"])
    y0, y1 = 2, 7
    box_walls(w, x0, z0, x1, z1, y0, y1, bay=3, pattern={"n": "plaster", "s": "mixed", "e": "plaster", "w": "shoji"},
              openings={"w": (5, 6), "s": (6,)}, nageshi=5)
    # hearths and stations along the east wall
    for z in (z0 + 2, z0 + 4):
        w.set(x1 - 1, 2, z, "smoker[facing=west]")
    for z in (z0 + 6, z0 + 8):
        w.set(x1 - 1, 2, z, "furnace[facing=west]")
    w.set(x1 - 1, 2, z0 + 10, "water_cauldron[level=3]")
    for x in range(x0 + 2, x0 + 7):
        w.set(x, 2, z0 + 1, "barrel[facing=up]")
    w.set(x0 + 8, 2, z0 + 1, "crafting_table")
    w.set(x0 + 9, 2, z0 + 1, "chest[facing=south,type=single]")
    w.set(52, 1, -4, "campfire[lit=true,signal_fire=false]")
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        w.set(52 + dx, 1, -4 + dz, "polished_andesite")
    ceiling(w, x0 + 1, z0 + 1, x1 - 1, z1 - 1, 8, grid=4)
    w.fill(51, 8, -5, 53, 8, -3, AIR)
    r = Roof((x0 - 3, x1 + 3, z0 - 3, z1 + 3), 8, kind="irimoya", axis="x", s0=0.5, s1=1.1, lift=1.2, lift_len=4,
             walls=(x0, x1, z0, z1))
    roof_group(w, [r], gable_crest="gold_block")
    close_to_roof(w, perimeter(x0, z0, x1, z1), 8, limit=4)
    for (x, z) in ((x0 + 2, z0 + 3), (x0 + 2, z1 - 3), (x1 - 3, z1 - 2)):
        hang(w, x, z, 5, maxup=4)
    # corridor from the East Wing veranda
    for x in range(42, 46):
        for z in (-6, -5, -4):
            w.set(x, 1, z, "stone_bricks")
            w.set(x, 2, z, "spruce_planks")
    for x in range(42, 46):
        for z in (-7, -3):
            w.set(x, 3, z, "dark_oak_fence")

    # smithy / swordsmith forge: open timber shed
    x0, x1, z0, z1 = 46, 59, -26, -15
    w.fill(x0, 0, z0, x1, 0, z1, "stone_bricks")
    w.fill(x0 + 1, 1, z0 + 1, x1 - 1, 1, z1 - 1, "cobblestone")
    for x in range(x0, x1 + 1, 3):
        for z in (z0, z1):
            w.fill(x, 1, z, x, 6, z, POST)
    for z in range(z0, z1 + 1, 3):
        for x in (x0, x1):
            w.fill(x, 1, z, x, 6, z, POST)
    timber_wall(w, x1, z0, x1, z1, 1, 6, 3, "plaster", nageshi=4)
    timber_wall(w, x0, z0, x1, z0, 1, 6, 3, "plaster", nageshi=4)
    for x in range(x0, x1 + 1):
        w.set(x, 6, z1, BEAM_X)
    for z in range(z0, z1 + 1):
        w.set(x0, 6, z, BEAM_Z)
    # forge hearth with lava cauldron and chimney
    w.fill(x1 - 4, 1, z0 + 1, x1 - 1, 2, z0 + 3, "bricks")
    w.set(x1 - 3, 2, z0 + 2, "lava_cauldron")
    w.set(x1 - 2, 2, z0 + 2, "lava_cauldron")
    w.fill(x1 - 3, 3, z0 + 1, x1 - 2, 12, z0 + 1, "bricks")
    w.set(x1 - 3, 1, z0 + 2, "campfire[lit=true,signal_fire=true]")
    for z in (z0 + 5, z0 + 7):
        w.set(x1 - 1, 1, z, "blast_furnace[facing=west]")
        w.set(x1 - 1, 2, z, "furnace[facing=west]")
    w.set(x1 - 1, 1, z0 + 9, "blast_furnace[facing=west]")
    w.set(x0 + 3, 1, z0 + 4, "anvil[facing=east]")
    w.set(x0 + 3, 1, z0 + 7, "anvil[facing=east]")
    w.set(x0 + 6, 1, z0 + 4, "smithing_table")
    w.set(x0 + 6, 1, z0 + 7, "grindstone[face=floor,facing=north]")
    w.set(x0 + 2, 1, z1 - 2, "stonecutter[facing=north]")
    w.set(x0 + 4, 1, z1 - 2, "crafting_table")
    w.set(x0 + 5, 1, z1 - 2, "fletching_table")
    w.set(x0 + 2, 1, z0 + 1, "water_cauldron[level=3]")
    for x in range(x0 + 5, x0 + 9):
        w.set(x, 1, z0 + 1, "barrel[facing=up]")
    r = Roof((x0 - 3, x1 + 3, z0 - 3, z1 + 3), 7, kind="gable", axis="x", s0=0.5, s1=1.0, lift=1.0, lift_len=3)
    roof_group(w, [r])
    close_to_roof(w, [(x, z0) for x in range(x0, x1 + 1)] + [(x1, z) for z in range(z0, z1 + 1)], 7, limit=4)
    for (x, z) in ((x0 + 3, z1 - 3), (x0 + 8, z1 - 3)):
        hang(w, x, z, 4, maxup=5)

    # kura (storehouse): two storeys of white plaster, heavy tiled roof
    x0, x1, z0, z1 = 49, 57, -41, -31
    w.fill(x0, -1, z0, x1, 1, z1, "stone_bricks")
    for y in (2, 3):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                w.set(x, y, z, "polished_andesite" if (x + y) % 2 else "white_concrete")
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                w.set(x, y, z, "polished_andesite" if (z + y) % 2 else "white_concrete")
    for y in range(4, 13):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                w.set(x, y, z, PLASTER)
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                w.set(x, y, z, PLASTER)
    w.fill(x0 + 1, 2, z0 + 1, x1 - 1, 12, z1 - 1, AIR)
    w.fill(x0 + 1, 1, z0 + 1, x1 - 1, 1, z1 - 1, "spruce_planks")
    w.fill(x0 + 1, 7, z0 + 1, x1 - 1, 7, z1 - 1, "spruce_planks")
    w.fill(x0 + 1, 12, z0 + 1, x1 - 1, 12, z1 - 1, "spruce_planks")
    # door (west) + small windows with shutters
    for y in (2, 3):
        w.set(x0, y, -36, AIR)
    w.fill(x0, 4, -37, x0, 4, -35, "dark_oak_planks")
    for (x, z) in ((x0, -39), (x0, -33), (x1, -36)):
        w.set(x, 9, z, "iron_bars")
    for z in (z0, z1):
        w.set(53, 9, z, "iron_bars")
    # empty chests in neat rows on both floors
    for fy in (2, 8):
        for z in range(z0 + 1, z1, 2):
            w.set(x1 - 1, fy, z, "chest[facing=west,type=single]")
            w.set(x1 - 1, fy + 1, z, "barrel[facing=west]")
        for x in range(x0 + 2, x1 - 1, 2):
            w.set(x, fy, z0 + 1, "chest[facing=south,type=single]")
    # stairs to the upper floor
    for i in range(5):
        w.set(x0 + 1 + i, 2 + i, z1 - 1, stairs("spruce", "east"))
    for i in range(5, 7):
        w.set(x0 + 1 + i, 7, z1 - 1, AIR)
    w.fill(x0 + 1, 7, z1 - 1, x0 + 6, 7, z1 - 1, AIR)
    andon(w, x0 + 2, 2, z0 + 2)
    andon(w, x0 + 2, 8, z0 + 2)
    r = Roof((x0 - 2, x1 + 2, z0 - 2, z1 + 2), 13, kind="gable", axis="z", s0=0.6, s1=1.15, lift=1.0, lift_len=3)
    roof_group(w, [r], gable_crest="gold_block")
    hang(w, x0 - 1, -36, 5, maxup=10)

    # stable
    x0, x1, z0, z1 = 50, 61, 6, 17
    w.fill(x0, 0, z0, x1, 0, z1, "stone_bricks")
    w.fill(x0 + 1, 0, z0 + 1, x1 - 1, 0, z1 - 1, "packed_mud")
    timber_wall(w, x1, z0, x1, z1, 1, 6, 3, "plaster", nageshi=4)
    timber_wall(w, x0, z0, x1, z0, 1, 6, 3, "plaster", nageshi=4)
    timber_wall(w, x0, z1, x1, z1, 1, 6, 3, "plaster", nageshi=4)
    for z in range(z0, z1 + 1, 3):
        w.fill(x0, 1, z, x0, 6, z, POST)
    for z in range(z0, z1 + 1):
        w.set(x0, 6, z, BEAM_Z)
    # four stalls opening west
    for z in (z0 + 3, z0 + 6, z0 + 9):
        w.fill(x0 + 5, 1, z, x1 - 1, 2, z, "spruce_fence")
    for zs in (z0 + 1, z0 + 4, z0 + 7, z0 + 10):
        w.set(x0 + 5, 1, zs + 1, "spruce_fence_gate[facing=west]")
        w.set(x0 + 5, 1, zs, "spruce_fence")
        w.set(x1 - 1, 1, zs, "hay_block")
        w.set(x1 - 1, 1, zs + 1, "water_cauldron[level=3]")
    r = Roof((x0 - 3, x1 + 2, z0 - 2, z1 + 2), 7, kind="gable", axis="z", s0=0.5, s1=1.0, lift=1.0, lift_len=3)
    roof_group(w, [r])
    close_to_roof(w, perimeter(x0, z0, x1, z1), 7, limit=4)
    for z in (z0 + 3, z1 - 3):
        hang(w, x0 - 1, z, 4, maxup=5)
    # stable yard toward the east gate
    for x in range(46, 62):
        for z in range(18, 25):
            if (x, z) not in T_WATER:
                w.set(x, 0, z, "coarse_dirt" if rng.random() < 0.6 else "gravel")
    for x in range(46, 50):
        w.set(x, 1, 18, "spruce_fence")
    w.set(48, 1, 21, "hay_block")
    w.set(48, 2, 21, "hay_block")
