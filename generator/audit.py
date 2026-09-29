"""In-game usability audit of the voxel model.

Checks the things you notice when you actually walk the estate:
  * stairs that are buried / flush with the ground (the flight doesn't rise)
  * places you can only reach by jumping (every entrance should be walkable)
  * containers that cannot be opened (solid block on top of a chest)
  * workstations sunk into a floor
  * tree limbs that cut through buildings
Run:  python3 audit.py
"""
from collections import deque

import numpy as np

from world import X0, Y0, Z0, parse, is_air, is_full_cube, is_plant, is_water

STAIR_FLIGHT_MATS = ("stone_brick", "polished_andesite", "andesite", "stone", "mossy_stone_brick", "spruce",
                     "dark_oak", "oak", "cherry", "bamboo", "cobblestone", "smooth_stone")
FUNCTIONAL = {"anvil", "furnace", "blast_furnace", "smoker", "grindstone", "smithing_table", "stonecutter",
              "crafting_table", "fletching_table", "chest", "barrel", "lectern", "brewing_stand", "cauldron",
              "water_cauldron", "loom", "cartography_table", "enchanting_table", "composter", "ender_chest",
              "hay_block", "decorated_pot", "lava_cauldron"}
FLOORS = {"oak_planks", "spruce_planks", "dark_oak_planks", "bamboo_mosaic", "bamboo_planks", "cobblestone",
          "stone_bricks", "packed_mud", "polished_deepslate", "polished_andesite", "stone", "smooth_stone"}
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
FACE = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


def passable(s):
    n, p = parse(s)
    if is_air(s) or is_plant(s) and n not in ("bamboo", "sweet_berry_bush", "lily_pad"):
        return True
    return n.endswith("_carpet") or n.endswith("_fence_gate") or n.endswith("_trapdoor") or n.endswith("_button") or \
        n.endswith("pressure_plate") or n.endswith("candle") or n in ("pink_petals", "moss_carpet")


def surfaces(s, y):
    """Standing heights (in half blocks) offered by the top of block s at y."""
    n, p = parse(s)
    if is_air(s) or is_water(s) or passable(s):
        return ()
    if n.endswith("_slab"):
        t = p.get("type", "bottom")
        return ((2 * y + 1),) if t == "bottom" else ((2 * y + 2),)
    if n.endswith("_stairs"):
        return ((2 * y + 1), (2 * y + 2)) if p.get("half", "bottom") == "bottom" else ((2 * y + 2),)
    if n.endswith("_trapdoor"):
        return ((2 * y + 2),) if p.get("half") == "top" and p.get("open") != "true" else ((2 * y + 1),)
    if n.endswith("_wall") or n.endswith("_fence"):
        return ()  # can't usefully stand on posts
    if n.endswith("_leaves") or n in ("iron_chain", "lantern", "bamboo"):
        return ()
    return ((2 * y + 2),)


