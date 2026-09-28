"""Preview renderer: isometric day/night views and a top-down plan, rendered
from the voxel model at half-block resolution so stairs and slabs read correctly."""
import hashlib

import numpy as np
from PIL import Image

from world import X0, Y0, Z0, parse, is_air, light_emission, is_water, is_leaves

C = {
    "dark_oak_planks": (67, 43, 22), "dark_oak_log": (60, 46, 28), "stripped_dark_oak_log": (78, 57, 36),
    "stripped_dark_oak_wood": (78, 57, 36), "dark_oak_wood": (60, 46, 28),
    "spruce_planks": (115, 85, 49), "stripped_spruce_log": (116, 90, 52), "spruce_log": (58, 37, 16),
    "stripped_spruce_wood": (116, 90, 52), "spruce_wood": (58, 37, 16),
    "cherry_planks": (227, 179, 173), "cherry_log": (55, 33, 45), "cherry_wood": (55, 33, 45),
    "stripped_cherry_log": (216, 146, 150), "stripped_cherry_wood": (216, 146, 150),
    "cherry_leaves": (232, 170, 198), "bamboo_planks": (194, 173, 80), "bamboo_mosaic": (190, 168, 76),
    "bamboo": (95, 146, 30), "bamboo_block": (127, 144, 58), "stripped_bamboo_block": (192, 172, 78),
    "oak_planks": (162, 130, 78), "oak_log": (109, 85, 50), "birch_planks": (196, 179, 123),
    "pale_oak_planks": (228, 217, 213), "stripped_oak_log": (177, 144, 86), "stripped_oak_wood": (177, 144, 86),
    "deepslate_tiles": (52, 52, 56), "polished_deepslate": (72, 72, 74), "cobbled_deepslate": (78, 78, 82),
    "chiseled_deepslate": (56, 56, 58), "deepslate_bricks": (70, 70, 72), "deepslate": (80, 80, 82),
    "stone_bricks": (122, 121, 122), "mossy_stone_bricks": (112, 120, 100), "cracked_stone_bricks": (118, 117, 118),
    "chiseled_stone_bricks": (119, 118, 119), "stone": (125, 125, 125), "smooth_stone": (160, 160, 160),
    "andesite": (136, 136, 137), "polished_andesite": (132, 135, 134), "cobblestone": (125, 125, 125),
    "mossy_cobblestone": (106, 118, 92), "tuff": (108, 109, 102), "tuff_bricks": (98, 102, 95),
    "polished_tuff": (97, 104, 99), "calcite": (223, 224, 220), "gravel": (131, 127, 126),
    "coarse_dirt": (119, 85, 59), "dirt": (134, 96, 67), "grass_block": (103, 156, 66), "moss_block": (89, 112, 45),
    "moss_carpet": (89, 112, 45), "podzol": (91, 63, 24), "rooted_dirt": (144, 103, 76), "mud": (60, 57, 61),
    "packed_mud": (142, 106, 79), "mud_bricks": (137, 104, 79), "dirt_path": (148, 122, 65), "sand": (219, 207, 163),
    "white_concrete": (212, 216, 217), "white_concrete_powder": (226, 228, 228),
    "light_gray_concrete_powder": (170, 170, 164), "white_terracotta": (209, 178, 161),
    "smooth_quartz": (236, 230, 223), "quartz_block": (236, 230, 223), "clay": (160, 166, 179),
    "water": (44, 88, 190), "lily_pad": (40, 130, 50), "sea_pickle": (110, 140, 50), "glow_lichen": (112, 140, 120),
    "lantern": (255, 196, 110), "shroomlight": (245, 150, 72), "campfire": (210, 120, 50),
    "pink_candle": (220, 110, 170), "white_candle": (225, 225, 215), "candle": (230, 210, 160),
    "red_concrete": (155, 36, 34), "red_terracotta": (143, 61, 46), "polished_blackstone": (53, 49, 57),
    "blackstone": (42, 36, 41), "gold_block": (246, 208, 61), "oxidized_copper": (82, 162, 132),
    "pink_petals": (246, 170, 206), "short_grass": (100, 150, 60), "fern": (88, 140, 60), "tall_grass": (100, 150, 60),
    "large_fern": (88, 140, 60), "azalea": (101, 124, 47), "flowering_azalea": (150, 115, 130),
    "azalea_leaves": (90, 118, 44), "flowering_azalea_leaves": (140, 120, 115), "spruce_leaves": (55, 88, 58),
    "dark_oak_leaves": (60, 100, 40), "oak_leaves": (70, 120, 40), "mangrove_leaves": (80, 130, 40),
    "white_stained_glass": (235, 235, 230), "white_stained_glass_pane": (235, 235, 230), "glass_pane": (200, 220, 230),
    "bookshelf": (117, 94, 59), "barrel": (140, 106, 60), "chest": (160, 110, 40), "hay_block": (166, 139, 12),
    "target": (226, 170, 157), "farmland": (81, 44, 15), "wheat": (205, 185, 80), "firefly_bush": (80, 95, 40),
    "obsidian": (18, 12, 28), "crying_obsidian": (34, 10, 62), "nether_portal": (110, 20, 200),
    "sugar_cane": (140, 185, 95), "white_tulip": (230, 235, 225), "pink_tulip": (240, 170, 200),
    "lily_of_the_valley": (240, 240, 240), "allium": (180, 120, 210), "blue_orchid": (40, 160, 220),
    "peony": (230, 170, 220), "lilac": (200, 150, 210), "rose_bush": (190, 40, 40), "iron_chain": (50, 55, 65),
    "chain": (50, 55, 65), "red_wool": (160, 40, 40), "white_wool": (235, 235, 235), "black_wool": (25, 25, 30),
    "smooth_stone_slab": (160, 160, 160), "light": (0, 0, 0), "ochre_froglight": (250, 230, 170),
    "pearlescent_froglight": (245, 225, 230), "sea_lantern": (200, 225, 220), "end_rod": (250, 240, 230),
    "wildflowers": (230, 220, 120), "leaf_litter": (150, 100, 50), "bush": (80, 130, 50),
    "oxeye_daisy": (230, 230, 210), "azure_bluet": (220, 230, 230), "cornflower": (70, 100, 210),
    "dandelion": (240, 220, 50), "poppy": (200, 40, 30), "torchflower": (230, 140, 40),
    "iron_bars": (110, 110, 115), "anvil": (68, 68, 68), "furnace": (110, 110, 110), "blast_furnace": (90, 90, 95),
    "smoker": (90, 80, 70), "crafting_table": (140, 100, 60), "enchanting_table": (150, 40, 40),
    "cauldron": (60, 60, 60), "water_cauldron": (60, 60, 90), "beehive": (190, 150, 80), "loom": (150, 120, 90),
    "smithing_table": (60, 50, 60), "grindstone": (130, 130, 130), "stonecutter": (120, 120, 120),
    "lectern": (160, 120, 70), "cartography_table": (110, 80, 60), "fletching_table": (190, 170, 120),
    "brewing_stand": (120, 100, 80), "composter": (120, 80, 40), "decorated_pot": (150, 90, 70),
    "flower_pot": (120, 70, 50), "jukebox": (100, 70, 50), "bell": (220, 180, 60), "ender_chest": (30, 45, 45),
    "seagrass": (40, 110, 40), "tall_seagrass": (40, 110, 40), "kelp": (60, 120, 40), "kelp_plant": (60, 120, 40),
    "carrots": (60, 150, 40), "potatoes": (60, 150, 40), "beetroots": (60, 150, 40), "sweet_berry_bush": (40, 90, 50),
    "white_bed": (235, 235, 235), "pink_bed": (240, 150, 190), "red_bed": (160, 40, 40),
    "stone_brick_wall": (122, 121, 122), "mossy_stone_brick_wall": (112, 120, 100), "andesite_wall": (136, 136, 137),
    "cobblestone_wall": (125, 125, 125), "mossy_cobblestone_wall": (106, 118, 92),
    "deepslate_tile_wall": (52, 52, 56), "polished_deepslate_wall": (72, 72, 74), "tuff_wall": (108, 109, 102),
    "red_nether_bricks": (70, 7, 9), "nether_bricks": (44, 21, 26), "mangrove_planks": (117, 54, 48),
    "crimson_planks": (101, 48, 70), "red_glazed_terracotta": (180, 60, 50),
}


