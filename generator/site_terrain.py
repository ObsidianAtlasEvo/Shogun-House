"""Site grading: estate plinth, manor podium, north berm & waterfall mound,
shrine terrace, ponds, streams and paths."""
import math

import numpy as np

from world import AIR, X0, Z0, parse

# ---------------------------------------------------------------- regions
EST = (-62, 62, -62, 62)          # the walled estate
APP = (-44, 44, 63, 108)          # arrival approach outside the south wall
WORK = (-70, 70, -70, 110)        # everything we clear / rebuild

WATER_Y = -1                      # water surface in the estate ponds
APP_WATER_Y = -2                  # approach stream sits one below the plains


def noise2(x, z, seed=0.0):
    return (math.sin(x * 0.37 + seed) * 0.5 + math.sin(z * 0.29 + seed * 1.7) * 0.5 +
            math.sin((x + z) * 0.21 + seed * 2.3) * 0.35 + math.sin((x - z) * 0.53 + seed * 0.7) * 0.2)


def ell(x, z, cx, cz, rx, rz):
    return ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2


# ---------------------------------------------------------------- water bodies
MOON_POND = [(-10, -42, 24, 10), (16, -40, 12, 8), (-40, -46, 11, 9), (-4, -31, 11, 4.5), (6, -49, 6, 5.5),
             (-26, -40, 8, 6)]
ISLAND = (-6, -44, 5.0)
TURTLE = (15, -41, 2.2)
KOI_POND = [(34, 45, 12, 10), (29, 36, 7, 6), (42, 36, 5, 5)]
PRIV_POND = [(-33, 1, 7, 5), (-27, 5, 4, 3)]
BATH_POOL = [(-54, -13, 6, 6.5), (-50, -9, 4, 4)]

STREAM = [(26, 38), (18, 37), (10, 36), (3, 37), (-3, 37), (-9, 38), (-14, 35), (-18, 29), (-19, 22),
          (-19, 16), (-21, 10), (-25, 5)]
APP_STREAM = [(-44, 92), (-34, 91), (-24, 89), (-14, 90), (-6, 90), (0, 90), (6, 90), (14, 89), (24, 90),
              (34, 92), (44, 91)]


def in_union(x, z, ells, jitter=0.0, seed=0.0):
    v = min(ell(x, z, *e) for e in ells)
    if jitter:
        v += jitter * noise2(x, z, seed) * 0.12
    return v


def seg_dist(px, pz, ax, az, bx, bz):
    vx, vz = bx - ax, bz - az
    L2 = vx * vx + vz * vz
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * vx + (pz - az) * vz) / L2))
    return math.hypot(px - (ax + t * vx), pz - (az + t * vz))


def poly_dist(px, pz, pts):
    return min(seg_dist(px, pz, *pts[i], *pts[i + 1]) for i in range(len(pts) - 1))


# ---------------------------------------------------------------- manor podium outline (surface y = 2)
PODIUM_RECTS = [(-19, 19, -27, 12), (-44, -17, -37, -14), (17, 44, -13, 13)]


def in_podium(x, z):
    return any(a <= x <= b and c <= z <= d for (a, b, c, d) in PODIUM_RECTS)


