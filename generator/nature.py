"""Hand-shaped vegetation: cherry trees (several archetypes), cloud-pruned pines,
bamboo groves, azalea mounds, boulders and ground cover."""
import math
import random

from world import AIR, is_air, parse, with_props, rock

LEAF = "cherry_leaves[persistent=true]"
WOOD = "cherry_wood[axis=y]"
PINE_LEAF = "spruce_leaves[persistent=true]"
PINE_WOOD = "spruce_wood[axis=y]"


def _axis_for(dx, dy, dz):
    a = max((abs(dx), "x"), (abs(dy), "y"), (abs(dz), "z"))[1]
    return a


def _bez(p0, p1, p2, t):
    return tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2))


def limb(w, p0, p1, p2, r0, r1, wood="cherry_wood", steps=None, protect_leaves=False):
    """Quadratic-bezier limb with radius tapering r0 -> r1."""
    L = math.dist(p0, p1) + math.dist(p1, p2)
    n = steps or max(4, int(L * 2.5))
    placed = []
    for i in range(n + 1):
        t = i / n
        c = _bez(p0, p1, p2, t)
        r = r0 + (r1 - r0) * t
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dy in range(-ri, ri + 1):
                for dz in range(-ri, ri + 1):
                    if dx * dx + dy * dy + dz * dz <= r * r + 0.35:
                        x, y, z = int(math.floor(c[0] + dx + 0.5)), int(math.floor(c[1] + dy + 0.5)), \
                            int(math.floor(c[2] + dz + 0.5))
                        w.set(x, y, z, f"{wood}[axis=y]")
                        placed.append((x, y, z))
    return placed


def blob(w, cx, cy, cz, rx, ry, rz, state, rng, density=0.9, only_air=True, flat=0.0, droop=0):
    """Noisy ellipsoid of leaves."""
    for dx in range(-int(rx) - 1, int(rx) + 2):
        for dy in range(-int(ry) - 1, int(ry) + 2):
            for dz in range(-int(rz) - 1, int(rz) + 2):
                d = (dx / rx) ** 2 + (dy / ry) ** 2 + (dz / rz) ** 2
                if dy > 0 and flat:
                    d += flat * dy / ry
                if d <= 1.0 - 0.25 * rng.random() or (d <= 1.12 and rng.random() < 0.35 * density):
                    if d > 0.55 and rng.random() > density:
                        continue
                    x, y, z = int(round(cx + dx)), int(round(cy + dy)), int(round(cz + dz))
                    if only_air and not is_air(w.get(x, y, z)):
                        continue
                    w.set(x, y, z, state)
    # drooping strands under the blob
    for _ in range(droop):
        a = rng.random() * math.tau
        rr = rng.random() ** 0.5
        x = int(round(cx + math.cos(a) * rx * rr * 0.9))
        z = int(round(cz + math.sin(a) * rz * rr * 0.9))
        # find the bottom of the blob at this column
        y = int(round(cy))
        while w.get(x, y - 1, z) == state and y > cy - ry - 2:
            y -= 1
        for k in range(rng.randint(1, 3)):
            if is_air(w.get(x, y - 1 - k, z)):
                w.set(x, y - 1 - k, z, state)