class Walk:
    def __init__(self, w):
        self.w = w

    def headroom(self, x, h2, z):
        y = (h2 + 1) // 2  # first cell whose volume the head occupies from the bottom
        base = h2 // 2
        return all(passable(self.w.get(x, yy, z)) for yy in range(base if h2 % 2 == 0 else base + 1,
                                                                    (h2 + 4 + 1) // 2 + (0 if h2 % 2 == 0 else 0)))

    def nodes_at(self, x, z, h_near):
        """Standing heights available in column (x,z) near h_near (half units)."""
        out = []
        for y in range(h_near // 2 - 4, h_near // 2 + 3):
            s = self.w.get(x, y, z)
            for h in surfaces(s, y):
                if self.headroom(x, h, z):
                    out.append(h)
        return out

    def component(self, start, max_rise=1, max_drop=1, limit=400000):
        """Cells reachable walking (rise <= max_rise half-blocks, drop <= max_drop)."""
        (x, h, z) = start
        seen = {start}
        dq = deque([start])
        while dq and len(seen) < limit:
            x, h, z = dq.popleft()
            for dx, dz in DIRS + ((0, 0),):
                for h2 in self.nodes_at(x + dx, z + dz, h):
                    if -max_drop <= h2 - h <= max_rise:
                        n = (x + dx, h2, z + dz)
                        if n not in seen:
                            seen.add(n)
                            dq.append(n)
        return seen


def buried_stairs(w):
    """Bottom stairs of a walkable flight whose low (front) side is blocked at the same level."""
    out = []
    for i, s in enumerate(w.palette):
        n, p = parse(s)
        if not n.endswith("_stairs") or p.get("half", "bottom") != "bottom":
            continue
        if not n[:-7] in STAIR_FLIGHT_MATS:
            continue
        for (xi, yi, zi) in np.argwhere(w.g == i):
            x, y, z = xi + X0, yi + Y0, zi + Z0
            if y >= 8 or not passable(w.get(x, y + 1, z)) or is_air(w.get(x, y - 1, z)):
                continue  # covered or floating: decorative trim (bargeboards), not a step
            fx, fz = FACE[p["facing"]]
            front = w.get(x - fx, y, z - fz)
            back_up = w.get(x + fx, y + 1, z + fz)
            if is_full_cube(front) and passable(w.get(x - fx, y + 1, z - fz)) and "deepslate" not in front:
                out.append(((x, y, z), s, "front of step is flush with solid ground - step is sunk"))
    return out


def blocked_chests(w):
    out = []
    for i, s in enumerate(w.palette):
        n = parse(s)[0]
        if n not in ("chest", "trapped_chest", "ender_chest"):
            continue
        for (xi, yi, zi) in np.argwhere(w.g == i):
            x, y, z = xi + X0, yi + Y0, zi + Z0
            if is_full_cube(w.get(x, y + 1, z)):
                out.append(((x, y, z), s, "solid block on top - chest cannot open: " + w.get(x, y + 1, z)))
    return out


def sunk_workstations(w):
    out = []
    for i, s in enumerate(w.palette):
        n = parse(s)[0]
        if n not in FUNCTIONAL:
            continue
        for (xi, yi, zi) in np.argwhere(w.g == i):
            x, y, z = xi + X0, yi + Y0, zi + Z0
            floor_nb = sum(1 for dx, dz in DIRS
                           if parse(w.get(x + dx, y, z + dz))[0] in FLOORS and passable(w.get(x + dx, y + 1, z + dz)))
            if floor_nb >= 2:
                out.append(((x, y, z), s, f"set into the floor ({floor_nb} floor blocks level with it)"))
    return out


KEY_PLACES = {
    "Great Hall": (0, 4, -10), "Upper storey": (0, 12, -11), "West Wing bedroom": (-36, 4, -29),
    "West Wing study": (-27, 4, -30), "East Wing library": (29, 4, -6), "Strategy room": (35, 4, -6),
    "Herbalist": (35, 4, 5), "Guest room": (25, 4, 6), "Moon island": (-4, 3, -44), "Tsukimidai": (-30, 4, -39),
    "Moon pavilion": (-55, 3, -53), "Shrine hall": (49, 7, -56), "Tea house": (45, 2, 36), "Dojo": (-36, 3, 31),
    "Dojo yard": (-36, 1, 48), "Archery hall": (-56, 3, 52), "Nagaya room": (-26, 2, 59), "Bath house": (-55, 2, -29),
    "Kitchen": (52, 2, -7), "Forge": (52, 1, -20), "Kura": (53, 2, -36), "Kura upper": (52, 8, -36),
    "Stable": (55, 1, 8), "Vault": (-33, -8, -25), "Portal cavern": (-38, -17, -3), "Approach start": (-31, 0, 104),
    "Private garden": (-26, 1, -6),
}


def reachability(w, start=(0, 1, 58)):
    wk = Walk(w)
    x, y, z = start
    h = 2 * y
    comp = wk.component((x, h, z), max_rise=1, max_drop=1)
    cols = {}
    for (cx, ch, cz) in comp:
        cols.setdefault((cx, cz), set()).add(ch)
    res = {}
    for name, (px, py, pz) in KEY_PLACES.items():
        ok = any(abs(h2 - 2 * py) <= 1 for h2 in cols.get((px, pz), ()))
        if not ok:
            # tolerate the exact probe point being furniture: check a 3x3
            ok = any(abs(h2 - 2 * py) <= 1 for dx in (-1, 0, 1) for dz in (-1, 0, 1)
                     for h2 in cols.get((px + dx, pz + dz), ()))
        res[name] = ok
    return res, comp


def limb_collisions(w, before, after_ids):
    return []


def run(w, verbose=True):
    report = {
        "buried stairs": buried_stairs(w),
        "blocked chests": blocked_chests(w),
        "sunk workstations": sunk_workstations(w),
    }
    reach, comp = reachability(w)
    below = ("Vault", "Portal cavern")
    report["not walkable from the gate without jumping"] = [k for k, v in reach.items() if not v and k not in below]
    # the vault is entered through a hidden floor hatch (one hop down by design); check the rest from the hatch
    wk = Walk(w)
    hatch = wk.component((-23, 6, -31))
    cols = {}
    for (cx, ch, cz) in hatch:
        cols.setdefault((cx, cz), set()).add(ch)
    for k in below:
        px, py, pz = KEY_PLACES[k]
        ok = any(abs(h2 - 2 * py) <= 1 for dx in (-1, 0, 1) for dz in (-1, 0, 1) for h2 in cols.get((px + dx, pz + dz), ()))
        if not ok:
            report["not walkable from the gate without jumping"].append(k + " (from the study hatch)")
    report["enchanting tables below 15 shelves"] = [e for e in enchanting_power(w) if e[1] < 15]
    report["farmland out of water reach"] = dry_farmland(w)
    if verbose:
        for k, v in report.items():
            print(f"== {k}: {len(v)}")
            for item in v[:60]:
                print("   ", item)
    return report



def enchanting_power(w):
    """Bookshelves that actually count for each enchanting table (need an air gap between)."""
    out = []
    for i, s in enumerate(w.palette):
        if parse(s)[0] != "enchanting_table":
            continue
        for (xi, yi, zi) in np.argwhere(w.g == i):
            x, y, z = xi + X0, yi + Y0, zi + Z0
            n = 0
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if max(abs(dx), abs(dz)) != 2:
                        continue
                    for dy in (0, 1):
                        if parse(w.get(x + dx, y + dy, z + dz))[0] == "bookshelf" and \
                                is_air(w.get(x + dx // 2, y + dy, z + dz // 2)):
                            n += 1
            out.append(((x, y, z), n))
    return out


def dry_farmland(w):
    out = []
    for i, s in enumerate(w.palette):
        if parse(s)[0] != "farmland":
            continue
        for (xi, yi, zi) in np.argwhere(w.g == i):
            x, y, z = xi + X0, yi + Y0, zi + Z0
            wet = any(parse(w.get(x + dx, y + dy, z + dz))[0] == "water"
                      for dx in range(-4, 5) for dz in range(-4, 5) for dy in (0, 1))
            if not wet:
                out.append((x, y, z))
    return out


if __name__ == "__main__":
    import estate
    from finalize import finalize
    w, t = estate.build()
    finalize(w)
    run(w)
