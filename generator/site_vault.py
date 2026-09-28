"""The hidden ancestral vault beneath the private study, and the shrine cavern
below it that conceals the Nether portal behind a red torii."""
import math

from world import AIR, is_air, rock
from arch import POST, stairs, torii, stone_lantern
from site_manor import hang

SARMOR = []  # (x, y, z, facing_yaw) positions for family armour stands


def vault(w, rng):
    # ---- hidden stair: three trapdoors in the study floor, descending south
    for x in (-24, -23):
        for z in (-31, -30, -29):
            w.set(x, 3, z, "spruce_trapdoor[facing=north,half=top,open=false]")
    for i in range(12):
        z = -31 + i
        y = 2 - i
        for x in (-24, -23):
            w.set(x, y, z, stairs("stone_brick", "north"))
            for yy in range(y + 1, y + 4):
                if yy != 3 or z > -29:
                    if yy <= 2:
                        w.set(x, yy, z, AIR)
            w.set(x, y - 1, z, "stone_bricks")
        for x in (-25, -22):
            for yy in range(y, y + 4):
                if yy <= 2:
                    w.set(x, yy, z, "stone_bricks" if (i + yy) % 5 else "chiseled_stone_bricks")
        for x in (-24, -23):
            if y + 4 <= 2:
                w.set(x, y + 4, z, "stone_bricks")
    # landing + corridor west to the vault
    w.fill(-26, -9, -21, -22, -9, -19, "polished_deepslate")
    w.fill(-26, -8, -21, -22, -5, -19, AIR)
    w.fill(-27, -10, -22, -21, -4, -18, "stone_bricks", only_air=False, replace=["stone", "dirt"])
    w.fill(-26, -8, -21, -22, -5, -19, AIR)

    # ---- main hall
    x0, x1, z0, z1 = -40, -27, -34, -20
    w.fill(x0 - 1, -10, z0 - 1, x1 + 1, -2, z1 + 1, "stone_bricks")
    w.fill(x0, -9, z0, x1, -9, z1, "polished_deepslate")
    w.fill(x0 + 1, -9, z0 + 1, x1 - 1, -9, z1 - 1, "dark_oak_planks")
    w.fill(x0 + 2, -9, z0 + 2, x1 - 2, -9, z1 - 2, "spruce_planks")
    w.fill(x0, -8, z0, x1, -3, z1, AIR)
    # doorway from the corridor
    w.fill(x1 + 1, -8, -21, x1 + 1, -6, -20, AIR)
    w.set(x1 + 1, -9, -21, "polished_deepslate")
    w.set(x1 + 1, -9, -20, "polished_deepslate")
    # timber pillars & beams
    for x in (x0 + 3, x1 - 3):
        for z in (z0 + 4, z1 - 4):
            w.fill(x, -8, z, x, -3, z, POST)
    for x in range(x0, x1 + 1):
        w.set(x, -3, z0 + 4, "stripped_dark_oak_log[axis=x]")
        w.set(x, -3, z1 - 4, "stripped_dark_oak_log[axis=x]")
    # family armour alcoves on the west wall
    for z in (z0 + 2, z0 + 6, z0 + 10):
        w.fill(x0 - 1, -8, z - 1, x0 - 1, -5, z + 1, "dark_oak_planks")
        w.set(x0, -4, z, "red_wall_banner[facing=east]")
        SARMOR.append((x0, -8, z, -90))
        w.set(x0, -8, z - 1, "white_candle[candles=3,lit=true]")
        w.set(x0, -8, z + 1, "white_candle[candles=3,lit=true]")
    # archive: bookshelves along the north wall
    for x in range(x0, x1 + 1):
        if x in (x0 + 3, x1 - 3):
            continue
        w.set(x, -8, z0, "bookshelf")
        w.set(x, -7, z0, "chiseled_bookshelf[facing=south]" if x % 2 else "bookshelf")
        w.set(x, -6, z0, "bookshelf")
    # treasure storage on the south wall (empty)
    for x in range(x0 + 1, x1, 2):
        w.set(x, -8, z1, "chest[facing=north,type=single]")
        w.set(x + 1, -8, z1, "barrel[facing=north]")
        w.set(x + 1, -7, z1, "barrel[facing=north]")
    # centre table
    for x in range(-35, -31):
        w.set(x, -8, -27, "dark_oak_slab[type=top]")
    w.set(-35, -7, -27, "white_candle[candles=4,lit=true]")
    w.set(-32, -7, -27, "white_candle[candles=4,lit=true]")
    w.set(-34, -7, -27, "decorated_pot")
    w.set(-33, -8, -24, "lectern[facing=north]")
    w.set(x1, -8, z0 + 2, "ender_chest[facing=west]")
    for (x, z) in ((-37, -30), (-30, -30), (-37, -24), (-30, -24)):
        hang(w, x, z, -5, maxup=4)

    # ---- the cavern
    cx, cy, cz = -38, -15, -4
    for x in range(-48, -27):
        for y in range(-20, -9):
            for z in range(-12, 4):
                d = ((x - cx) / 9.0) ** 2 + ((y - cy) / 5.0) ** 2 + ((z - cz) / 7.5) ** 2
                n = 0.12 * math.sin(x * 0.9 + y * 0.7) + 0.1 * math.cos(z * 1.1 - y * 0.5)
                if d + n <= 1.0 and y >= -17:
                    w.set(x, y, z, AIR)
                elif d + n <= 1.45:
                    w.set(x, y, z, rock(x, y, z, ("stone", "tuff", "andesite")))
    # floor
    for x in range(-48, -27):
        for z in range(-12, 4):
            if is_air(w.get(x, -17, z)):
                w.set(x, -18, z, rock(x, -18, z, ("moss_block", "stone", "moss_block")))
    # reflecting pool with glowing lichen
    for x in range(-45, -40):
        for z in range(-9, -4):
            if ((x + 42.5) / 2.6) ** 2 + ((z + 6.5) / 2.6) ** 2 <= 1 and is_air(w.get(x, -17, z)):
                w.set(x, -18, z, "water")
                w.set(x, -19, z, "stone")
    for (x, z) in ((-43, -7), (-42, -6)):
        w.set(x, -18, z, "sea_pickle[pickles=2,waterlogged=true]")
    # ---- descent to the shrine cavern (from the SW corner, south)
    for i in range(9):
        z = z1 + 1 + i
        y = -9 - i
        for x in (-39, -38):
            w.set(x, y, z, stairs("stone_brick", "north"))
            w.set(x, y - 1, z, "stone_bricks")
            for yy in range(y + 1, y + 4):
                w.set(x, yy, z, AIR)
        for x in (-40, -37):
            for yy in range(y, y + 4):
                w.set(x, yy, z, "stone_bricks")
        for x in (-39, -38):
            w.set(x, y + 4, z, "stone_bricks")
    w.fill(-39, -8, z1, -38, -6, z1, AIR)

    # connect the stair bottom
    for x in (-39, -38):
        for z in range(z1 + 9, -8):
            for y in (-17, -16, -15):
                w.set(x, y, z, AIR)
            w.set(x, -18, z, "stone_bricks")
    # nether portal on the south side behind a red torii
    px0, pz = -40, 1
    for x in range(px0, px0 + 4):
        for y in range(-18, -13):
            edge = x in (px0, px0 + 3) or y in (-18, -14)
            corner = x in (px0, px0 + 3) and y in (-18, -14)
            if edge:
                w.set(x, y, pz, "crying_obsidian" if corner else "obsidian")
            else:
                w.set(x, y, pz, "nether_portal[axis=x]")
        for y in range(-17, -13):
            w.set(x, y, pz + 1, "stone")
    for x in range(px0 - 1, px0 + 5):
        w.set(x, -18, pz - 1, "polished_blackstone")
    torii(w, -38, -3, -17, half_width=3, height=7, axis="x", color="red", beam_over=1)
    for (x, z) in ((-44, -2), (-32, -2), (-44, -10), (-32, -10)):
        if is_air(w.get(x, -17, z)):
            w.set(x, -17, z, "stone_brick_wall")
            w.set(x, -16, z, "lantern")
    for (x, z) in ((-41, 0), (-35, 0), (-40, -1), (-36, -1)):
        if is_air(w.get(x, -17, z)):
            w.set(x, -17, z, "red_candle[candles=3,lit=true]")
