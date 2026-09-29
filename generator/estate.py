"""Sakura Shogun Estate - top level build script.

    python3 estate.py      builds the model, writes previews and the command file
"""
import os
import random
import sys
import time

import numpy as np

from world import World, X0, Y0, Z0, AIR
import site_terrain as T
import site_manor as M
import site_zones as Z
import site_planting as P
import site_vault as V
import site_access as A

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PREV = os.environ.get("PREVIEW_DIR", os.path.join(ROOT, "previews"))

# the waterfall curtain is the only place water is allowed to flow
FLOW_OK = {(x, y, -53) for x in (7, 8) for y in range(0, 8)}


def baseline(w):
    """World state right after the clear + base fills (before the model is written)."""
    b = np.zeros_like(w.g)
    stone, dirt, grass = w.pid("stone"), w.pid("dirt"), w.pid("grass_block")
    b[:, : -6 - Y0 + 1, :] = stone
    b[:, -5 - Y0: -2 - Y0 + 1, :] = dirt
    b[:, -1 - Y0, :] = grass
    return b


def work_region(w):
    m = np.zeros(w.g.shape, dtype=bool)
    x0, x1, z0, z1 = T.WORK
    m[x0 - X0:x1 - X0 + 1, -24 - Y0:, z0 - Z0:z1 - Z0 + 1] = True
    return m


def entities(w):
    """Decor entities (no loot anywhere - frames and stands only)."""
    E = []
    # family armour in the vault
    kit = [("netherite", "netherite", "iron", "netherite"), ("iron", "chainmail", "iron", "iron"),
           ("golden", "netherite", "chainmail", "golden")]
    for (x, y, z, yaw), (h, c, l, b) in zip(V.SARMOR, kit):
        E.append(armor(x, y, z, yaw, h, c, l, b))
    # dojo armoury flanking the master's platform
    E.append(armor(-43, 3, 26, 180, "iron", "iron", "iron", "iron"))
    E.append(armor(-29, 3, 26, 180, "chainmail", "chainmail", "chainmail", "chainmail"))
    # dojo weapon wall (east side, facing west into the hall)
    for z, item in ((27, "iron_sword"), (30, "bow"), (32, "netherite_sword"), (34, "crossbow"), (36, "iron_axe")):
        w.set(-46, 5, z, "dark_oak_planks")
        E.append(f'summon item_frame ~-45 ~5 ~{z} {{Facing:5b,Fixed:1b,Invulnerable:1b,Item:{{id:"minecraft:{item}",count:1}}}}')
    # strategy-room map wall: empty glow frames ready for maps (north wall of the East Wing, facing south)
    for x in range(33, 38):
        w.set(x, 5, -9, "white_concrete")
        for y in (5, 6):
            E.append(f"summon glow_item_frame ~{x} ~{y} ~-8 {{Facing:3b,Fixed:1b,Invulnerable:1b}}")
    # koi
    koi = [(34, 44), (30, 48), (38, 40), (27, 38), (40, 50), (-8, -36), (4, -40), (-20, -44), (-30, -48), (10, -46)]
    koi = [nearest_water(w, x, z) for (x, z) in koi]
    for i, (x, z) in enumerate(koi):
        var = (1) | (1 << 8) | ((1 if i % 2 else 0) << 16) | ((14 if i % 3 else 0) << 24)
        E.append(f"summon tropical_fish ~{x} ~-2 ~{z} {{Variant:{var},PersistenceRequired:1b}}")
    return E


def nearest_water(w, x, z):
    for r in range(0, 6):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if w.get(x + dx, -2, z + dz) == "water" and w.get(x + dx, -1, z + dz) == "water":
                    return (x + dx, z + dz)
    raise ValueError((x, z))


def armor(x, y, z, yaw, h, c, l, b):
    return (f'summon armor_stand ~{x} ~{y} ~{z} {{Rotation:[{yaw}f,0f],'
            f'equipment:{{head:{{id:"{h}_helmet"}},chest:{{id:"{c}_chestplate"}},'
            f'legs:{{id:"{l}_leggings"}},feet:{{id:"{b}_boots"}}}}}}')


