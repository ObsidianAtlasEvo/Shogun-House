"""Voxel world model for the Sakura Shogun Estate generator.

All coordinates are RELATIVE to the estate centre (dx, dy, dz):
  +x = east, -x = west, +z = south, -z = north, dy = 0 is standing height
  on the surrounding plains (the plains grass block sits at dy = -1).
Blocks are stored as block-state strings without the "minecraft:" prefix,
interned in a palette so the grid itself is a compact numpy array.
"""
import math
import random

import numpy as np

X0, X1 = -74, 74
Y0, Y1 = -28, 46
Z0, Z1 = -74, 112

AIR = "air"


def parse(state):
    """'oak_stairs[facing=north,half=top]' -> ('oak_stairs', {'facing': 'north', ...})"""
    if "[" not in state:
        return state, {}
    name, rest = state.split("[", 1)
    props = {}
    for kv in rest.rstrip("]").split(","):
        if kv:
            k, v = kv.split("=")
            props[k] = v
    return name, props


def fmt(name, props):
    if not props:
        return name
    return name + "[" + ",".join(f"{k}={v}" for k, v in props.items()) + "]"


def with_props(state, **kw):
    name, props = parse(state)
    props = dict(props)
    for k, v in kw.items():
        props[k] = str(v).lower() if isinstance(v, bool) else str(v)
    return fmt(name, props)


class World:
    def __init__(self, seed=1868):
        self.nx, self.ny, self.nz = X1 - X0 + 1, Y1 - Y0 + 1, Z1 - Z0 + 1
        self.palette = [AIR]
        self.index = {AIR: 0}
        self.g = np.zeros((self.nx, self.ny, self.nz), dtype=np.int32)
        self.rng = random.Random(seed)
        self.entities = []  # raw relative summon commands (text after 'summon')
        self.pairs = []      # two-part blocks placed as ordered setblocks: list of [(x,y,z,state),...]
        self.protect = np.zeros((self.nx, self.ny, self.nz), dtype=bool)

    # ---------------------------------------------------------------- palette
    def pid(self, state):
        state = state.replace("minecraft:", "")
        i = self.index.get(state)
        if i is None:
            i = len(self.palette)
            self.palette.append(state)
            self.index[state] = i
        return i

    def inb(self, x, y, z):
        return X0 <= x <= X1 and Y0 <= y <= Y1 and Z0 <= z <= Z1

    # ---------------------------------------------------------------- access
    def get(self, x, y, z):
        if not self.inb(x, y, z):
            return AIR
        return self.palette[self.g[x - X0, y - Y0, z - Z0]]

    def set(self, x, y, z, state, force=False):
        if not self.inb(x, y, z):
            return
        if self.protect[x - X0, y - Y0, z - Z0] and not force:
            return
        self.g[x - X0, y - Y0, z - Z0] = self.pid(state)

    def set_if_air(self, x, y, z, state):
        if self.inb(x, y, z) and self.g[x - X0, y - Y0, z - Z0] == 0:
            self.set(x, y, z, state)

    def fill(self, x0, y0, z0, x1, y1, z1, state, only_air=False, replace=None):
        xa, xb = sorted((x0, x1))
        ya, yb = sorted((y0, y1))
        za, zb = sorted((z0, z1))
        xa, xb = max(xa, X0), min(xb, X1)
        ya, yb = max(ya, Y0), min(yb, Y1)
        za, zb = max(za, Z0), min(zb, Z1)
        if xa > xb or ya > yb or za > zb:
            return
        sl = (slice(xa - X0, xb - X0 + 1), slice(ya - Y0, yb - Y0 + 1), slice(za - Z0, zb - Z0 + 1))
        p = self.pid(state)
        mask = ~self.protect[sl]
        if only_air:
            mask &= self.g[sl] == 0
        if replace is not None:
            ids = [self.index[r] for r in ([replace] if isinstance(replace, str) else replace) if r in self.index]
            mask &= np.isin(self.g[sl], ids)
        self.g[sl][mask] = p

    def hollow(self, x0, y0, z0, x1, y1, z1, state):
        self.fill(x0, y0, z0, x1, y1, z1, state)
        self.fill(x0 + 1, y0 + 1, z0 + 1, x1 - 1, y1 - 1, z1 - 1, AIR)

    def column_top(self, x, z, ignore=("air",)):
        """Highest non-air (and non-plant) y in a column, or None."""
        col = self.g[x - X0, :, z - Z0]
        for yi in range(self.ny - 1, -1, -1):
            if col[yi] != 0:
                name = parse(self.palette[col[yi]])[0]
                if name in ignore or name == "light":
                    continue
                return yi + Y0
        return None

    def surface(self, x, z, ymax=Y1):
        """Top y of the first 'ground-like' block scanning down from ymax."""
        col = self.g[x - X0, :, z - Z0]
        for y in range(ymax, Y0 - 1, -1):
            s = self.palette[col[y - Y0]]
            if s != AIR and is_solid(s):
                return y
        return None

    def entity(self, text):
        self.entities.append(text)

    def pair(self, parts):
        """Two-part blocks (doors, beds, tall plants). parts = [(x,y,z,state), ...] in placement order."""
        for (x, y, z, s) in parts:
            self.set(x, y, z, s)
        self.pairs.append(parts)


