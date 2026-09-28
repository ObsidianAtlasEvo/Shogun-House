"""The shogun residence: Great Hall (two storeys, layered roofs, chidori gable,
karahafu entrance), the private West Wing, the scholarly East Wing, verandas,
the stone podium and every interior room."""
import math

from world import AIR, is_air, parse, with_props
from arch import (POST, BEAM_X, BEAM_Z, PLASTER, DARK, FLOOR, TATAMI, SHOJI, timber_wall, box_walls, engawa,
                  ceiling, tatami_floor, roof_group, stone_lantern, hanging_lantern, stairs, slab, arched_bridge)
from roofs import Roof, TILE

# ---------------------------------------------------------------- geometry constants
GH = dict(x0=-15, x1=15, z0=-21, z1=0, fy=3, top=9)
GH_UP = dict(x0=-9, x1=9, z0=-17, z1=-5, fy=11, top=17)
WW = dict(x0=-39, x1=-21, z0=-33, z1=-18, fy=3, top=8)
EW = dict(x0=21, x1=39, z0=-9, z1=9, fy=3, top=8)


def hang(w, x, z, y_lantern, kind="lantern", maxup=8):
    """Hang a lantern at y_lantern from whatever is above (roof soffit / beam) using chains."""
    y = y_lantern + 1
    while y < y_lantern + maxup and is_air(w.get(x, y, z)):
        y += 1
    if y >= y_lantern + maxup:
        return False
    for yy in range(y_lantern + 1, y):
        w.set(x, yy, z, "iron_chain[axis=y]")
    w.set(x, y_lantern, z, f"{kind}[hanging=true]")
    return True


def close_to_roof(w, pts, y_from, mat=DARK, limit=8):
    """Extend wall tops upward until they meet the roof shell."""
    for (x, z) in pts:
        y = y_from
        while y < y_from + limit and is_air(w.get(x, y, z)):
            w.set(x, y, z, mat)
            y += 1


def perimeter(x0, z0, x1, z1):
    pts = []
    for x in range(x0, x1 + 1):
        pts += [(x, z0), (x, z1)]
    for z in range(z0 + 1, z1):
        pts += [(x0, z), (x1, z)]
    return pts


def andon(w, x, y, z):
    """Floor lamp: dark post + lantern."""
    w.set(x, y, z, "dark_oak_fence")
    w.set(x, y + 1, z, "lantern")


