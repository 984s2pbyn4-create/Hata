"""Validate static geometry, model completeness, and interactive-feature tagging.
Run from any directory: python source/validate_interactions.py
"""
from pathlib import Path
import hashlib, json, itertools, sys
import trimesh, numpy as np
root=Path(__file__).resolve().parents[1]
geo=json.loads((root/'source/geometry.json').read_text(encoding='utf-8'))
by_id={w['id']:w for w in geo['walls']}
assert any(h['type']=='door' for h in by_id['w_closet_n']['holes']), 'Corridor entry missing'
assert any(h['type']=='door' for h in by_id['w_l_e']['holes'] if h['a']>=990), 'Bedroom entry missing'
scenarios=list(itertools.product(('warm','japandi','graphite'),('now','two','school'),('daily','guest','dinner')))
all_sig=set(); result=[]
for style,age,mode in scenarios:
 path=root/'models'/f'kvartira-{style}-{age}-{mode}.glb'
 assert path.is_file(),f'Missing: {path}'
 scene=trimesh.load(path,force='scene')
 nodes=list(scene.graph.nodes_geometry)
 features={f:sum(f in n for n in nodes) for f in ('feature_peninsula','feature_laptop','feature_screen','feature_wardrobe')}
 assert all(features.values()),f'Interactive feature missing in {path.name}: {features}'
 bed=any('unfolded_guest_bed' in n for n in nodes)
 assert bed==(mode=='guest'),f'Guest bed incorrect: {path.name}'
 walls=[]
 for node in nodes:
  if not node.startswith('wall_'):continue
  xform,mesh_id=scene.graph[node]
  mesh=scene.geometry[mesh_id]
  vv=np.round(trimesh.transform_points(mesh.vertices,xform),5)
  walls.append((node,vv.tobytes(),mesh.faces.tobytes()))
 digest=hashlib.sha256(b''.join(k.encode()+v+f for k,v,f in sorted(walls))).hexdigest()
 all_sig.add(digest)
 result.append({'file':path.name,'nodes':len(nodes),'walls':len(walls),'geometry_sha256':digest,'movable':features})
assert len(all_sig)==1,'Structural wall geometry differs across variants!'
shell=root/'models/kvartira-planirovka.glb';assert shell.is_file()
html=(root/'tour.html').read_text()
js=(root/'tour.js').read_text()
for key in ('sofaAction','cinemaScene','guidedTour','data-mechanism="peninsula"','data-mechanism="laptop"','data-mechanism="screen"','data-mechanism="wardrobe"','data-stage="two"'):
 assert key in html, f'Missing interactive control {key}'
for key in ('animatedPoint','animatedPos','uMechanisms','setSofaState'):
 assert key in js, f'Missing logic {key}'
(root/'data/model_validation_v6.json').write_text(json.dumps({'model_count':len(scenarios),'all_structural_digests_equal':True,'structural_digest':next(iter(all_sig)),'checked_models':result},ensure_ascii=False,indent=2))
print('PASSED:',len(scenarios),'GLB configurations, 4 movable node groups each, both wardrobe entries, 1 shared wall digest')
