"""Walkability checks between the key rooms of the estate."""
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import estate
from finalize import finalize
from world import parse, is_air, is_solid, is_plant
from collections import deque
w,t=estate.build(); finalize(w)
def passable(s):
    n,p=parse(s)
    if is_air(s) or is_plant(s): return True
    if n.endswith('_trapdoor') : return True
    if n.endswith('_carpet') or n.endswith('candle') or n in('lantern','iron_chain','pink_petals'): return True
    return False
def standable(s):
    n,p=parse(s)
    return is_solid(s) or n.endswith('_stairs') or n.endswith('_slab') or n=='water'
def walk(start, goal, maxn=400000):
    q=deque([start]); seen={start}
    while q:
        x,y,z=q.popleft()
        if (x,y,z)==goal: return True
        for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
            for dy in (0,1,-1,-2):
                nx,ny,nz=x+dx,y+dy,z+dz
                if (nx,ny,nz) in seen: continue
                if passable(w.get(nx,ny,nz)) and passable(w.get(nx,ny+1,nz)) and standable(w.get(nx,ny-1,nz)):
                    if dy==1 and not passable(w.get(x,y+2,z)): continue
                    seen.add((nx,ny,nz)); q.append((nx,ny,nz))
        if len(seen)>maxn: return None
    return False
pts={k:v for k,v in [a.split('=') for a in sys.argv[1:]]}
tests=[((-23,4,-28),(-33,-8,-25),'study->vault'),((-33,-8,-25),(-38,-17,-1),'vault->portal'),
       ((0,1,100),(0,4,-5),'approach->hall'),((0,4,-5),(-4,4,-44),'hall->island'),((0,4,-5),(49,7,-52),'hall->shrine'),
       ((0,4,-5),(45,2,34),'hall->tea'),((0,4,-5),(-36,3,30),'hall->dojo'),((0,4,-5),(-55,2,-28),'hall->bath'),
       ((0,4,-5),(4,12,-10),'hall->upstairs'),((0,4,-5),(53,2,-35),'hall->kura')]
for a,b,name in tests:
    print(name, walk(a,b))
