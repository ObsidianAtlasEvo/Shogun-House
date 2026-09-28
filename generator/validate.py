"""Validate every block state against the Minecraft 26.1 block registry (minecraft-data)."""
import json
import os

from world import parse

_DB = None


def db():
    global _DB
    if _DB is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "blocks_26.1.json")
        _DB = {b["name"]: b for b in json.load(open(p))}
    return _DB


def check_state(state):
    n, props = parse(state)
    b = db().get(n)
    if b is None:
        return f"unknown block {n}"
    spec = {s["name"]: s for s in b.get("states", [])}
    for k, v in props.items():
        if k not in spec:
            return f"{n}: no property {k}"
        s = spec[k]
        if s["type"] == "bool":
            if v not in ("true", "false"):
                return f"{n}: bad bool {k}={v}"
        elif v not in s.get("values", []):
            return f"{n}: bad value {k}={v} (allowed {s.get('values')})"
    return None


def check_palette(states):
    errs = {}
    for s in states:
        e = check_state(s)
        if e:
            errs[s] = e
    return errs