def cherry(w, x, y, z, rng, height=11, spread=7, lean=(0.0, 0.0), trunk_r=0.9, branches=5, style="classic",
           canopy=1.0, petals=True, ground_y=None, lantern=None, uplight=False, glow=False, clearance=None):
    """Custom cherry tree: visible trunk, vase of branches, layered flat blossom clouds.
    (x, y, z): base of trunk (first block above ground)."""
    lx, lz = lean
    H = height
    clear = clearance if clearance is not None else max(3, int(H * 0.45))
    fork = (x + lx * H * 0.3, y + H * 0.42, z + lz * H * 0.3)
    mid = (x + lx * H * 0.08 + rng.uniform(-0.6, 0.6), y + H * 0.2, z + lz * H * 0.08 + rng.uniform(-0.6, 0.6))
    if trunk_r >= 1.3:
        for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            if rng.random() < 0.75:
                w.set(x + dx, y, z + dz, "cherry_wood[axis=y]")
                w.set(x + dx, y - 1, z + dz, "cherry_wood[axis=y]")
    limb(w, (x, y - 1, z), mid, fork, trunk_r, trunk_r * 0.7)
    ends = []
    base_ang = rng.random() * math.tau
    for i in range(branches):
        ang = base_ang + i * math.tau / branches + rng.uniform(-0.4, 0.4)
        reach = spread * rng.uniform(0.72, 1.05)
        ex = fork[0] + math.cos(ang) * reach + lx * spread * 0.4
        ez = fork[2] + math.sin(ang) * reach + lz * spread * 0.4
        if style == "spreading":
            ey = y + H * rng.uniform(0.6, 0.75)
        elif style == "weeping":
            ey = y + H * rng.uniform(0.7, 0.85)
        else:
            ey = y + H * rng.uniform(0.66, 0.86)
        ctrl = (fork[0] + math.cos(ang) * reach * 0.3, ey + rng.uniform(0.5, 2.0),
                fork[2] + math.sin(ang) * reach * 0.3)
        limb(w, fork, ctrl, (ex, ey, ez), trunk_r * 0.6, 0.3)
        ends.append((ex, ey, ez, ang, reach))
        if reach > 3.5 and rng.random() < 0.85:
            a2 = ang + rng.choice((-1, 1)) * rng.uniform(0.5, 0.95)
            p0 = _bez(fork, ctrl, (ex, ey, ez), 0.6)
            e2 = (p0[0] + math.cos(a2) * reach * 0.5, p0[1] + rng.uniform(-0.5, 1.5),
                  p0[2] + math.sin(a2) * reach * 0.5)
            limb(w, p0, ((p0[0] + e2[0]) / 2, p0[1] + 0.8, (p0[2] + e2[2]) / 2), e2, 0.3, 0.2)
            ends.append((e2[0], e2[1], e2[2], a2, reach * 0.55))
    floor_y = y + clear
    for (ex, ey, ez, ang, reach) in ends:
        rx = (1.9 + reach * 0.32) * canopy
        ry = 0.9 + reach * 0.08
        _cloud(w, ex, ey + 0.8, ez, rx, ry, rng, floor_y, droop=(3 if style == "weeping" else 1))
    top = (fork[0] + lx * 1.5, y + H * 0.9, fork[2] + lz * 1.5)
    limb(w, fork, ((fork[0] + top[0]) / 2, top[1] - 2, (fork[2] + top[2]) / 2), top, trunk_r * 0.45, 0.3)
    _cloud(w, top[0], top[1] + 0.5, top[2], spread * 0.42 * canopy + 1, 1.3, rng, floor_y, droop=0)
    if lantern:
        for (ex, ey, ez, ang, reach) in ends[:lantern]:
            hx = int(round(ex - math.cos(ang) * reach * 0.35))
            hz = int(round(ez - math.sin(ang) * reach * 0.35))
            yy = int(round(ey + 1))
            while yy > y and not is_air(w.get(hx, yy - 1, hz)):
                yy -= 1
            if yy - 3 > y + 2 and not is_air(w.get(hx, yy, hz)):
                w.set(hx, yy - 1, hz, "iron_chain[axis=y]")
                w.set(hx, yy - 2, hz, "lantern[hanging=true]")
    if glow:
        for (ex, ey, ez, ang, reach) in ends[: max(1, len(ends) // 2)]:
            gx, gy, gz = int(round(ex)), int(round(ey + 0.8)), int(round(ez))
            if w.get(gx, gy, gz) == LEAF:
                w.set(gx, gy, gz, "shroomlight")
    if petals and ground_y is not None:
        scatter_petals(w, x, z, int(spread) + 2, ground_y, rng)
    return ends


def _cloud(w, cx, cy, cz, rx, ry, rng, floor_y, droop=1):
    """Flat blossom cloud: domed top, flat-ish underside, ragged edge, a few hanging tufts."""
    ix = int(rx) + 2
    iy = int(ry) + 2
    for dx in range(-ix, ix + 1):
        for dz in range(-ix, ix + 1):
            rr = math.hypot(dx, dz) / rx
            if rr > 1.15:
                continue
            edge = rr + rng.uniform(-0.12, 0.12)
            if edge > 1.0:
                continue
            up = ry * math.sqrt(max(0.0, 1 - edge * edge))
            down = ry * 0.45 * math.sqrt(max(0.0, 1 - edge * edge)) + 0.2
            for dy in range(-iy, iy + 1):
                if -down <= dy <= up:
                    X, Y, Z = int(round(cx + dx)), int(round(cy + dy)), int(round(cz + dz))
                    if Y < floor_y:
                        continue
                    if is_air(w.get(X, Y, Z)):
                        w.set(X, Y, Z, LEAF)
    for _ in range(int(rx * 1.5 * droop)):
        a = rng.random() * math.tau
        rr = 0.3 + 0.65 * rng.random()
        X = int(round(cx + math.cos(a) * rx * rr))
        Z = int(round(cz + math.sin(a) * rx * rr))
        Y = int(round(cy))
        while w.get(X, Y - 1, Z) == LEAF:
            Y -= 1
        if w.get(X, Y, Z) != LEAF:
            continue
        for k in range(1, rng.randint(1, 1 + droop) + 1):
            if Y - k < floor_y - 1 or not is_air(w.get(X, Y - k, Z)):
                break
            w.set(X, Y - k, Z, LEAF)


FACE = ("north", "east", "south", "west")


def scatter_petals(w, cx, cz, r, ground_y, rng, dens=0.3):
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d = math.hypot(dx, dz) / r
            if d > 1 or rng.random() > dens * (1 - d * 0.8):
                continue
            x, z = cx + dx, cz + dz
            gy = surface_y(w, x, z, ground_y + 6)
            if gy is None:
                continue
            below = parse(w.get(x, gy, z))[0]
            if below not in ("grass_block", "moss_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt"):
                continue
            if not is_air(w.get(x, gy + 1, z)):
                continue
            amt = 4 if d < 0.45 else 2
            w.set(x, gy + 1, z, f"pink_petals[flower_amount={amt},facing={FACE[(cx + cz) % 4]}]")


def surface_y(w, x, z, ymax):
    for y in range(ymax, -14, -1):
        s = w.get(x, y, z)
        n = parse(s)[0]
        if s != AIR and n != "light" and not n.endswith("_leaves") and n not in ("pink_petals",):
            return y
    return None


def pine(w, x, y, z, rng, height=7, pads=5, spread=4, lean=(0.0, 0.0)):
    """Cloud-pruned Japanese black pine (niwaki)."""
    lx, lz = lean
    pts = []
    cx, cz = float(x), float(z)
    for i in range(height):
        cx += lx + rng.uniform(-0.35, 0.35)
        cz += lz + rng.uniform(-0.35, 0.35)
        pts.append((int(round(cx)), y + i, int(round(cz))))
    for p in pts:
        w.set(*p, PINE_WOOD)
    top = pts[-1]
    # pads on horizontal arms
    for k in range(pads):
        t = 0.35 + 0.65 * k / max(pads - 1, 1)
        base = pts[int(t * (len(pts) - 1))]
        ang = rng.random() * math.tau
        reach = spread * (1.1 - t * 0.6) * rng.uniform(0.8, 1.1)
        ex, ez = base[0] + math.cos(ang) * reach, base[2] + math.sin(ang) * reach
        ey = base[1] + rng.uniform(0, 1.5)
        limb(w, base, ((base[0] + ex) / 2, base[1] + 0.8, (base[2] + ez) / 2), (ex, ey, ez), 0.35, 0.2,
             wood="spruce_wood")
        r = 1.6 + reach * 0.35
        blob(w, ex, ey + 0.8, ez, r * 1.1, 0.9, r * 1.1, PINE_LEAF, rng, density=0.95, flat=0.6)
    blob(w, top[0], top[1] + 1.2, top[2], 2.4, 1.1, 2.4, PINE_LEAF, rng, density=0.95, flat=0.6)


def bamboo_clump(w, cx, cz, r, ground_y, rng, density=0.45, hmin=8, hmax=14, exclude=None):
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            if math.hypot(dx, dz) > r + 0.3 or rng.random() > density:
                continue
            x, z = cx + dx, cz + dz
            if exclude and exclude(x, z):
                continue
            bamboo_stalk(w, x, z, ground_y, rng, hmin, hmax)


def bamboo_stalk(w, x, z, ground_y, rng, hmin=8, hmax=14):
    gy = ground_y
    if parse(w.get(x, gy, z))[0] not in ("grass_block", "dirt", "podzol", "coarse_dirt", "moss_block",
                                         "rooted_dirt", "gravel", "mud"):
        return
    if not is_air(w.get(x, gy + 1, z)):
        return
    h = rng.randint(hmin, hmax)
    thick = 1 if rng.random() < 0.7 else 0
    for i in range(h):
        yy = gy + 1 + i
        if not is_air(w.get(x, yy, z)):
            h = i
            break
    if h < 3:
        return
    for i in range(h):
        yy = gy + 1 + i
        if i >= h - 3:
            st = f"bamboo[age={thick},leaves=large,stage=1]"
        else:
            st = f"bamboo[age={thick},leaves=none,stage=1]"
        w.set(x, yy, z, st)


def azalea_mound(w, cx, y, cz, r, rng, flowering=0.5, h=None):
    """Karikomi: clipped round azalea shrub. y = first air block above ground."""
    hh = h or max(1.2, r * 0.7)
    for dx in range(-int(r) - 1, int(r) + 2):
        for dz in range(-int(r) - 1, int(r) + 2):
            for dy in range(0, int(hh) + 2):
                d = (dx / r) ** 2 + (dz / r) ** 2 + (dy / hh) ** 2
                if d <= 1.0:
                    st = "flowering_azalea_leaves[persistent=true]" if rng.random() < flowering else \
                        "azalea_leaves[persistent=true]"
                    if is_air(w.get(cx + dx, y + dy, cz + dz)):
                        w.set(cx + dx, y + dy, cz + dz, st)


def boulder(w, cx, y, cz, r, rng, mats=("stone", "andesite", "tuff", "mossy_cobblestone", "cobblestone"),
            moss_top=True, sink=1):
    """Irregular garden rock. y = ground surface level (top block of ground)."""
    ry = r * rng.uniform(0.6, 0.9)
    for dx in range(-int(r) - 1, int(r) + 2):
        for dz in range(-int(r) - 1, int(r) + 2):
            for dy in range(-sink, int(ry) + 2):
                d = (dx / r) ** 2 + (dz / r) ** 2 + (max(dy, 0) / max(ry, 0.5)) ** 2
                if d <= 1.0 - 0.2 * rng.random():
                    m = rock(cx + dx, y + dy, cz + dz, mats[:3])
                    w.set(cx + dx, y + dy, cz + dz, m)
    if moss_top:
        for dx in range(-int(r), int(r) + 1):
            for dz in range(-int(r), int(r) + 1):
                if rng.random() < 0.35:
                    x, z = cx + dx, cz + dz
                    for yy in range(y + int(ry) + 2, y - 1, -1):
                        s = w.get(x, yy, z)
                        if not is_air(s):
                            if parse(s)[0] in ("stone", "andesite", "tuff", "cobblestone", "mossy_cobblestone") \
                                    and is_air(w.get(x, yy + 1, z)):
                                w.set(x, yy + 1, z, "moss_carpet")
                            break


def ground_cover(w, x0, x1, z0, z1, rng, ymax, p_grass=0.12, p_fern=0.03, p_flower=0.02,
                 flowers=("white_tulip", "pink_tulip", "lily_of_the_valley", "azure_bluet", "oxeye_daisy"),
                 exclude=None):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if exclude and exclude(x, z):
                continue
            gy = surface_y(w, x, z, ymax)
            if gy is None:
                continue
            s = parse(w.get(x, gy, z))[0]
            if s not in ("grass_block", "moss_block") or not is_air(w.get(x, gy + 1, z)):
                continue
            r = rng.random()
            if r < p_grass:
                w.set(x, gy + 1, z, "short_grass")
            elif r < p_grass + p_fern:
                w.set(x, gy + 1, z, "fern")
            elif r < p_grass + p_fern + p_flower:
                w.set(x, gy + 1, z, rng.choice(flowers))


def close_canopy(w, x0, x1, y0, y1, z0, z1, leaf=LEAF, passes=2):
    """Fill hidden air pockets inside blossom clouds (fewer commands, no visual change)."""
    import numpy as np
    from world import X0, Y0, Z0
    lid = w.pid(leaf)
    sl = (slice(x0 - X0, x1 - X0 + 1), slice(y0 - Y0, y1 - Y0 + 1), slice(z0 - Z0, z1 - Z0 + 1))
    for _ in range(passes):
        g = w.g[sl]
        L = g == lid
        A = g == 0
        cnt = np.zeros(g.shape, dtype=np.int8)
        for ax in range(3):
            for d in (1, -1):
                cnt += np.roll(L, d, axis=ax)
        fill = A & (cnt >= 5)
        # also cells sandwiched vertically inside a cloud
        fill |= A & np.roll(L, 1, axis=1) & np.roll(L, -1, axis=1) & (cnt >= 4)
        g[fill] = lid


def hide_inner_wood(w, x0, x1, y0, y1, z0, z1, wood="cherry_wood[axis=y]", leaf=LEAF):
    """Wood completely buried inside blossom is invisible: turn it into blossom so fills merge."""
    import numpy as np
    from world import X0, Y0, Z0
    if wood not in w.index:
        return
    wid, lid = w.index[wood], w.pid(leaf)
    sl = (slice(x0 - X0, x1 - X0 + 1), slice(y0 - Y0, y1 - Y0 + 1), slice(z0 - Z0, z1 - Z0 + 1))
    for _ in range(2):
        g = w.g[sl]
        W = g == wid
        L = g == lid
        solid = W | L
        enclosed = W.copy()
        nl = np.zeros(g.shape, dtype=np.int8)
        for ax in range(3):
            for d in (1, -1):
                enclosed &= np.roll(solid, d, axis=ax)
                nl += np.roll(L, d, axis=ax)
        g[enclosed & (nl >= 2)] = lid
