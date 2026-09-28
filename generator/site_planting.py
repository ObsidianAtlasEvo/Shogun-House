"""Planting plan: ~37 hand-shaped cherry trees in deliberate archetypes, niwaki pines,
bamboo groves, clipped azaleas, fireflies and ground cover."""
import math

from world import AIR, is_air, parse
import nature as N
import site_terrain as T

# (x, z, height, spread, trunk_r, branches, style, lean, extras)
CHERRIES = [
    # --- Moon Garden: the ancient island tree is the heart of the estate
    (-6, -44, 19, 12, 1.8, 7, "spreading", (0.0, 0.0), dict(lantern=5, glow=True, clearance=8)),
    (-49, -38, 12, 8, 1.0, 5, "classic", (0.45, -0.1), dict(glow=True)),
    (24, -30, 11, 7, 0.9, 5, "classic", (-0.25, -0.45), {}),
    (-60, -44, 10, 6, 0.9, 4, "weeping", (0.2, 0.0), {}),
    (12, -29, 8, 6, 0.8, 4, "spreading", (0.0, -0.3), {}),
    # north berm grove (frames the garden, hides the plains)
    (-38, -59, 13, 8, 1.1, 5, "classic", (0.0, 0.1), {}),
    (-22, -60, 14, 9, 1.2, 6, "classic", (0.1, 0.1), {}),
    (-50, -58, 11, 7, 1.0, 5, "classic", (0.1, 0.1), {}),
    (23, -58, 12, 8, 1.0, 5, "classic", (-0.1, 0.1), {}),
    (30, -50, 10, 7, 0.9, 5, "spreading", (0.0, 0.0), dict(beehive=True)),
    (-9, -60, 12, 8, 1.0, 5, "classic", (0.0, 0.2), {}),
    # shrine
    (37, -58, 11, 7, 1.0, 5, "classic", (0.1, 0.1), dict(beehive=True)),
    (58, -47, 10, 6, 0.9, 4, "weeping", (-0.2, 0.0), {}),
    (57, -60, 12, 7, 1.0, 5, "classic", (-0.1, 0.1), {}),
    # forecourt: two big gate cherries and a stream-side leaner
    (-13, 51, 12, 7, 1.1, 6, "classic", (0.1, 0.0), dict(glow=True)),
    (14, 48, 11, 7, 1.0, 5, "classic", (-0.1, 0.05), dict(glow=True)),
    (-13, 29, 10, 7, 0.9, 5, "classic", (0.35, 0.2), {}),
    # dojo
    (-28, 51, 10, 6, 0.9, 5, "classic", (0.0, 0.0), {}),
    # tea garden
    (27, 30, 11, 7, 1.0, 5, "classic", (0.3, 0.4), dict(glow=True)),
    (50, 53, 12, 7, 1.0, 5, "classic", (-0.2, -0.1), {}),
    (22, 55, 10, 6, 0.9, 5, "weeping", (0.1, -0.1), {}),
    # bath & private garden
    (-47, -8, 8, 6, 0.8, 4, "spreading", (0.1, 0.0), {}),
    (-40, 9, 11, 7, 1.0, 5, "classic", (0.2, -0.1), {}),
    (-24, 11, 9, 6, 0.9, 4, "weeping", (0.0, -0.1), {}),
    # service
    (44, 21, 10, 6, 0.9, 5, "classic", (0.0, 0.0), {}),
    # approach: cherry tunnel over the lantern avenue (kept clear of the torii)
    (-8, 75, 10, 5, 0.9, 5, "classic", (0.3, 0.0), dict(glow=True)),
    (8, 77, 10, 5, 0.9, 5, "classic", (-0.3, 0.0), {}),
    (-8, 83, 9, 5, 0.9, 4, "classic", (0.3, 0.0), {}),
    (8, 84, 9, 5, 0.9, 4, "classic", (-0.3, 0.0), dict(glow=True)),
    # approach: entry grove that hides the estate until the bend
    (-40, 104, 13, 8, 1.1, 5, "classic", (0.1, 0.0), {}),
    (-18, 105, 10, 7, 0.9, 5, "classic", (0.0, 0.0), {}),
    (13, 100, 12, 8, 1.0, 5, "classic", (0.0, 0.0), {}),
    (28, 104, 13, 8, 1.1, 5, "classic", (0.0, 0.0), {}),
    (39, 97, 11, 7, 1.0, 5, "classic", (0.0, 0.0), {}),
]