def podium(w, rng):
    """Stone retaining edges of the manor podium (surface y=2), with stepped mossy courses."""
    from site_terrain import in_podium
    for x in range(-46, 47):
        for z in range(-40, 16):
            if not in_podium(x, z):
                continue
            edge = any(not in_podium(x + dx, z + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                for y in range(-1, 3):
                    r = rng.random()
                    m = "mossy_stone_bricks" if r < 0.22 else "stone_bricks"
                    w.set(x, y, z, m)
                # capstone
                w.set(x, 2, z, "polished_andesite")
                # low stone kerb just above the edge every other block where no veranda sits
            else:
                w.set(x, 2, z, "gravel")


def great_hall(w, rng):
    g = GH
    fy = g["fy"]
    # floor slab + engawa
    w.fill(g["x0"] - 2, fy, g["z0"] - 2, g["x1"] + 2, fy, g["z1"] + 2, FLOOR)
    engawa(w, g["x0"] - 2, g["z0"] - 2, g["x1"] + 2, g["z1"] + 2, fy, post_top=g["top"], posts_every=3,
           post_grid_origin=(g["x0"], g["z0"]))
    # interior tatami
    tatami_floor(w, g["x0"] + 1, g["z0"] + 1, g["x1"] - 1, g["z1"] - 1, fy)
    # ground-floor walls: south = shoji with a wide entrance; north = opens to the moon garden
    y0, y1 = fy + 1, g["top"]
    timber_wall(w, g["x0"], g["z1"], g["x1"], g["z1"], y0, y1, 3, "shoji", openings=range(13, 18))
    timber_wall(w, g["x0"], g["z0"], g["x1"], g["z0"], y0, y1, 3, "shoji",
                openings=list(range(4, 12)) + list(range(19, 27)))
    timber_wall(w, g["x0"], g["z0"], g["x0"], g["z1"], y0, y1, 3, "mixed", openings=(10, 11))
    timber_wall(w, g["x1"], g["z0"], g["x1"], g["z1"], y0, y1, 3, "mixed", openings=(10, 11))
    # engawa eave beams on post tops
    ex0, ex1, ez0, ez1 = g["x0"] - 2, g["x1"] + 2, g["z0"] - 2, g["z1"] + 2
    for x in range(ex0, ex1 + 1):
        for z in (ez0, ez1):
            if is_air(w.get(x, g["top"], z)):
                w.set(x, g["top"], z, BEAM_X)
    for z in range(ez0, ez1 + 1):
        for x in (ex0, ex1):
            if is_air(w.get(x, g["top"], z)):
                w.set(x, g["top"], z, BEAM_Z)
    # brackets (tokyo) under the eave beam on each post
    for x in range(ex0, ex1 + 1):
        for z in range(ez0, ez1 + 1):
            if w.get(x, g["top"] - 1, z) == POST and (x in (ex0, ex1) or z in (ez0, ez1)):
                for f, dx, dz in (("south", 0, -1), ("north", 0, 1), ("east", -1, 0), ("west", 1, 0)):
                    nx, nz = x + dx, z + dz
                    outside = not (ex0 <= nx <= ex1 and ez0 <= nz <= ez1)
                    if outside:
                        w.set(nx, g["top"] - 1, nz, stairs("dark_oak", f, "top"))
    # ceiling
    ceiling(w, g["x0"] + 1, g["z0"] + 1, g["x1"] - 1, g["z1"] - 1, g["top"] + 1)
    # --- upper storey
    u = GH_UP
    w.fill(u["x0"], u["fy"], u["z0"], u["x1"], u["fy"], u["z1"], FLOOR)
    tatami_floor(w, u["x0"] + 1, u["z0"] + 1, u["x1"] - 1, u["z1"] - 1, u["fy"])
    uy0, uy1 = u["fy"] + 1, u["top"]
    timber_wall(w, u["x0"], u["z1"], u["x1"], u["z1"], uy0, uy1, 3, "shoji")
    timber_wall(w, u["x0"], u["z0"], u["x1"], u["z0"], uy0, uy1, 3, "shoji", openings=range(4, 15))
    timber_wall(w, u["x0"], u["z0"], u["x0"], u["z1"], uy0, uy1, 3, "plaster")
    timber_wall(w, u["x1"], u["z0"], u["x1"], u["z1"], uy0, uy1, 3, "plaster")
    ceiling(w, u["x0"] + 1, u["z0"] + 1, u["x1"] - 1, u["z1"] - 1, u["top"] + 1, grid=3)
    # moon-viewing balcony railing in the northern opening
    for x in range(u["x0"] + 4, u["x0"] + 15):
        w.set(x, uy0, u["z0"], "dark_oak_fence")


def porch(w, rng):
    """Genkan with karahafu roof, stepping down to the forecourt."""
    fy = GH["fy"]
    w.fill(-5, fy, 1, 5, fy, 10, FLOOR)
    for (x, z) in ((-5, 10), (5, 10), (-5, 4), (5, 4)):
        w.fill(x, fy + 1, z, x, 9, z, POST)
    for x in range(-5, 6):
        w.set(x, 9, 10, BEAM_X)
        w.set(x, 8, 10, stairs("dark_oak", "south", "top") if abs(x) < 5 else POST)
    for z in range(1, 11):
        w.set(-5, 9, z, BEAM_Z)
        w.set(5, 9, z, BEAM_Z)
    # kaerumata / decorative frog-leg strut at the gable centre
    w.set(0, 8, 10, "chiseled_quartz_block")
    w.set(-1, 8, 10, stairs("dark_oak", "west", "top"))
    w.set(1, 8, 10, stairs("dark_oak", "east", "top"))
    # steps down to the court (surface y=0)
    for x in range(-4, 5):
        w.set(x, 2, 11, stairs("polished_andesite", "north"))
        w.set(x, 1, 12, stairs("polished_andesite", "north"))
        w.set(x, 0, 13, stairs("polished_andesite", "north"))
        w.fill(x, -1, 11, x, 1, 11, "stone_bricks")
        w.fill(x, -1, 12, x, 0, 12, "stone_bricks")
    # shikidai + genkan lanterns
    hang(w, -3, 9, 7)
    hang(w, 3, 9, 7)


def west_wing(w, rng):
    g = WW
    fy = g["fy"]
    engawa(w, g["x0"] - 2, g["z0"] - 2, g["x1"] + 2, g["z1"] + 2, fy, post_top=g["top"], posts_every=3,
           post_grid_origin=(g["x0"], g["z0"]))
    tatami_floor(w, g["x0"] + 1, g["z0"] + 1, g["x1"] - 1, g["z1"] - 1, fy)
    y0, y1 = fy + 1, g["top"]
    timber_wall(w, g["x0"], g["z0"], g["x1"], g["z0"], y0, y1, 3, "shoji", openings=(7, 8, 10, 11), nageshi=fy + 3)
    timber_wall(w, g["x0"], g["z1"], g["x1"], g["z1"], y0, y1, 3, "shoji", openings=(4, 5, 13, 14), nageshi=fy + 3)
    timber_wall(w, g["x0"], g["z0"], g["x0"], g["z1"], y0, y1, 3, "mixed", openings=(7, 8), nageshi=fy + 3)
    timber_wall(w, g["x1"], g["z0"], g["x1"], g["z1"], y0, y1, 3, "shoji", openings=(7, 8, 10, 11), nageshi=fy + 3)
    ex0, ex1, ez0, ez1 = g["x0"] - 2, g["x1"] + 2, g["z0"] - 2, g["z1"] + 2
    for x in range(ex0, ex1 + 1):
        for z in (ez0, ez1):
            if is_air(w.get(x, y1, z)):
                w.set(x, y1, z, BEAM_X)
    for z in range(ez0, ez1 + 1):
        for x in (ex0, ex1):
            if is_air(w.get(x, y1, z)):
                w.set(x, y1, z, BEAM_Z)
    ceiling(w, g["x0"] + 1, g["z0"] + 1, g["x1"] - 1, g["z1"] - 1, y1 + 1)
    # link the wing's veranda to the Great Hall veranda
    w.fill(-19, fy, -23, -17, fy, -16, FLOOR)


def east_wing(w, rng):
    g = EW
    fy = g["fy"]
    engawa(w, g["x0"] - 2, g["z0"] - 2, g["x1"] + 2, g["z1"] + 2, fy, post_top=g["top"], posts_every=3,
           post_grid_origin=(g["x0"], g["z0"]))
    tatami_floor(w, g["x0"] + 1, g["z0"] + 1, g["x1"] - 1, g["z1"] - 1, fy)
    y0, y1 = fy + 1, g["top"]
    timber_wall(w, g["x0"], g["z1"], g["x1"], g["z1"], y0, y1, 3, "shoji", openings=(4, 5, 13, 14), nageshi=fy + 3)
    timber_wall(w, g["x0"], g["z0"], g["x1"], g["z0"], y0, y1, 3, "shoji", openings=(10, 11), nageshi=fy + 3)
    timber_wall(w, g["x0"], g["z0"], g["x0"], g["z1"], y0, y1, 3, "shoji", openings=(7, 8, 10, 11), nageshi=fy + 3)
    timber_wall(w, g["x1"], g["z0"], g["x1"], g["z1"], y0, y1, 3, "mixed", openings=(4, 5), nageshi=fy + 3)
    ex0, ex1, ez0, ez1 = g["x0"] - 2, g["x1"] + 2, g["z0"] - 2, g["z1"] + 2
    for x in range(ex0, ex1 + 1):
        for z in (ez0, ez1):
            if is_air(w.get(x, y1, z)):
                w.set(x, y1, z, BEAM_X)
    for z in range(ez0, ez1 + 1):
        for x in (ex0, ex1):
            if is_air(w.get(x, y1, z)):
                w.set(x, y1, z, BEAM_Z)
    ceiling(w, g["x0"] + 1, g["z0"] + 1, g["x1"] - 1, g["z1"] - 1, y1 + 1)
    w.fill(17, fy, -11, 19, fy, 2, FLOOR)


def manor_roofs(w):
    """Lower group: GH skirt roof + wings + porch karahafu (merged). Upper: GH irimoya + chidori gable."""
    gh_low = Roof((-21, 21, -27, 6), 10, kind="hip", axis="x", s0=0.42, s1=0.62, lift=1.4, lift_len=7,
                  hole=(GH_UP["x0"], GH_UP["x1"], GH_UP["z0"], GH_UP["z1"]), walls=(-15, 15, -21, 0))
    ww = Roof((-44, -16, -38, -13), 9, kind="irimoya", axis="z", s0=0.45, s1=1.05, lift=1.3, lift_len=6,
              walls=(WW["x0"], WW["x1"], WW["z0"], WW["z1"]))
    ew = Roof((16, 44, -14, 14), 9, kind="irimoya", axis="z", s0=0.45, s1=1.05, lift=1.3, lift_len=6,
              walls=(EW["x0"], EW["x1"], EW["z0"], EW["z1"]))
    kara = Roof((-6, 6, 1, 11), 9, kind="kara", axis="z", s0=0.5, s1=1.0, lift=0.9, lift_len=3, height_scale=1.0,
                walls=(-5, 5, 1, 10))
    roof_group(w, [gh_low, ww, ew, kara], gable_crest="gold_block")
    up = Roof((-13, 13, -21, -1), 18, kind="irimoya", axis="x", s0=0.5, s1=1.2, lift=1.5, lift_len=6,
              walls=(GH_UP["x0"], GH_UP["x1"], GH_UP["z0"], GH_UP["z1"]))
    chidori = Roof((-5, 5, -9, 0), 18, kind="gable", axis="z", s0=0.55, s1=1.15, lift=0.8, lift_len=3,
                   walls=(-5, 5, -9, 0))
    roof_group(w, [up, chidori], gable_crest="gold_block")
    # close wall tops up to the roof undersides
    close_to_roof(w, perimeter(GH["x0"], GH["z0"], GH["x1"], GH["z1"]), GH["top"] + 1)
    close_to_roof(w, perimeter(GH_UP["x0"], GH_UP["z0"], GH_UP["x1"], GH_UP["z1"]), GH_UP["top"] + 1)
    close_to_roof(w, perimeter(WW["x0"], WW["z0"], WW["x1"], WW["z1"]), WW["top"] + 1)
    close_to_roof(w, perimeter(EW["x0"], EW["z0"], EW["x1"], EW["z1"]), EW["top"] + 1)
    return gh_low, up


def veranda_lanterns(w):
    """Hanging lanterns from the eaves at alternate veranda posts + soft light along the decks."""
    specs = [(GH, 2), (WW, 2), (EW, 2)]
    for g, off in specs:
        ex0, ex1, ez0, ez1 = g["x0"] - off, g["x1"] + off, g["z0"] - off, g["z1"] + off
        ly = g["fy"] + 4
        pts = []
        for x in range(ex0, ex1 + 1, 6):
            pts += [(x, ez0 - 1), (x, ez1 + 1)]
        for z in range(ez0, ez1 + 1, 6):
            pts += [(ex0 - 1, z), (ex1 + 1, z)]
        pts += [(ex0 - 1, ez0 - 1), (ex1 + 1, ez0 - 1), (ex0 - 1, ez1 + 1), (ex1 + 1, ez1 + 1)]
        for (x, z) in pts:
            hang(w, x, z, ly, maxup=6)
    # upper storey corners
    u = GH_UP
    for (x, z) in ((u["x0"] - 2, u["z0"] - 2), (u["x1"] + 2, u["z0"] - 2), (u["x0"] - 2, u["z1"] + 2),
                   (u["x1"] + 2, u["z1"] + 2), (0, u["z0"] - 3)):
        hang(w, x, z, u["top"], maxup=6)


# ---------------------------------------------------------------- interiors
def interiors(w, rng):
    fy = GH["fy"]
    Y = fy + 1
    # ===== Great Hall: audience chamber with raised jodan-no-ma and tokonoma
    w.fill(-7, fy + 1, -20, 7, fy + 1, -17, TATAMI)             # dais one step up
    for x in range(-7, 8):
        w.set(x, fy + 1, -16, stairs("dark_oak", "north"))
    # tokonoma alcove in the north wall behind the dais
    w.set(0, fy + 2, -20, "dark_oak_planks")
    w.set(0, fy + 3, -20, "potted_flowering_azalea_bush")  # ikebana
    for x in (-2, 2):
        w.fill(x, fy + 2, -20, x, fy + 5, -20, POST)
    w.set(-1, fy + 2, -20, "decorated_pot")
    w.set(1, fy + 2, -20, "potted_cherry_sapling")
    # lord's seat: cushions (red carpet) and armrest
    for x in (-1, 0, 1):
        w.set(x, fy + 2, -18, "red_carpet")
    # retainers' cushions in rows
    for x in (-10, -7, 7, 10):
        for z in (-14, -11, -8, -5):
            w.set(x, Y, z, "light_gray_carpet")
    # interior columns
    for x in (-9, 9):
        for z in (-15, -9, -3):
            w.fill(x, Y, z, x, GH["top"], z, POST)
    # andon floor lamps
    for (x, z) in ((-12, -18), (12, -18), (-12, -3), (12, -3), (-5, -18), (5, -18)):
        andon(w, x, Y, z)
    # banners of the house flanking the dais
    for x in (-6, 6):
        w.set(x, fy + 5, -21, "dark_oak_planks")
        w.set(x, fy + 5, -20, "red_wall_banner[facing=south]")
    # staircase to the upper storey (east side, rising westward)
    for i in range(7):
        x = 8 - i
        y = Y + i
        for z in (-7, -6):
            w.set(x, y, z, stairs("dark_oak", "west"))
            for yy in range(y + 1, y + 4):
                if yy >= GH["top"] + 1 and yy <= GH_UP["fy"]:
                    w.set(x, yy, z, AIR)
                elif yy < GH["top"] + 1:
                    w.set(x, yy, z, AIR)
    # upper floor: lord's private viewing room
    u = GH_UP
    uy = u["fy"] + 1
    for (x, z) in ((-7, -15), (7, -15), (-7, -7)):
        andon(w, x, uy, z)
    w.set(0, uy, -9, "dark_oak_slab[type=bottom]")
    w.set(-1, uy, -9, "dark_oak_slab[type=bottom]")
    w.set(1, uy, -9, "dark_oak_slab[type=bottom]")
    w.set(0, uy, -10, "red_carpet")
    w.set(-4, uy, -15, "ender_chest[facing=south]")
    w.set(4, uy, -15, "lectern[facing=north]")
    w.set(-3, uy, -15, "chest[facing=south,type=single]")

    # ===== West Wing: private residence
    g = WW
    Y = g["fy"] + 1
    # partitions (fusuma) : x = -30 and z = -25
    for z in range(g["z0"] + 1, g["z1"]):
        if z not in (-29, -28, -22, -21):
            w.fill(-30, Y, z, -30, g["top"], z, "birch_planks" if z % 3 else POST)
    for x in range(g["x0"] + 1, g["x1"]):
        if x not in (-35, -34, -26, -25):
            w.fill(x, Y, -25, x, g["top"], -25, "birch_planks" if x % 3 else POST)
    # lord's bedroom (NW): futon beds
    w.pair([(-37, Y, -30, "white_bed[facing=north,part=foot]"), (-37, Y, -31, "white_bed[facing=north,part=head]")])
    w.pair([(-35, Y, -30, "pink_bed[facing=north,part=foot]"), (-35, Y, -31, "pink_bed[facing=north,part=head]")])
    andon(w, -38, Y, -27)
    w.set(-32, Y, -32, "chest[facing=south,type=single]")
    w.set(-31, Y, -32, "decorated_pot")
    # second bedroom (SW)
    w.pair([(-37, Y, -21, "white_bed[facing=north,part=foot]"), (-37, Y, -22, "white_bed[facing=north,part=head]")])
    w.pair([(-35, Y, -21, "light_gray_bed[facing=north,part=foot]"),
            (-35, Y, -22, "light_gray_bed[facing=north,part=head]")])
    andon(w, -32, Y, -19)
    # study (NE) with the hidden stair
    for x in range(-29, -25):
        w.set(x, Y, -32, "bookshelf")
        w.set(x, Y + 1, -32, "chiseled_bookshelf[facing=south]")
    w.set(-26, Y, -28, "lectern[facing=west]")
    w.set(-27, Y, -28, "dark_oak_slab[type=bottom]")
    w.set(-28, Y, -28, "dark_oak_slab[type=bottom]")
    andon(w, -29, Y, -26)
    w.set(-27, Y + 1, -28, "potted_white_tulip")
    # dressing / tea room (SE)
    w.set(-26, Y, -21, "loom[facing=south]")
    w.set(-28, Y, -21, "barrel[facing=up]")
    andon(w, -23, Y, -19)

    # ===== East Wing: library, strategy room, herbalist, guest room
    g = EW
    Y = g["fy"] + 1
    for z in range(g["z0"] + 1, g["z1"]):
        if z not in (-5, -4, 4, 5):
            w.fill(31, Y, z, 31, g["top"], z, "birch_planks" if z % 3 else POST)
    for x in range(g["x0"] + 1, g["x1"]):
        if x not in (25, 26, 35, 36):
            w.fill(x, Y, 1, x, g["top"], 1, "birch_planks" if x % 3 else POST)
    # scholar's library: enchanting table ringed by exactly 15 bookshelves
    cx, cz = 26, -4
    w.set(cx, Y, cz, "enchanting_table")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2 and not (dx == 0 and dz == 2):
                w.set(cx + dx, Y, cz + dz, "bookshelf")
            elif max(abs(dx), abs(dz)) == 1:
                w.set(cx + dx, Y, cz + dz, AIR)
    for z in range(-8, 0):
        w.set(22, Y + 1, z, "bookshelf")
    w.set(29, Y, -8, "lectern[facing=south]")
    andon(w, 29, Y, -1)
    andon(w, 22, Y, -1)
    # strategy room: cartography table, war table, map wall (item frames added as entities)
    w.set(35, Y, -8, "cartography_table")
    for x in range(33, 38):
        w.set(x, Y, -4, "dark_oak_fence")
        w.set(x, Y + 1, -4, "dark_oak_pressure_plate")
    andon(w, 38, Y, -1)
    andon(w, 32, Y, -8)
    # herbalist: brewing
    w.set(34, Y, 8, "brewing_stand")
    w.set(35, Y, 8, "cauldron")
    w.set(36, Y, 8, "brewing_stand")
    w.set(38, Y, 7, "barrel[facing=up]")
    w.set(38, Y, 6, "barrel[facing=up]")
    for (x, z, p) in ((33, 2, "potted_allium"), (38, 2, "potted_blue_orchid"), (38, 4, "potted_fern")):
        w.set(x, Y, z, p)
    andon(w, 32, Y, 6)
    # guest room
    w.set(25, Y, 5, "dark_oak_slab[type=bottom]")
    w.set(26, Y, 5, "dark_oak_slab[type=bottom]")
    w.set(26, Y + 1, 5, "potted_azure_bluet")
    for (x, z) in ((25, 3), (26, 7)):
        w.set(x, Y, z, "pink_carpet")
    andon(w, 22, Y, 8)


def moon_bridge(w):
    """Curved drum bridge from the Great Hall terrace to the ancient cherry island."""
    prof = arched_bridge(w, "z", -38, -28, -6, 3, 3, 3.2, deck="dark_oak", rail="dark_oak_fence",
                         post="red_concrete", water_y=-1, lanterns=False)
    # stone landings
    w.fill(-8, 2, -39, -4, 2, -39, "polished_andesite")
    return prof


def tsukimidai(w):
    """Bamboo moon-viewing platform projecting from the West Wing over the pond."""
    y = 3
    w.fill(-34, y, -42, -26, y, -36, "bamboo_mosaic")
    for x in range(-34, -25):
        for z in (-42,):
            w.set(x, y + 1, z, "bamboo_fence")
    for z in range(-42, -35):
        w.set(-34, y + 1, z, "bamboo_fence")
        w.set(-26, y + 1, z, "bamboo_fence")
    for (x, z) in ((-34, -42), (-26, -42), (-34, -39), (-26, -39)):
        w.fill(x, -4, z, x, y - 1, z, "stripped_bamboo_block[axis=y]")
    # low moon lanterns at the corners
    w.set(-34, y + 2, -42, "lantern")
    w.set(-26, y + 2, -42, "lantern")
