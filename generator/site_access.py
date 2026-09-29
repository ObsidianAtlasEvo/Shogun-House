"""Access & circulation: every entrance, podium edge, veranda and threshold gets a
proper walkable flight (each step half a block, no jumping), plus shoe-stones
(kutsunugi-ishi) in front of verandas and a stepping-stone path to the pavilion.

Uses its own RNG so it never disturbs the random layout of the rest of the estate."""
import random

from world import AIR, is_air, parse
import nature as N
import site_terrain as T

OUT = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
BACK = {"north": "south", "south": "north", "east": "west", "west": "east"}
SOFT = {"short_grass", "fern", "pink_petals", "wildflowers", "firefly_bush", "light", "bamboo", "sugar_cane",
        "white_tulip", "pink_tulip", "lily_of_the_valley", "azure_bluet", "oxeye_daisy", "cornflower"}


def flight(w, cells, direction, top, bottom, mat="polished_andesite", support="stone_bricks", headroom=3):
    """Stair flight descending outward from a platform edge.

    cells:     platform edge cells (x, z) - the last cells you stand on up top
    direction: outward direction of travel going down
    top:       standing height on the platform (y of the air block you stand in)
    bottom:    standing height at the foot of the flight
    Step k (1..top-bottom) sits k cells out with its block at y = top - k, so the
    last step rests exactly on the ground at the foot - never sunk into it.
    """
    dx, dz = OUT[direction]
    face = BACK[direction]
    for (x, z) in cells:
        for k in range(1, top - bottom + 1):
            cx, cz = x + dx * k, z + dz * k
            y = top - k
            w.set(cx, y, cz, f"{mat}_stairs[facing={face},half=bottom]")
            for yy in range(bottom - 1, y):
                w.set(cx, yy, cz, support)
            for yy in range(y + 1, y + 1 + headroom):
                if not is_air(w.get(cx, yy, cz)):
                    w.set(cx, yy, cz, AIR)
        # the ground right at the foot must be clear to step onto
        fx, fz = x + dx * (top - bottom + 1), z + dz * (top - bottom + 1)
        for yy in range(bottom, bottom + 2):
            if parse(w.get(fx, yy, fz))[0] in SOFT:
                w.set(fx, yy, fz, AIR)


def shoe_stones(w, cells, y, mat="smooth_stone_slab[type=bottom]"):
    """Half-block stepping stone in front of a veranda: podium -> stone -> deck without jumping."""
    for (x, z) in cells:
        w.set(x, y, z, mat)
        for yy in (y + 1, y + 2):
            if not is_air(w.get(x, yy, z)):
                w.set(x, yy, z, AIR)


def _ground(w, x, z, ymax):
    for y in range(ymax, -8, -1):
        s = w.get(x, y, z)
        n = parse(s)[0]
        if is_air(s) or n in SOFT or n.endswith("_leaves"):
            continue
        return y
    return None


def stepping_path(w, pts, rng):
    """Flush stepping stones through the garden; clears bamboo/plants off the line and
    puts a stone step wherever the ground rises or falls by a block along the way."""
    order = []
    for i in range(len(pts) - 1):
        (ax, az), (bx, bz) = pts[i], pts[i + 1]
        n = max(abs(bx - ax), abs(bz - az))
        for s in range(n + 1):
            t = s / max(n, 1)
            c = (round(ax + (bx - ax) * t), round(az + (bz - az) * t))
            if not order or order[-1] != c:
                if order and abs(order[-1][0] - c[0]) + abs(order[-1][1] - c[1]) == 2:
                    order.append((c[0], order[-1][1]))   # keep the line 4-connected
                order.append(c)
    ground = {}
    for (x, z) in order:
        g = _ground(w, x, z, 6)
        if g is None or parse(w.get(x, g, z))[0] == "water" or parse(w.get(x, g, z))[0].endswith("_wood"):
            continue
        for yy in range(g + 1, g + 16):
            if parse(w.get(x, yy, z))[0] in SOFT or parse(w.get(x, yy, z))[0] in ("azalea_leaves",
                                                                                  "flowering_azalea_leaves"):
                w.set(x, yy, z, AIR)
        if parse(w.get(x, g, z))[0] in ("grass_block", "moss_block", "dirt", "coarse_dirt", "podzol"):
            w.set(x, g, z, "polished_andesite" if rng.random() < 0.7 else "moss_block")
        ground[(x, z)] = g
    for (a, b) in zip(order, order[1:]):
        if a not in ground or b not in ground:
            continue
        ga, gb = ground[a], ground[b]
        if abs(ga - gb) != 1:
            continue
        low, high = (a, b) if ga < gb else (b, a)
        dx, dz = high[0] - low[0], high[1] - low[1]
        face = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}[(dx, dz)]
        y = min(ga, gb) + 1
        w.set(low[0], y, low[1], f"mossy_stone_brick_stairs[facing={face},half=bottom]")
        for yy in (y + 1, y + 2):
            if not is_air(w.get(low[0], yy, low[1])):
                w.set(low[0], yy, low[1], AIR)