# ---------------------------------------------------------------- block classes
PLANT_NAMES = {
    "short_grass", "tall_grass", "fern", "large_fern", "pink_petals", "wildflowers", "leaf_litter",
    "dandelion", "poppy", "blue_orchid", "allium", "azure_bluet", "red_tulip", "orange_tulip",
    "white_tulip", "pink_tulip", "oxeye_daisy", "cornflower", "lily_of_the_valley", "torchflower",
    "peony", "lilac", "rose_bush", "sunflower", "pitcher_plant", "sugar_cane", "bamboo", "lily_pad",
    "sea_pickle", "seagrass", "tall_seagrass", "kelp", "kelp_plant", "glow_lichen", "vine",
    "moss_carpet", "firefly_bush", "bush", "azalea", "flowering_azalea", "sweet_berry_bush",
    "wheat", "carrots", "potatoes", "beetroots", "cherry_sapling", "dead_bush", "spore_blossom",
    "short_dry_grass", "tall_dry_grass", "hanging_roots", "small_dripleaf", "big_dripleaf",
    "big_dripleaf_stem", "melon_stem", "pumpkin_stem", "brown_mushroom", "red_mushroom",
}
THIN_SUFFIX = ("_fence", "_fence_gate", "_wall", "_pane", "_bars", "_chain", "_rod", "_button",
               "_pressure_plate", "_sign", "_banner", "_carpet", "_candle", "_torch", "_head", "_skull")
THIN_NAMES = {"iron_chain", "chain", "lantern", "soul_lantern", "iron_bars", "candle", "torch",
              "end_rod", "lightning_rod", "flower_pot", "ladder", "lever", "tripwire_hook", "scaffolding",
              "campfire", "soul_campfire", "brewing_stand", "bell", "decorated_pot", "cake"}


def base_name(state):
    return parse(state)[0]


def is_air(state):
    n = base_name(state)
    return n in ("air", "cave_air", "light")


def is_water(state):
    return base_name(state) == "water"


def is_plant(state):
    n = base_name(state)
    return n in PLANT_NAMES or n.endswith("_sapling") or n.endswith("_tulip")


def is_thin(state):
    n = base_name(state)
    if n in THIN_NAMES:
        return True
    return any(n.endswith(s) for s in THIN_SUFFIX) or n.endswith("candle")


def is_partial(state):
    n = base_name(state)
    return (n.endswith("_stairs") or n.endswith("_slab") or n.endswith("_trapdoor") or n.endswith("_door")
            or n.endswith("_bed") or is_thin(state) or is_plant(state))


def is_solid(state):
    """Full-ish opaque or structural block (not air, water, plant, thin)."""
    if is_air(state) or is_water(state) or is_plant(state) or is_thin(state):
        return False
    n = base_name(state)
    if n.endswith("_trapdoor") or n.endswith("_door") or n.endswith("_bed"):
        return False
    return True


def is_full_cube(state):
    n, p = parse(state)
    if not is_solid(state):
        return False
    if n.endswith("_stairs"):
        return False
    if n.endswith("_slab"):
        return p.get("type") == "double"
    if n in ("farmland", "dirt_path", "enchanting_table", "stonecutter", "chest", "ender_chest",
             "trapped_chest", "anvil", "grindstone", "lectern", "cauldron", "water_cauldron", "composter",
             "hopper", "bell", "daylight_detector", "snow", "cactus"):
        return False
    return True