PINES = [(-17, -25, 6, 4), (17, -24, 6, 4), (47, 45, 6, 3.5), (-44, -48, 7, 4), (36, -48, 6, 3.5)]


def plant(w, rng, water):
    trees = []
    for (x, z, h, sp, tr, br, style, lean, ex) in CHERRIES:
        gy = N.surface_y(w, x, z, 20)
        if gy is None:
            continue
        ends = N.cherry(w, x, gy + 1, z, rng, height=h, spread=sp, trunk_r=tr, branches=br, style=style,
                        lean=lean, ground_y=gy, lantern=ex.get("lantern"), glow=ex.get("glow", False),
                        clearance=ex.get("clearance"))
        trees.append((x, gy + 1, z, h))
        N.close_canopy(w, x - sp - 6, x + sp + 6, gy + 2, gy + h + 6, z - sp - 6, z + sp + 6)
        N.hide_inner_wood(w, x - sp - 6, x + sp + 6, gy + 4, gy + h + 6, z - sp - 6, z + sp + 6)
        if ex.get("beehive"):
            done = False
            for y in range(gy + 2, gy + 6):
                for (dx, dz, f) in ((0, 1, "south"), (1, 0, "east"), (-1, 0, "west"), (0, -1, "north")):
                    if parse(w.get(x, y, z))[0] == "cherry_wood" and is_air(w.get(x + dx, y, z + dz)):
                        w.set(x + dx, y, z + dz, f"beehive[facing={f},honey_level=0]")
                        done = True
                        break
                if done:
                    break
    for (x, z, h, sp) in PINES:
        gy = N.surface_y(w, x, z, 20)
        if gy is not None:
            N.pine(w, x, gy + 1, z, rng, height=h, pads=5, spread=sp)
    return trees


def bamboo(w, rng, water):
    def ok(x, z):
        return (x, z) not in water

    def band(x0, x1, z0, z1, dens, hmin=9, hmax=15, skip=None):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if not ok(x, z) or rng.random() > dens or (skip and skip(x, z)):
                    continue
                gy = N.surface_y(w, x, z, 12)
                if gy is not None:
                    N.bamboo_stalk(w, x, z, gy, rng, hmin, hmax)
    # west screen along the wall and around the bath house
    band(-61, -58, -45, 14, 0.5, skip=lambda x, z: -35 <= z <= -1 and x >= -61 and False)
    band(-61, -45, -44, -36, 0.35)
    band(-47, -45, -22, -4, 0.45)
    band(-61, -59, -22, -2, 0.5)
    # hedge between dojo and archery range
    band(-50, -48, 19, 55, 0.55)
    # bamboo beside the waterfall
    band(0, 4, -62, -57, 0.55, 11, 16)
    band(11, 15, -62, -58, 0.55, 11, 16)
    # east screen behind the kura and smithy
    band(59, 61, -43, -28, 0.5)
    # NW corner grove behind the pavilion
    band(-61, -55, -62, -58, 0.45)
    # private garden corner
    band(-44, -42, 8, 14, 0.5)