class Terrain:
    """Height map + surface material map, then materialised into the world."""

    def __init__(self, w):
        self.w = w
        self.h = {}
        self.mat = {}
        self.water = {}   # (x,z) -> (surface_y, bed_y)

    def H(self, x, z):
        return self.h.get((x, z), -1)

    def build(self):
        w = self.w
        x0, x1, z0, z1 = WORK
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                self.h[(x, z)] = -1
                self.mat[(x, z)] = "grass_block"
        # estate plinth (1 above plains)
        for x in range(EST[0], EST[1] + 1):
            for z in range(EST[2], EST[3] + 1):
                self.h[(x, z)] = 0
        # north berm + NW/NE shoulders + waterfall mound
        for x in range(EST[0], EST[1] + 1):
            for z in range(EST[2], -44):
                t = (-52 - z) / 10.0
                b = 5.2 * max(0.0, min(1.0, t + 0.15)) ** 1.3 + noise2(x, z, 3.1) * 0.8
                # corners rise more
                cx = max(0.0, (abs(x) - 40) / 22.0)
                b += cx * 2.0 * max(0.0, min(1.0, (-44 - z) / 14))
                mound = 8.5 * math.exp(-(((x - 7.5) / 7.5) ** 2 + ((z + 58) / 5.5) ** 2))
                hh = max(0, int(round(max(b, mound))))
                self.h[(x, z)] = max(self.h[(x, z)], hh)
        # west shoulder behind the moon pavilion (bamboo slope)
        for x in range(EST[0], -50):
            for z in range(-60, -40):
                d = (x + 50) / -12.0
                hh = int(round(3.0 * max(0.0, min(1.0, d)) + noise2(x, z, 5.5) * 0.5))
                self.h[(x, z)] = max(self.h[(x, z)], hh)
        # shrine terrace
        for x in range(34, 62):
            for z in range(-61, -43):
                self.h[(x, z)] = max(self.h[(x, z)], 4)
        # manor podium
        for x in range(-45, 46):
            for z in range(-38, 14):
                if in_podium(x, z):
                    self.h[(x, z)] = 2
                    self.mat[(x, z)] = "podium"
        # dojo plinth
        for x in range(-47, -24):
            for z in range(23, 41):
                self.h[(x, z)] = 1
                self.mat[(x, z)] = "podium"
        # ponds ------------------------------------------------------------
        for x in range(-58, 34):
            for z in range(-58, -24):
                if in_podium(x, z):
                    continue
                v = in_union(x, z, MOON_POND, jitter=1.0, seed=1.0)
                if v <= 1.0:
                    depth = 1 + int(round(3 * (1 - v) ** 0.6))
                    self.water[(x, z)] = (WATER_Y, WATER_Y - depth)
        for x in range(18, 50):
            for z in range(26, 58):
                v = in_union(x, z, KOI_POND, jitter=1.0, seed=2.0)
                if v <= 1.0:
                    depth = 1 + int(round(2.5 * (1 - v) ** 0.6))
                    self.water[(x, z)] = (WATER_Y, WATER_Y - depth)
        for x in range(-44, -18):
            for z in range(-8, 12):
                v = in_union(x, z, PRIV_POND, jitter=1.0, seed=4.0)
                if v <= 1.0:
                    self.water[(x, z)] = (WATER_Y, WATER_Y - 2)
        # front stream
        for x in range(-30, 30):
            for z in range(0, 44):
                d = poly_dist(x, z, STREAM)
                if d <= 1.2 + 0.4 * math.sin(x * 0.4 + z * 0.3):
                    if (x, z) not in self.water:
                        self.water[(x, z)] = (WATER_Y, WATER_Y - 2)
        # approach stream
        for x in range(-44, 45):
            for z in range(84, 98):
                d = poly_dist(x, z, APP_STREAM)
                if d <= 1.6 + 0.5 * math.sin(x * 0.3):
                    self.water[(x, z)] = (APP_WATER_Y, APP_WATER_Y - 2)
        # islands
        for x in range(-12, 1):
            for z in range(-50, -37):
                r = math.hypot(x - ISLAND[0], z - ISLAND[1]) + noise2(x, z, 7) * 0.4
                if r <= ISLAND[2]:
                    self.water.pop((x, z), None)
                    self.h[(x, z)] = 2 if r < 3.2 else 1
                    self.mat[(x, z)] = "moss_block" if r < 3.2 else "grass_block"
        for x in range(12, 19):
            for z in range(-44, -37):
                if math.hypot(x - TURTLE[0], z - TURTLE[1]) <= TURTLE[2]:
                    self.water.pop((x, z), None)
                    self.h[(x, z)] = 0
                    self.mat[(x, z)] = "moss_block"
        for (x, z), (ws, bed) in self.water.items():
            self.h[(x, z)] = bed

    def materialise(self):
        w = self.w
        x0, x1, z0, z1 = WORK
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                hh = self.h[(x, z)]
                m = self.mat[(x, z)]
                if (x, z) in self.water:
                    ws, bed = self.water[(x, z)]
                    w.set(x, bed, z, "gravel" if ws == WATER_Y else "clay")
                    w.fill(x, bed + 1, z, x, ws, z, "water")
                    w.fill(x, ws + 1, z, x, 0, z, AIR)
                    continue
                if hh >= 0:
                    w.fill(x, -1, z, x, hh - 1, z, "dirt")
                if m == "podium":
                    w.fill(x, -1, z, x, hh, z, "stone")
                    w.set(x, hh, z, "stone_bricks")
                else:
                    w.set(x, hh, z, m if m != "podium" else "stone")