def base_color(state):
    n, p = parse(state)
    if n in C:
        return C[n]
    for suf in ("_stairs", "_slab", "_fence_gate", "_fence", "_trapdoor", "_door", "_wall", "_pane",
                "_button", "_pressure_plate", "_carpet", "_wall_banner", "_banner"):
        if n.endswith(suf):
            root = n[: -len(suf)]
            for cand in (root, root + "s", root + "_planks", root.replace("_brick", "_bricks"),
                         root.replace("_tile", "_tiles"), root + "_block"):
                if cand in C:
                    return C[cand]
            if root.endswith("brick"):
                return C.get(root + "s", (120, 120, 120))
    if n.endswith("candle"):
        return C["pink_candle"] if "pink" in n else C["candle"]
    for k in ("red", "white", "black", "pink", "gray", "blue", "green", "yellow", "orange"):
        if n.startswith(k):
            return {"red": (160, 40, 40), "white": (230, 230, 230), "black": (30, 30, 34), "pink": (230, 140, 180),
                    "gray": (70, 70, 75), "blue": (50, 70, 170), "green": (80, 110, 40), "yellow": (230, 200, 60),
                    "orange": (220, 120, 40)}[k]
    h = hashlib.md5(n.encode()).digest()
    return (80 + h[0] % 120, 80 + h[1] % 120, 80 + h[2] % 120)