def build():
    w = World()
    rng = random.Random(1868)
    w.g[:] = baseline(w)
    t = T.Terrain(w)
    t.build()
    t.materialise()
    Z.T_WATER.clear()
    Z.T_WATER.update(t.water)
    Z.TERRAIN = t
    M.podium(w, rng)
    M.great_hall(w, rng)
    M.porch(w, rng)
    M.west_wing(w, rng)
    M.east_wing(w, rng)
    M.manor_roofs(w)
    M.interiors(w, rng)
    M.moon_bridge(w)
    M.tsukimidai(w)
    Z.estate_walls(w, rng)
    Z.main_gate(w, rng)
    Z.nagaya(w, rng)
    Z.approach(w, rng)
    Z.forecourt(w, rng)
    Z.moon_garden(w, rng)
    Z.shrine(w, rng)
    Z.dojo(w, rng)
    Z.tea_house(w, rng)
    Z.bath(w, rng)
    Z.service(w, rng)
    V.vault(w, rng)
    P.plant(w, rng, t.water)
    P.bamboo(w, rng, t.water)
    P.shrubs_and_cover(w, rng, t.water)
    P.water_life(w, rng, t.water)
    P.uplights(w)
    M.veranda_lanterns(w)
    A.access(w)
    w.entities = entities(w)
    return w, t


def compile_all(w, write=True, base=None):
    """Spawn-proof, compile and write the single command file."""
    from lighting import spawn_proof, region_mask, compute_light
    from emit import compile_model, chunked, PFX
    region = region_mask(w, [T.EST, T.APP], ymin=-22, ymax=44)
    # keep the invisible lights of the first release where they still fit, so a fix run
    # only touches what actually changed
    import json
    kept = 0
    for (x, y, z, lv) in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data",
                                                     "lights_v1.json"))):
        if w.get(x, y, z) == AIR:
            w.set(x, y, z, f"light[level={lv}]")
            kept += 1
    placed, remaining, L = spawn_proof(w, region, level=7)
    print("kept lights:", kept)
    print("invisible light blocks:", placed, "dark spawnable cells left:", remaining)
    base = baseline(w) if base is None else base
    cmds, pair_cmds = compile_model(w, base, work_region(w))
    return cmds, pair_cmds, L


SEL = "positioned ~-74 ~-30 ~-74"
BOX = "dx=148,dy=80,dz=186"