def is_leaves(state):
    return base_name(state).endswith("_leaves")


def is_glassy(state):
    n = base_name(state)
    return "glass" in n or n.endswith("_leaves") or n == "ice"


LIGHT_EMIT = {
    "lantern": 15, "soul_lantern": 10, "shroomlight": 15, "glowstone": 15, "sea_lantern": 15,
    "ochre_froglight": 15, "pearlescent_froglight": 15, "verdant_froglight": 15, "end_rod": 14,
    "torch": 14, "wall_torch": 14, "jack_o_lantern": 15, "glow_lichen": 7, "firefly_bush": 2,
    "crying_obsidian": 10, "nether_portal": 11, "enchanting_table": 7, "ender_chest": 7,
    "brewing_stand": 1, "magma_block": 3, "lava": 15, "beacon": 15, "conduit": 15,
}


def light_emission(state):
    n, p = parse(state)
    if n == "light":
        return int(p.get("level", 15))
    if n in ("campfire",):
        return 15 if p.get("lit", "true") == "true" else 0
    if n == "soul_campfire":
        return 10 if p.get("lit", "true") == "true" else 0
    if n.endswith("candle"):
        return 3 * int(p.get("candles", 1)) if p.get("lit") == "true" else 0
    if n == "sea_pickle":
        return (3 + 3 * int(p.get("pickles", 1))) if p.get("waterlogged", "true") == "true" else 0
    if n == "redstone_lamp":
        return 15 if p.get("lit") == "true" else 0
    return LIGHT_EMIT.get(n, 0)


def blocks_light(state):
    """Conservative light occlusion used both for spawn-proofing and night renders."""
    if is_air(state) or is_water(state) or is_plant(state) or is_thin(state) or is_glassy(state):
        return False
    n, p = parse(state)
    if n.endswith("_trapdoor") or n.endswith("_door") or n.endswith("_bed") or n.endswith("_carpet"):
        return False
    if light_emission(state) > 0:
        return False
    return True


def spawn_floor(state):
    """Can a hostile mob stand on top of this block?"""
    n, p = parse(state)
    if not is_solid(state) or is_leaves(state) or is_glassy(state):
        return False
    if n.endswith("_slab"):
        return p.get("type") in ("top", "double")
    if n.endswith("_stairs"):
        return p.get("half") == "top"
    if n in ("farmland", "dirt_path", "enchanting_table", "chest", "ender_chest", "anvil", "grindstone",
             "lectern", "cauldron", "water_cauldron", "composter", "bedrock", "barrier", "campfire",
             "soul_campfire", "magma_block", "stonecutter", "beehive", "bee_nest", "decorated_pot",
             "brewing_stand", "bell", "cake"):
        return False
    if n.endswith("_wall") or n.endswith("_fence") or n.endswith("_fence_gate"):
        return False
    return True


def spawn_space(state):
    """Can a mob occupy this cell?"""
    if is_air(state):
        return True
    n = base_name(state)
    if n in ("short_grass", "fern", "pink_petals", "wildflowers", "leaf_litter", "dandelion", "poppy",
             "allium", "azure_bluet", "oxeye_daisy", "cornflower", "lily_of_the_valley", "white_tulip",
             "pink_tulip", "red_tulip", "orange_tulip", "blue_orchid", "short_dry_grass", "glow_lichen",
             "vine", "tall_grass", "large_fern", "dead_bush"):
        return True
    return False


def rot_facing(f, turns):
    order = ["north", "east", "south", "west"]
    return order[(order.index(f) + turns) % 4]


OPP = {"north": "south", "south": "north", "east": "west", "west": "east", "up": "down", "down": "up"}
DIRV = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0),
        "up": (0, 1, 0), "down": (0, -1, 0)}


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def dist2(ax, az, bx, bz):
    return math.hypot(ax - bx, az - bz)


def rock(x, y, z, mats=("stone", "mossy_cobblestone", "andesite")):
    """Spatially coherent rock material (patches, not per-block noise) so fills merge."""
    v = math.sin(x * 0.45 + y * 0.3) + math.sin(z * 0.38 - y * 0.2) + 0.6 * math.sin((x + z) * 0.21)
    k = int((v + 2.6) / 5.2 * len(mats))
    return mats[max(0, min(len(mats) - 1, k))]