CCW = {"north": "west", "west": "south", "south": "east", "east": "north"}
CW = {v: k for k, v in CCW.items()}
QUAD = {"north": [(0, 0), (1, 0)], "south": [(0, 1), (1, 1)], "west": [(0, 0), (0, 1)], "east": [(1, 0), (1, 1)]}


def corner(a, b):
    s = set(QUAD[a]) & set(QUAD[b])
    return s.pop()


def shape_mask(state):
    """2x2x2 occupancy [sx][sy][sz]."""
    n, p = parse(state)
    m = np.zeros((2, 2, 2), dtype=bool)
    if is_air(state):
        return m
    if n.endswith("_stairs"):
        f = p.get("facing", "north")
        lo, hi = (0, 1) if p.get("half", "bottom") == "bottom" else (1, 0)
        m[:, lo, :] = True
        shape = p.get("shape", "straight")
        quads = set()
        left, right = CCW[f], CW[f]
        back, front = f, {"north": "south", "south": "north", "east": "west", "west": "east"}[f]
        if shape == "straight":
            quads = set(QUAD[back])
        elif shape == "outer_left":
            quads = {corner(back, left)}
        elif shape == "outer_right":
            quads = {corner(back, right)}
        elif shape == "inner_left":
            quads = set(QUAD[back]) | {corner(front, left)}
        elif shape == "inner_right":
            quads = set(QUAD[back]) | {corner(front, right)}
        for (sx, sz) in quads:
            m[sx, hi, sz] = True
        return m
    if n.endswith("_slab"):
        t = p.get("type", "bottom")
        if t == "bottom":
            m[:, 0, :] = True
        elif t == "top":
            m[:, 1, :] = True
        else:
            m[:] = True
        return m
    if n.endswith("_trapdoor"):
        if p.get("open") == "true":
            f = p.get("facing", "north")
            opp = {"north": "south", "south": "north", "east": "west", "west": "east"}[f]
            for (sx, sz) in QUAD[opp]:
                m[sx, :, sz] = True
        else:
            m[:, 1 if p.get("half") == "top" else 0, :] = True
        return m
    if n.endswith("_carpet") or n in ("pink_petals", "moss_carpet", "leaf_litter", "wildflowers", "lily_pad"):
        m[:, 0, :] = True
        return m
    if n.endswith("_bed"):
        m[:, 0, :] = True
        return m
    if n.endswith("_door"):
        f = p.get("facing", "north")
        opp = {"north": "south", "south": "north", "east": "west", "west": "east"}[f]
        for (sx, sz) in QUAD[opp]:
            m[sx, :, sz] = True
        return m
    if (n.endswith("_fence") or n.endswith("_wall") or n.endswith("_pane") or n in ("iron_bars",)
            or n.endswith("_fence_gate")):
        m[0, :, 0] = True
        if p.get("east") in ("true", "low", "tall"):
            m[1, :, 0] = True
        if p.get("south") in ("true", "low", "tall"):
            m[0, :, 1] = True
        if n.endswith("_fence_gate"):
            if p.get("facing") in ("north", "south"):
                m[1, :, 0] = True
            else:
                m[0, :, 1] = True
        return m
    if n in ("iron_chain", "chain", "bamboo", "sugar_cane", "end_rod", "lightning_rod"):
        m[0, :, 0] = True
        return m
    if n in ("lantern", "soul_lantern") or n.endswith("candle") or n in ("flower_pot",) or n.startswith("potted_"):
        m[0, 0, 0] = True
        return m
    if n in ("short_grass", "fern", "tall_grass", "large_fern", "white_tulip", "pink_tulip", "lily_of_the_valley",
             "allium", "blue_orchid", "peony", "lilac", "rose_bush", "azure_bluet", "oxeye_daisy", "cornflower",
             "dandelion", "poppy", "torchflower", "seagrass", "tall_seagrass", "glow_lichen", "sea_pickle",
             "firefly_bush", "bush", "wheat", "carrots", "potatoes", "beetroots", "kelp", "kelp_plant",
             "sweet_berry_bush", "red_mushroom", "brown_mushroom"):
        m[0, 0, 0] = True
        m[1, 0, 1] = True
        return m
    m[:] = True
    return m