def access(w):
    rng = random.Random(4217)
    # --- Great Hall: entrance porch down to the forecourt (the flight in the screenshot)
    flight(w, [(x, 10) for x in range(-4, 5)], "south", 4, 1)
    # stone cheek blocks either side of the flight
    for x in (-5, 5):
        for z, y in ((11, 3), (12, 2), (13, 1)):
            w.set(x, y, z, "polished_andesite_slab[type=bottom]" if y == 1 else "stone_bricks")
            w.set(x, y - 1, z, "stone_bricks")
    # decorative strut under the porch beam: timber, not a floating white block
    w.set(0, 8, 10, "stripped_dark_oak_wood[axis=x]")
    # --- verandas <-> podium: shoe-stones where the gravel terrace meets a deck
    shoe_stones(w, [(x, -24) for x in (-9, -8, -7, 7, 8, 9)], 3)          # hall rear, to the moon bridge terrace
    shoe_stones(w, [(-18, z) for z in (-11, -10, -9)], 3)                 # hall west side
    shoe_stones(w, [(x, 3) for x in (-9, -8, 8, 9)], 3)                   # hall front beside the porch
    # --- podium edges down to the gardens
    flight(w, [(x, 11) for x in (28, 29, 30)], "south", 4, 1)          # East Wing -> tea garden / forecourt
    flight(w, [(x, -16) for x in (-32, -31, -30)], "south", 4, 1)      # West Wing -> private garden
    flight(w, [(x, -11) for x in (39, 40, 41)], "north", 4, 1)         # East Wing -> shrine sando
    flight(w, [(-41, z) for z in (-34, -33, -32)], "west", 4, 1)       # West Wing -> pavilion path
    # --- dojo (floor stands 2 above the yard)
    flight(w, [(x, 40) for x in (-37, -36, -35)], "south", 3, 1, mat="stone_brick")
    flight(w, [(-26, z) for z in (31, 32)], "east", 3, 1, mat="stone_brick")
    # --- archery hall
    flight(w, [(x, 49) for x in (-55, -54, -53)], "north", 3, 1, mat="stone_brick")
    # --- moon pavilion: base, then floor; path from the West Wing flight
    # the western shoulder rises to meet the pavilion, so only the east half needs a step
    flight(w, [(x, -50) for x in (-55, -54)], "south", 3, 2, mat="stone_brick")
    stepping_path(w, [(-45, -33), (-48, -34), (-52, -36), (-53, -41), (-54, -45), (-55, -47)], rng)
    # --- retainers' row house doors
    flight(w, [(x, 56) for x in (-35, -28, -21, -14)], "north", 2, 1, mat="stone_brick")
    # --- tea house: south door and the roji arrival
    flight(w, [(x, 42) for x in (47, 48, 49)], "south", 2, 1, mat="spruce")
    flight(w, [(39, 31)], "west", 2, 1, mat="spruce")
    # --- bath house: south door, corridor ends
    flight(w, [(x, -24) for x in (-56, -55, -54)], "south", 2, 1, mat="spruce")
    flight(w, [(-48, z) for z in (-29, -28, -27)], "west", 3, 2, mat="spruce", support="spruce_planks")
    flight(w, [(-43, z) for z in (-29, -28, -27)], "west", 4, 3, mat="spruce", support="spruce_planks")
    # --- kitchen corridor, kitchen south door, kura door
    flight(w, [(41, z) for z in (-6, -5, -4)], "east", 4, 3, mat="spruce", support="spruce_planks")
    flight(w, [(44, z) for z in (-6, -5, -4)], "east", 3, 2, mat="spruce", support="spruce_planks")
    flight(w, [(52, 2)], "south", 2, 1, mat="stone_brick")
    flight(w, [(49, -36)], "west", 2, 1, mat="stone_brick")
    # --- shrine hall: base -> floor
    flight(w, [(x, -50) for x in range(47, 52)], "south", 7, 6, mat="stone_brick")
    # --- thresholds: main gate and service gate step down to the plains outside
    flight(w, [(x, 62) for x in range(-3, 4)], "south", 1, 0, mat="stone_brick")
    flight(w, [(62, z) for z in range(19, 24)], "east", 1, 0, mat="stone_brick", support="cobblestone")
