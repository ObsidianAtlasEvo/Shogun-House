"""Block-light simulation and spawn-proofing with invisible light blocks.

Hostile mobs (1.18+) only spawn where block light is 0, so the solver
finds every spawnable cell inside the estate that sits in total darkness
and drops the fewest practical invisible light blocks to reach level >= 1.
Visible lanterns do the art; these just remove the dark gaps between them."""
from collections import deque

import numpy as np

from world import X0, Y0, Z0, blocks_light, light_emission, spawn_floor, spawn_space, parse


def _tables(world):
    P = world.palette
    emit = np.array([light_emission(s) for s in P], dtype=np.int16)
    transmit = np.array([not blocks_light(s) for s in P], dtype=bool)
    floor = np.array([spawn_floor(s) for s in P], dtype=bool)
    space = np.array([spawn_space(s) for s in P], dtype=bool)
    return emit, transmit, floor, space


def compute_light(world):
    emit, transmit, _, _ = _tables(world)
    E = emit[world.g]
    T = transmit[world.g]
    L = E.copy()
    for _ in range(15):
        n = L.copy()
        m = np.maximum
        n[1:] = m(n[1:], L[:-1] - 1)
        n[:-1] = m(n[:-1], L[1:] - 1)
        n[:, 1:] = m(n[:, 1:], L[:, :-1] - 1)
        n[:, :-1] = m(n[:, :-1], L[:, 1:] - 1)
        n[:, :, 1:] = m(n[:, :, 1:], L[:, :, :-1] - 1)
        n[:, :, :-1] = m(n[:, :, :-1], L[:, :, 1:] - 1)
        n = np.where(T, n, E)
        n = np.maximum(n, E)
        n = np.maximum(n, 0)
        if np.array_equal(n, L):
            break
        L = n
    return L


def spawnable(world, region):
    _, _, floor, space = _tables(world)
    G = world.g
    sp = np.zeros(G.shape, dtype=bool)
    sp[:, 1:, :] = space[G[:, 1:, :]] & floor[G[:, :-1, :]]
    return sp & region


def region_mask(world, rects, ymin=-26, ymax=44):
    m = np.zeros(world.g.shape, dtype=bool)
    for (xa, xb, za, zb) in rects:
        m[xa - X0:xb - X0 + 1, ymin - Y0:ymax - Y0 + 1, za - Z0:zb - Z0 + 1] = True
    return m


def _bfs_add(L, T, sx, sy, sz, level):
    nx, ny, nz = L.shape
    if L[sx, sy, sz] >= level:
        return
    L[sx, sy, sz] = level
    dq = deque([(sx, sy, sz)])
    while dq:
        x, y, z = dq.popleft()
        v = L[x, y, z] - 1
        if v <= 0:
            continue
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            a, b, c = x + dx, y + dy, z + dz
            if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz and T[a, b, c] and L[a, b, c] < v:
                L[a, b, c] = v
                dq.append((a, b, c))


def spawn_proof(world, region, level=6, max_lights=4000):
    """Place invisible light blocks until no spawnable cell in region is dark."""
    emit, transmit, floor, space = _tables(world)
    L = compute_light(world)
    T = transmit[world.g]
    sp = spawnable(world, region)
    dark = sp & (L == 0)
    placed = 0
    air_id = 0
    cand = np.argwhere(dark)
    # sweep in a coarse order so lights end up spread evenly
    order = np.lexsort((cand[:, 1], cand[:, 2] // 5, cand[:, 0] // 5))
    cand = cand[order]
    for (x, y, z) in cand:
        if L[x, y, z] > 0:
            continue
        # choose an air cell for the light: the cell itself, or 1 above
        tx, ty, tz = x, y, z
        if world.g[x, y, z] != air_id:
            if y + 1 < world.g.shape[1] and world.g[x, y + 1, z] == air_id:
                ty = y + 1
            else:
                continue
        # prefer to lift the light one block when there is headroom (lights more floor)
        if ty == y and y + 1 < world.g.shape[1] and world.g[x, y + 1, z] == air_id and level >= 5:
            ty = y + 1
        world.g[tx, ty, tz] = world.pid(f"light[level={level}]")
        T[tx, ty, tz] = True
        _bfs_add(L, T, tx, ty, tz, level)
        if L[x, y, z] == 0:
            _bfs_add(L, T, x, y, z, 1)
        placed += 1
        if placed >= max_lights:
            break
    remaining = int((sp & (L == 0)).sum())
    return placed, remaining, L