def build_sub(world, box=None, ycut=None):
    """Expand the world into a 2x sub-voxel id grid (0 = empty)."""
    g = world.g
    if box:
        (xa, xb, ya, yb, za, zb) = box
        g = g[xa - X0:xb - X0 + 1, ya - Y0:yb - Y0 + 1, za - Z0:zb - Z0 + 1]
        off = (xa, ya, za)
    else:
        off = (X0, Y0, Z0)
    if ycut is not None:
        g = g.copy()
        g[:, ycut - off[1] + 1:, :] = 0
    nx, ny, nz = g.shape
    sub = np.zeros((nx * 2, ny * 2, nz * 2), dtype=np.int32)
    ids = np.unique(g)
    for i in ids:
        if i == 0:
            continue
        st = world.palette[i]
        if is_air(st):
            continue
        m = shape_mask(st)
        where = g == i
        for sx in range(2):
            for sy in range(2):
                for sz in range(2):
                    if m[sx, sy, sz]:
                        sub[sx::2, sy::2, sz::2][where] = i
    return sub, off


def palette_colors(world):
    cols = np.zeros((len(world.palette), 3), dtype=np.float32)
    emis = np.zeros(len(world.palette), dtype=bool)
    for i, st in enumerate(world.palette):
        cols[i] = base_color(st)
        if light_emission(st) >= 10:
            emis[i] = True
    return cols, emis


