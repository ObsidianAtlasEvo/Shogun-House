# Sakura Shogun Estate

A one-run automated Minecraft (Java 26.1) build of a romantic late-samurai estate,
centred on `408.5 69 -230.5` by default.

* **To build it:** see [`SAKURA_SHOGUN_ESTATE/README_FIRST.txt`](SAKURA_SHOGUN_ESTATE/README_FIRST.txt),
  then run `SAKURA_SHOGUN_ESTATE/BUILD_SAKURA_ESTATE.bat`. The centre is set once, at the top of that file.
* **Already built the first release?** Run `SAKURA_SHOGUN_ESTATE/FIX_SAKURA_ESTATE.bat` (repair pass, ~2 minutes,
  only changed blocks).
* **Previews:** [`previews/`](previews) holds day and night renders of the model.
* **Generator:** [`generator/`](generator) is the Python that designs the estate as a voxel model
  (curved roofs, hand-shaped cherry trees, water, lighting) and compiles it into
  `SAKURA_SHOGUN_ESTATE/commands/sakura_estate_full.txt`.

```
pip install numpy pillow
python3 generator/estate.py        # rebuild command file + previews
python3 generator/audit.py         # walk-through audit (steps, jumps, chests, workstations)
python3 generator/verify.py        # replays both command files, block-for-block check
```

Build-time checks: every block state is validated against the 26.1 block registry
(`generator/data/blocks_26.1.json`, from PrismarineJS minecraft-data), water must be fully
contained (only the waterfall may flow), every plant/lantern/candle must have valid support,
every spawnable cell is lit (block light >= 1), each command fits Minecraft's 256-char chat limit, and the
usability audit must come back clean. The repair file is the exact difference between the first release
(`generator/data/estate_v1_as_built.*`) and the current model.