def write_commands(w, path):
    from emit import chunked, PFX
    cmds, pair_cmds, L = compile_all(w)
    ents = w.entities
    lines = []
    A = lines.append
    A("# SAKURA SHOGUN ESTATE - complete build, one pass")
    A("# Every placement is relative to {C}; the .bat substitutes the centre you choose.")
    A("# Lines starting with # are directives/comments for the runner and are never typed.")
    A("#SETUP")
    A("/gamemode spectator @s")
    A("/execute positioned {C} run tp @s ~ ~62 ~24 180 58")
    A("/execute positioned {C} run forceload add ~-74 ~-74 ~74 ~112")
    A("#WAIT 6000")
    A("/tick freeze")
    A("#ENDSETUP")
    A("#SECTION Clearing the old estate")
    for t in ("armor_stand", "item_frame", "glow_item_frame", "painting", "item", "experience_orb",
              "tropical_fish", "falling_block", "leash_knot"):
        A(f"/execute positioned {{C}} {SEL} run kill @e[type=minecraft:{t},{BOX}]")
    x0, x1, z0, z1 = T.WORK
    for c in chunked(x0, 0, z0, x1, 44, z1, "air"):
        A(c)
    A("#SECTION Rebuilding the ground")
    for c in chunked(x0, -24, z0, x1, -6, z1, "stone"):
        A(c)
    for c in chunked(x0, -5, z0, x1, -2, z1, "dirt"):
        A(c)
    for c in chunked(x0, -1, z0, x1, -1, z1, "grass_block"):
        A(c)
    names = {0: "Carving the vault and cavern", 1: "Terrain, architecture, roofs and trees", 2: "Ponds, streams and the waterfall",
             3: "Lantern chains", 4: "Plants, lanterns, candles and details", 5: "Hanging lanterns",
             6: "Invisible spawn-proof light"}
    last = None
    for k, c in cmds:
        if k != last:
            A(f"#SECTION {names[k]}")
            last = k
        A(c)
    A("#SECTION Beds")
    lines.extend(pair_cmds)
    A("#SECTION Armour, weapon wall, map wall and koi")
    for e in ents:
        A(f"/execute positioned {{C}} run {e}")
    A("#SECTION Finishing")
    A("/tick unfreeze")
    A("#WAIT 3000")
    A(f"/execute positioned {{C}} {SEL} run kill @e[type=minecraft:item,{BOX}]")
    A("/execute positioned {C} run forceload remove ~-74 ~-74 ~74 ~112")
    A("#IF SUNSET /time set 12400")
    A("/gamemode {MODE} @s")
    A("/execute positioned {C} run tp @s ~ ~1 ~61 180 4")
    A('/title @s subtitle {"text":"Walk slowly. The garden was made for dusk.","color":"#f5c6d6","italic":true}')
    A('/title @s title {"text":"Sakura Shogun Estate","color":"#ffd7e4"}')
    # validation
    bad = [l for l in lines if not l.startswith("#") and len(l.replace("{C}", "-29999999.5 319 -29999999.5")
                                                              .replace("{MODE}", "survival")) > 255]
    assert not bad, bad[:3]
    with open(path, "w", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")
    n = sum(1 for l in lines if l.startswith("/") or l.startswith("#IF"))
    return n, L


def old_model_grid(w, pkl):
    """The as-built world of the first release, mapped into this world's palette."""
    import json
    meta = json.load(open(pkl + ".json"))
    g = np.load(pkl + ".npz")["g"].astype(np.int32)
    remap = np.array([w.pid(s) for s in meta["palette"]], dtype=np.int32)
    return remap[g], meta.get("entities", [])


def write_fix(w, old_pkl, path):
    """Repair file: only the cells that differ between the as-built estate and the fixed model,
    plus any attachment (flower, lantern, petal...) touching a changed cell so nothing pops off."""
    from emit import compile_model, klass
    old, old_ents = old_model_grid(w, old_pkl)
    # lights first (same as the full build) so both files describe the same final estate
    compile_all(w, base=old)  # places the light blocks into w
    G = w.g
    diff = G != old
    attach = np.array([klass(s) in (4, 5) for s in w.palette])
    near = np.zeros_like(diff)
    for ax in range(3):
        for d in (1, -1):
            near |= np.roll(diff, d, axis=ax)
    touch = near & attach[G] & ~diff
    base = old.copy()
    base[touch] = -1          # force re-placement of those attachments after their neighbours change
    cmds, pair_cmds = compile_model(w, base, work_region(w))
    changed_pairs = []
    for parts in w.pairs:
        if any(diff[x - X0, y - Y0, z - Z0] for (x, y, z, s) in parts):
            changed_pairs += [c for c in pair_cmds if any(f" ~{x} ~{y} ~{z} " in c.replace("~ ", "~0 ") for (x, y, z, s) in parts)]
    lines = []
    A = lines.append
    A("# SAKURA SHOGUN ESTATE - repair pass for an estate built with the first release")
    A("# Only changed blocks are placed. {C} is replaced by the centre set in the .bat.")
    A("#SETUP")
    A("/gamemode spectator @s")
    A("/execute positioned {C} run tp @s ~ ~62 ~24 180 58")
    A("/execute positioned {C} run forceload add ~-74 ~-74 ~74 ~112")
    A("#WAIT 6000")
    A("/tick freeze")
    A("#ENDSETUP")
    names = {0: "Clearing what the fixes replace", 1: "Steps, stair flights, floors and structure",
             2: "Water", 3: "Chains", 4: "Re-seating plants, lanterns and details", 5: "Hanging lanterns",
             6: "Invisible light"}
    last = None
    for k, c in cmds:
        if k != last:
            A(f"#SECTION {names[k]}")
            last = k
        A(c)
    if changed_pairs:
        A("#SECTION Beds")
        lines.extend(changed_pairs)
    A("#SECTION Finishing")
    A("/tick unfreeze")
    A("#WAIT 3000")
    A(f"/execute positioned {{C}} {SEL} run kill @e[type=minecraft:item,{BOX}]")
    A("/execute positioned {C} run forceload remove ~-74 ~-74 ~74 ~112")
    A("/gamemode {MODE} @s")
    A("/execute positioned {C} run tp @s ~ ~1 ~17 180 8")
    A('/title @s subtitle {"text":"Every step, stair and threshold now walks true.","color":"#f5c6d6","italic":true}')
    A('/title @s title {"text":"Estate repaired","color":"#ffd7e4"}')
    bad = [l for l in lines if not l.startswith("#") and len(l.replace("{C}", "-29999999.5 319 -29999999.5")) > 255]
    assert not bad, bad[:3]
    with open(path, "w", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")
    n_cells = int(diff.sum())
    return sum(1 for l in lines if l.startswith("/")), n_cells, int(touch.sum()), old_ents == w.entities


if __name__ == "__main__":
    import render
    from finalize import finalize, check_water
    from validate import check_palette
    os.makedirs(PREV, exist_ok=True)
    t0 = time.time()
    w, t = build()
    finalize(w)
    print("built", round(time.time() - t0, 1), "s")
    leaks = check_water(w, FLOW_OK)
    assert not leaks, leaks[:20]
    from support import check_support
    unsupported = check_support(w)
    assert not unsupported, unsupported[:20]
    import audit
    problems = {k: v for k, v in audit.run(w, verbose=False).items() if v}
    assert not problems, problems
    out_dir = os.path.join(ROOT, "SAKURA_SHOGUN_ESTATE", "commands")
    os.makedirs(out_dir, exist_ok=True)
    n, L = write_commands(w, os.path.join(out_dir, "sakura_estate_full.txt"))
    used = {w.palette[i] for i in np.unique(w.g)} | {s for parts in w.pairs for (_, _, _, s) in parts}
    errs = check_palette(used)
    assert not errs, errs
    print("commands:", n, "| block states validated:", len(used))
    old_pkl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "estate_v1_as_built")
    if os.path.exists(old_pkl + ".npz"):
        w2, _ = build()
        finalize(w2)
        nf, cells, touched, same_ents = write_fix(w2, old_pkl, os.path.join(out_dir, "sakura_estate_fix_v2.txt"))
        print(f"fix file: {nf} commands, {cells} changed blocks, {touched} attachments re-seated, "
              f"entities unchanged: {same_ents}")
    if "--no-render" not in sys.argv:
        render.plan(w, os.path.join(PREV, "plan.png"), px=4)
        render.iso(w, os.path.join(PREV, "aerial_day.png"), "SE", box=(-66, 66, -8, 34, -66, 110), scale=1)
        render.iso(w, os.path.join(PREV, "aerial_night.png"), "SE", box=(-66, 66, -8, 34, -66, 110), night=True,
                   light=L, scale=1)
        render.iso(w, os.path.join(PREV, "moon_garden.png"), "NW", box=(-62, 34, -6, 30, -62, -10), scale=2)
        render.iso(w, os.path.join(PREV, "moon_garden_night.png"), "NW", box=(-62, 34, -6, 30, -62, -10),
                   night=True, light=L, scale=2)
        render.iso(w, os.path.join(PREV, "arrival.png"), "SW", box=(-24, 24, -2, 30, 30, 108), scale=2)
        render.iso(w, os.path.join(PREV, "manor.png"), "SE", box=(-46, 46, -2, 30, -40, 16), scale=2)
        render.iso(w, os.path.join(PREV, "vault_cutaway.png"), "SE", box=(-50, -18, -22, 4, -38, 6), ycut=-5, scale=3)
        print("previews in", PREV)