def iso(world, path, view="SE", box=None, night=False, light=None, ycut=None, scale=1, title=None):
    sub, off = build_sub(world, box, ycut)
    if view in ("SW", "NW"):
        sub = sub[::-1, :, :]
    if view in ("NE", "NW"):
        sub = sub[:, :, ::-1]
    cols, emis = palette_colors(world)
    water_ids = np.array([is_water(s) for s in world.palette])
    leaf_ids = np.array([is_leaves(s) for s in world.palette])
    lgrid = None
    if night and light is not None:
        lg = light
        if box:
            (xa, xb, ya, yb, za, zb) = box
            lg = lg[xa - X0:xb - X0 + 1, ya - Y0:yb - Y0 + 1, za - Z0:zb - Z0 + 1]
        if view in ("SW", "NW"):
            lg = lg[::-1, :, :]
        if view in ("NE", "NW"):
            lg = lg[:, :, ::-1]
        lgrid = lg
    occ = sub != 0
    # water only occludes / shows its top surface
    nx, ny, nz = sub.shape
    faces = []
    empty_above = np.ones_like(occ)
    empty_above[:, :-1, :] = ~occ[:, 1:, :] | water_ids[sub[:, 1:, :]] & ~water_ids[sub[:, :-1, :]]
    empty_px = np.ones_like(occ)
    empty_px[:-1, :, :] = ~occ[1:, :, :] | (water_ids[sub[1:, :, :]] & ~water_ids[sub[:-1, :, :]])
    empty_pz = np.ones_like(occ)
    empty_pz[:, :, :-1] = ~occ[:, :, 1:] | (water_ids[sub[:, :, 1:]] & ~water_ids[sub[:, :, :-1]])
    for kind, vis, shade, pix, nb in (
        ("top", occ & empty_above, 1.0, [(0, -1), (0, 0), (1, -2), (1, -1), (1, 0), (1, 1)], (0, 1, 0)),
        ("px", occ & empty_px & ~water_ids[sub], 0.78, [(2, 0), (2, 1), (3, 0), (3, 1)], (1, 0, 0)),
        ("pz", occ & empty_pz & ~water_ids[sub], 0.62, [(2, -2), (2, -1), (3, -2), (3, -1)], (0, 0, 1)),
    ):
        xs, ys, zs = np.nonzero(vis)
        if len(xs) == 0:
            continue
        ids = sub[xs, ys, zs]
        col = cols[ids] * shade
        if night:
            if lgrid is not None:
                bx = np.clip((xs + nb[0]) // 2, 0, lgrid.shape[0] - 1)
                by = np.clip((ys + nb[1]) // 2, 0, lgrid.shape[1] - 1)
                bz = np.clip((zs + nb[2]) // 2, 0, lgrid.shape[2] - 1)
                L = np.maximum(lgrid[bx, by, bz], lgrid[xs // 2, ys // 2, zs // 2]).astype(np.float32)
            else:
                L = np.zeros(len(xs), dtype=np.float32)
            f = 0.10 + 0.95 * (L / 15.0) ** 1.6
            warm = np.stack([f * 1.05, f * 0.86, f * 0.62], axis=1)
            moon = np.array([0.11, 0.12, 0.2])
            lit = col * np.maximum(warm, moon)
            lit[emis[ids]] = cols[ids][emis[ids]] * 1.1
            col = lit
        if kind == "top":
            wat = water_ids[ids]
            col[wat] = col[wat] * 0.9 + np.array([10, 20, 40]) * (0.3 if night else 1)
            lf = leaf_ids[ids]
            jitter = ((xs * 7 + zs * 13 + ys * 3) % 5)[lf] * (6 if not night else 1)
            col[lf] = col[lf] - jitter[:, None]
        depth = xs + ys + zs
        u = 2 * (xs - zs)
        v = (xs + zs) - 2 * ys
        for (dv, du) in pix:
            faces.append((u + du, v + dv, depth, col))
    U = np.concatenate([f[0] for f in faces])
    V = np.concatenate([f[1] for f in faces])
    D = np.concatenate([f[2] for f in faces])
    COL = np.concatenate([f[3] for f in faces])
    U -= U.min()
    V -= V.min()
    order = np.argsort(D, kind="stable")
    W, H = U.max() + 1, V.max() + 1
    bg = np.array([14, 16, 30] if night else [196, 214, 232], dtype=np.float32)
    img = np.empty((H, W, 3), dtype=np.float32)
    img[:] = bg
    img[V[order], U[order]] = COL[order]
    img = np.clip(img, 0, 255).astype(np.uint8)
    im = Image.fromarray(img)
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(path)
    return im


def plan(world, path, px=4, box=None):
    """Top-down plan: colour of the highest block, hill-shaded."""
    g = world.g
    xa, xb, za, zb = (X0, X0 + g.shape[0] - 1, Z0, Z0 + g.shape[2] - 1) if box is None else box
    cols, emis = palette_colors(world)
    sub = g[xa - X0:xb - X0 + 1, :, za - Z0:zb - Z0 + 1]
    airish = np.array([is_air(s) for s in world.palette])
    nonair = ~airish[sub]
    ny = sub.shape[1]
    top = ny - 1 - np.argmax(nonair[:, ::-1, :], axis=1)
    has = nonair.any(axis=1)
    ids = np.take_along_axis(sub, top[:, None, :], axis=1)[:, 0, :]
    img = cols[ids]
    h = top.astype(np.float32)
    shade = np.ones_like(h)
    shade[1:, 1:] += (h[1:, 1:] - h[:-1, :-1]) * 0.08
    img = img * np.clip(shade, 0.6, 1.4)[..., None] * (0.75 + 0.25 * (h / ny))[..., None] * 1.1
    img[~has] = (20, 20, 20)
    img = np.clip(img, 0, 255).astype(np.uint8).transpose(1, 0, 2)
    im = Image.fromarray(img).resize((img.shape[1] * px, img.shape[0] * px), Image.NEAREST)
    # grid every 10 blocks
    a = np.array(im)
    for x in range(xa, xb + 1):
        if x % 10 == 0:
            a[:, (x - xa) * px, :] = a[:, (x - xa) * px, :] // 2
    for z in range(za, zb + 1):
        if z % 10 == 0:
            a[(z - za) * px, :, :] = a[(z - za) * px, :, :] // 2
    Image.fromarray(a).save(path)
