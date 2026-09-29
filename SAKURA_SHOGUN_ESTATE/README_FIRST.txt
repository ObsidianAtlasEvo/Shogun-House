SAKURA SHOGUN ESTATE - one-run automated build
Minecraft Java 26.1.x   |   default centre 408.5 69 -230.5
===============================================================================

WHAT YOU GET
------------
A romantic late-samurai estate on the footprint of the old build, composed for
dusk and designed from the arrival sequence inward:

  entry grove -> bending stone path -> vermilion drum bridge over a stream ->
  lantern avenue under a cherry tunnel, between rice paddies -> red torii ->
  modest roofed gate -> forecourt with raked gravel, pines and a stream bridge ->
  the Great Hall reveal: karahafu porch, deep skirt roof, upper storey,
  chidori gable and a curved irimoya roof -> the Moon Garden behind it: a large
  pond, a curved bridge to an ancient lantern-hung cherry on its island, a narrow
  waterfall, bamboo and a moon pavilion.

  * 34 hand-shaped cherry trees (ancient, leaning, weeping, spreading, tunnel,
    boundary grove), 5 cloud-pruned pines, bamboo groves, clipped azaleas
  * Curved roofs everywhere: every roof is generated with a concave pitch,
    upturned corners, irimoya gables with plaster faces, bargeboards and gold
    crests, ridge caps with end ornaments
  * Water everywhere, quietly: Moon pond, koi pond, a stream through the
    forecourt into a private garden pond, the approach stream, flooded paddies,
    a hot spring with hidden campfire glow, a hinoki tub, a waterfall
  * Lighting built for night: eave lanterns on every veranda, stone lanterns
    on the paths, lantern-hung and inner-glowing cherry canopies, glowing shoji,
    submerged glow lichen and sea pickles in the ponds, firefly bushes along the
    water, hidden up-lights at the feature trees - and a solver that placed
    invisible light blocks in every remaining dark spot, so NO hostile mob can
    spawn anywhere in the estate while it still feels like soft pools of light.
  * Every chest, barrel and storage block is EMPTY. (Only decor: armour on
    stands, weapons in the dojo's item frames, empty glow frames for maps.)

ALREADY BUILT IT?  RUN THE REPAIR PASS (v2)
-------------------------------------------
If you built the estate with the first release, do NOT rebuild. Double-click
FIX_SAKURA_ESTATE.bat, type REPAIR, and hands off for about 2-3 minutes.
It places only the 860 blocks that change (271 commands), with game ticks
frozen so nothing flows or pops while it works. Use the same CENTER you built with.

What the repair fixes (found by a walk-through audit of the whole estate):
  * Great Hall entrance: the porch steps were sunk into the ground. They are
    now a proper 3-step flight from the forecourt up to the porch floor.
  * Vault and shrine cavern: the last two steps of each stair had been carved
    away, leaving a 2-block ledge you could drop down but never climb back up.
  * Great Hall and kura interior staircases ended one block short of the
    upper floor; both now land level with it.
  * All three arched bridges (Moon, forecourt, arrival): their end steps were
    sunk. Decks are now a smooth half-block-per-step arch, flush at both ends.
  * Shrine terrace: its bottom step was buried in the ground.
  * Every building could only be entered by jumping (veranda lips, the 2-block
    manor podium, dojo / archery hall / pavilion plinths, gate thresholds).
    Added stair flights at the podium edges, shoe-stones in front of the
    verandas, and steps at every door, corridor and threshold, plus a
    stepping-stone path to the Moon Pavilion.
  * Kura storehouse: 10 chests had barrels on top and could never be opened.
    They are now barrels (usable).
  * Forge: anvils, furnaces and tables were set half into the floor. The
    floor now sits under them.
  * Cherry branches no longer cut through roofs, gables or torii (99 blocks
    restored on the shrine, pavilion, tea house and West Wing roofs).
  * The white block floating under the porch beam is now a timber strut.

Everything else in your world is left exactly as it is.

HOW TO BUILD FROM SCRATCH (one run, everything)
-----------------------------------------------
1. Back up your world if you can. The build CLEARS the old estate:
   141 x 181 blocks around the centre, from 24 blocks below it to 44 above.
2. Optional: open BUILD_SAKURA_ESTATE.bat in Notepad to change CENTER, SPEED,
   END_GAMEMODE, SUNSET or CHAT_KEY. The centre lives in that one place only.
3. Join the world/server as an operator (permission level 3+ for /tick).
4. Close all menus so you are looking at the world.
5. Double-click BUILD_SAKURA_ESTATE.bat and type SAKURA.
6. Hands off. It moves you above the site in spectator mode, force-loads the
   area and freezes game ticks (so water, sand and leaves stay put while the
   estate is assembled), then builds, unfreezes, and drops you under the main
   gate at golden hour.

   Time: about 52 min on NORMAL, 35 on FAST, 110 on SAFE.
   12,779 commands (already includes every repair above). Works in
   single-player or on a server (operators are not affected by the chat
   spam limit).

If you need your PC mid-build, just click away: the runner PAUSES by itself
and resumes when you click back into Minecraft. If you close it, progress is
saved - run the .bat again and answer Y to resume. If you stop and do NOT resume
straight away, type /tick unfreeze in Minecraft (the runner prints the exact
commands to restore normal play).

ESTATE TOUR (block coordinates for the default centre)
------------------------------------------------------
  Place                                                          X    Y      Z
  Arrival - start of the stone path (entry grove)              377   70   -127
  Vermilion drum bridge over the stream                        408   72   -141
  Lantern avenue and cherry tunnel                             408   70   -152
  Torii threshold                                              408   70   -159
  Main gate (yakuimon)                                         408   70   -170
  Stone arch bridge over the forecourt stream                  408   71   -194
  Karahafu entrance porch of the Great Hall                    408   73   -225
  Great Hall audience chamber (raised dais, tokonoma)          408   73   -241
  Upper storey - lord's moon-viewing room (ender chest)        408   81   -242
  Moon bridge to the ancient cherry island                     402   73   -264
  Ancient cherry tree island                                   404   72   -275
  Waterfall                                                    415   70   -283
  Moon pavilion (azumaya)                                      353   72   -284
  West Wing - bedrooms (beds)                                  372   73   -260
  West Wing - study (hidden trapdoor stair in the floor)       384   73   -259
  Ancestral vault (family armour, archive, storage)            375   61   -258
  Shrine cavern and hidden Nether portal                       370   52   -234
  Tsukimidai moon-viewing deck                                 378   73   -270
  Bath house (hinoki tub) and hot spring                       353   71   -259
  East Wing - scholar's library (enchanting, 15 shelves)       434   73   -233
  East Wing - strategy room (map wall, cartography)            443   73   -236
  East Wing - herbalist (brewing)                              443   73   -225
  Kitchen (smokers, furnaces, irori hearth)                    460   71   -235
  Swordsmith forge (blast furnaces, anvils, smithing)          460   71   -251
  Kura storehouse (empty chests & barrels, 2 floors)           461   71   -267
  Stable and service gate                                      463   70   -219
  Senbon torii tunnel to the shrine                            448   70   -256
  Shrine (honden, bell, lanterns)                              457   76   -280
  Tea house over the koi pond                                  453   71   -195
  Dojo (armour, weapon wall, master's platform)                372   72   -200
  Archery range (kyudojo)                                      352   72   -179
  Nagaya - retainers' rooms (villager workstations & beds)     385   71   -172
  Rice paddies (farms)                                         384   69   -156

SURVIVAL FUNCTIONS, HIDDEN IN BELIEVABLE PLACES
------------------------------------------------
  Beds ............... West Wing bedrooms, nagaya rooms
  Storage ............ Kura storehouse (two floors), vault, dojo, kitchen (all empty)
  Enchanting ......... East Wing library (table + exactly 15 bookshelves)
  Brewing ............ East Wing herbalist room
  Map wall ........... East Wing strategy room (10 empty glow frames + cartography)
  Cooking ............ Kitchen: smokers, furnaces, water cauldron
  Smithing ........... Forge: blast furnaces, furnaces, anvils, grindstone,
                       smithing table, stonecutter, fletching table, lava hearth
  Armour ............. Dojo armoury + ancestral vault
  Ender chests ....... Upper storey of the Great Hall, vault
  Nether portal ...... Shrine cavern beneath the vault (portal is pre-lit)
  Farms .............. Rice paddies (wheat) either side of the lantern avenue
  Bees ............... Beehives hung on the orchard/shrine cherry trees (add bees)
  Fishing / koi ...... Koi pond and Moon pond (10 koi)
  Bamboo, sugar cane . Bamboo groves; sugar cane at the Moon pond margins
  Horses ............. Stable with four stalls, hay and water, east service gate
  Villagers .......... Nagaya: four rooms with lectern, composter, barrel, brewing stand

THE HIDDEN VAULT
----------------
In the West Wing study, three trapdoors in the floor (by the east wall) open onto
a stone stair down to the ancestral vault. From its south-west corner a second
stair descends to a candle-lit cavern where a red torii frames the Nether portal.

REGENERATING / MOVING THE ESTATE
--------------------------------
The whole estate is produced by the Python generator in /generator of the
repository (python3 generator/estate.py). It builds a voxel model, checks it
(every block state against the 26.1 registry, water containment, support for
every plant/lantern/candle, spawn-proofing, and a walk-through audit: no buried
steps, no chest you can't open, no workstation set into a floor, and every room
reachable from the gate without jumping), and compiles the
command file. Previews are in /previews.