def shrubs_and_cover(w, rng, water):
    def near_water(x, z):
        return any((x + a, z + b) in water for a in (-1, 0, 1) for b in (-1, 0, 1))
    mounds = [(-20, -27, 1.6), (20, -26, 1.5), (-45, -14, 1.8), (-18, 14, 1.5), (18, 15, 1.6), (26, 16, 1.4),
              (-26, 16, 1.4), (-52, -36, 1.8), (-42, -58, 1.6), (18, -52, 1.6), (32, -40, 1.8), (-30, -44, 1.3),
              (10, -36, 1.2), (30, 22, 1.5), (44, 28, 1.3), (-15, 57, 1.4), (15, 57, 1.4), (-18, 45, 1.5),
              (20, 42, 1.3), (-40, 44, 1.4), (38, -46, 1.2), (-36, -12, 1.4), (-22, -10, 1.3), (6, -60, 1.6)]
    for (x, z, r) in mounds:
        gy = N.surface_y(w, x, z, 12)
        if gy is not None and (x, z) not in water:
            N.azalea_mound(w, x, gy + 1, z, r, rng, flowering=0.55)
    # fireflies along pond margins and the approach stream
    cand = []
    for (x, z) in list(water.keys()):
        for a, b in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            n = (x + a, z + b)
            if n not in water:
                cand.append(n)
    rng.shuffle(cand)
    placed = 0
    for (x, z) in cand:
        if placed >= 38:
            break
        gy = N.surface_y(w, x, z, 8)
        if gy is None or not is_air(w.get(x, gy + 1, z)):
            continue
        if parse(w.get(x, gy, z))[0] in ("grass_block", "moss_block", "dirt"):
            w.set(x, gy + 1, z, "firefly_bush")
            placed += 1
    # grasses, ferns & small flowers in the soft areas
    def excl(x, z):
        return (x, z) in water
    N.ground_cover(w, -62, 62, -62, 62, rng, 12, p_grass=0.006, p_fern=0.006, p_flower=0.008, exclude=excl)
    N.ground_cover(w, -44, 44, 86, 108, rng, 6, p_grass=0.01, p_fern=0.0, p_flower=0.02,
                   flowers=("oxeye_daisy", "azure_bluet", "pink_tulip", "white_tulip", "cornflower"), exclude=excl)


def water_life(w, rng, water):
    """Lily pads on the ponds, and the soft submerged glow: lichen and sea pickles on the beds."""
    ponds = [(x, z) for (x, z), (ws, bed) in water.items() if ws == T.WATER_Y]
    rng.shuffle(ponds)
    pads = glow = pick = 0
    for (x, z) in ponds:
        ws, bed = water[(x, z)]
        if w.get(x, ws, z) != "water" or not is_air(w.get(x, ws + 1, z)):
            continue
        if pads < 70 and rng.random() < 0.5 and w.get(x, ws - 1, z) == "water":
            # keep pads off the plunge pool and away from walls
            if not (-2 <= x <= 12 and z <= -50):
                w.set(x, ws + 1, z, "lily_pad")
                pads += 1
                continue
        if bed + 1 <= ws and w.get(x, bed + 1, z) == "water" and parse(w.get(x, bed, z))[0] in ("gravel", "clay"):
            if glow < 60 and rng.random() < 0.6:
                w.set(x, bed + 1, z, "glow_lichen[down=true,waterlogged=true]")
                glow += 1
            elif pick < 24:
                w.set(x, bed + 1, z, f"sea_pickle[pickles={rng.choice((1, 2))},waterlogged=true]")
                pick += 1
    return pads, glow, pick


UPLIGHT = [(-6, -44), (-13, 51), (14, 48), (27, 30), (-49, -38), (-8, 75), (8, 84), (37, -58)]


def uplights(w):
    """Invisible light tucked beside the trunks of the feature trees: lit bark and underside of the blossom."""
    for (x, z) in UPLIGHT:
        gy = N.surface_y(w, x, z, 20)
        for (dx, dz) in ((2, 1), (-2, -1), (1, -2)):
            X, Z = x + dx, z + dz
            g = N.surface_y(w, X, Z, gy + 3 if gy is not None else 10)
            if g is not None and is_air(w.get(X, g + 1, Z)) and is_air(w.get(X, g + 2, Z)):
                w.set(X, g + 1, Z, "light[level=10]")
                break
