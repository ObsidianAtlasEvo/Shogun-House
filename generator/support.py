"""Find blocks that would pop off once the world updates them (unsupported plants, lanterns, candles...)."""
import numpy as np

from world import X0, Y0, Z0, parse, is_full_cube, is_leaves, is_air

DIRTLIKE = {"grass_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt", "moss_block", "mud", "farmland",
            "mycelium", "pale_moss_block", "muddy_mangrove_roots"}
PLANTS_ON_DIRT = {"short_grass", "fern", "pink_petals", "wildflowers", "dandelion", "poppy", "blue_orchid", "allium",
                  "azure_bluet", "white_tulip", "pink_tulip", "red_tulip", "orange_tulip", "oxeye_daisy",
                  "cornflower", "lily_of_the_valley", "firefly_bush", "azalea", "flowering_azalea", "bush",
                  "torchflower", "cherry_sapling", "tall_grass", "large_fern"}


def center_support(s):
    n, p = parse(s)
    if is_full_cube(s) or is_leaves(s):
        return True
    if n.endswith("_slab"):
        return p.get("type") in ("top", "double")
    if n.endswith("_stairs"):
        return p.get("half") == "top"
    if n.endswith("_wall") or n.endswith("_fence") or n in ("iron_chain", "lightning_rod", "end_rod"):
        return True
    if n in ("glass", "white_stained_glass", "hay_block", "bookshelf", "barrel", "crafting_table", "target",
             "beehive", "smoker", "furnace", "blast_furnace", "cartography_table", "fletching_table",
             "smithing_table", "loom", "chiseled_bookshelf", "shroomlight"):
        return True
    return False


def check_support(w):
    G = w.g
    P = w.palette
    bad = []
    names = [parse(s) for s in P]
    ids = np.unique(G)
    for i in ids:
        n, p = names[i]
        need = None
        if n in PLANTS_ON_DIRT:
            need = "dirt"
        elif n in ("lantern", "soul_lantern"):
            need = "above" if p.get("hanging") == "true" else "center"
        elif n.endswith("candle") or n.endswith("_button") and p.get("face") == "floor" or n.endswith("pressure_plate"):
            need = "center"
        elif n.endswith("_carpet") or n == "moss_carpet":
            need = "nonair"
        elif n == "sugar_cane":
            need = "cane"
        elif n == "bamboo":
            need = "bamboo"
        elif n in ("wheat", "carrots", "potatoes", "beetroots"):
            need = "farmland"
        elif n == "lily_pad":
            need = "water"
        elif n == "sea_pickle":
            need = "center"
        elif n == "bell":
            need = "above" if p.get("attachment") == "ceiling" else None
        elif n.endswith("_wall_banner"):
            need = "wall"
        if not need:
            continue
        for (x, y, z) in np.argwhere(G == i):
            below = P[G[x, y - 1, z]]
            above = P[G[x, y + 1, z]]
            bn = parse(below)[0]
            ok = True
            if need == "dirt":
                ok = bn in DIRTLIKE
            elif need == "center":
                ok = center_support(below)
            elif need == "above":
                an, ap = parse(above)
                ok = center_support(above) or an == "iron_chain" or \
                    (an.endswith("_slab") and ap.get("type", "bottom") == "bottom") or \
                    (an.endswith("_stairs") and ap.get("half", "bottom") == "bottom")
            elif need == "nonair":
                ok = not is_air(below)
            elif need == "farmland":
                ok = bn == "farmland"
            elif need == "water":
                ok = bn == "water"
            elif need == "bamboo":
                ok = bn in DIRTLIKE | {"bamboo", "gravel", "sand"}
            elif need == "cane":
                if bn == "sugar_cane":
                    ok = True
                else:
                    ok = bn in DIRTLIKE | {"sand"} and any(
                        parse(P[G[x + a, y - 1, z + b]])[0] == "water" for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            elif need == "wall":
                f = p.get("facing", "north")
                dx, dz = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}[f]
                ok = is_full_cube(P[G[x + dx, y, z + dz]])
            if not ok:
                bad.append(((int(x) + X0, int(y) + Y0, int(z) + Z0), P[i], below if need != "above" else above))
    return bad
