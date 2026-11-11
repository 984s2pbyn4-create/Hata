"""DARK TECH FAMILY • executable 3D scene generator.
Structural geometry from source/geometry.json incl. two existing wardrobe entries.
Furniture is conceptual, not surveyed or construction-ready.
"""
from pathlib import Path
import json, math
import numpy as np, trimesh
from shapely.geometry import Polygon
from shapely.ops import triangulate
from trimesh.transformations import rotation_matrix
ROOT=Path(__file__).resolve().parents[1]; SCALE=100.5
G=json.loads((ROOT/'source/geometry.json').read_text())
H=G['wall_height_m']; OUT=ROOT/'models';OUT.mkdir(exist_ok=True)
STYLES={
 'warm':dict(floor='#866953',wall='#cec9c2',tile='#73767a',wood='#644731',woodDark='#382b27',fabric='#857b73',soft='#b9a99a',accent='#d3ac77',metal='#b38b53',cabinet='#33373c',white='#e6dfd5',black='#151a20',green='#57725d',glass='#789da9',rug='#a89b8b',kids='#79949b'),
 'japandi':dict(floor='#8d735d',wall='#d6d0c5',tile='#777a76',wood='#6f513e',woodDark='#413a30',fabric='#7d8979',soft='#c3bfaf',accent='#a0ac79',metal='#9d907d',cabinet='#4a5148',white='#ebe7df',black='#1c2221',green='#668666',glass='#86a7a3',rug='#b2ac9d',kids='#9badab'),
 'graphite':dict(floor='#735747',wall='#c5c4c1',tile='#696e71',wood='#6a4632',woodDark='#2e2727',fabric='#57595e',soft='#9b9591',accent='#c2a16d',metal='#bd9a63',cabinet='#292c31',white='#e4ddd4',black='#121519',green='#4b6956',glass='#7095a2',rug='#92867c',kids='#6c8299')
}

def rgba(h):return np.array([int(h[i:i+2],16) for i in (1,3,5)]+[255],dtype=np.uint8)
def shell(floor_color,wall_color,tile_color):
 sc=trimesh.Scene()
 def add(mesh,name,col):
  mesh.visual.vertex_colors=np.tile(rgba(col),(len(mesh.vertices),1))
  sc.add_geometry(mesh,node_name=name)
 def flat(points):
  poly=Polygon([(x/SCALE,z/SCALE) for x,z in points]);vs=[];fs=[]
  for tr in triangulate(poly):
   if not poly.covers(tr.representative_point()):continue
   pts=list(tr.exterior.coords)[:3]
   for y in (0.015,-.05):
    ids=[]
    for x,z in pts:ids.append(len(vs));vs.append([x,y,z])
    fs.append(ids if y>0 else ids[::-1])
  for a,b in zip(list(poly.exterior.coords)[:-1],list(poly.exterior.coords)[1:]):
   (x,z),(u,v)=a,b;i=len(vs);vs.extend([[x,.015,z],[u,.015,v],[u,-.05,v],[x,-.05,z]]);fs.extend([[i,i+1,i+2],[i,i+2,i+3]])
  return trimesh.Trimesh(vertices=vs,faces=fs,process=False)
 for room in G['rooms']:
  col=tile_color if room['id'] in ('bath','wc','hall','closet','balcony') else floor_color
  add(flat(room['polygon']),f'floor_{room["id"]}',col)
 for wall in G['walls']:
  x1,z1=wall['a'];x2,z2=wall['b'];hor=abs(z1-z2)<3;axis=0 if hor else 1
  start,end=sorted([wall['a'][axis],wall['b'][axis]])
  typ=wall['type'];height=1.04 if typ=='rail' else 0.95 if typ=='parapet' else H
  thick=.235 if typ=='exterior' else .17 if typ=='parapet' else .055 if typ=='rail' else .116
  def segment(a,b,h=height,y=0,col=wall_color,th=thick):
   if b-a <.05 or h<.01:return
   cx=(a+b)/2 if hor else x1;cz=z1 if hor else (a+b)/2
   ext=((b-a)/SCALE,h,th)
   mesh=trimesh.creation.box(extents=ext)
   if not hor:mesh.apply_transform(rotation_matrix(-math.pi/2,(0,1,0)))
   mesh.apply_translation((cx/SCALE,y+h/2,cz/SCALE))
   add(mesh,f'wall_{wall["id"]}_{a:.0f}_{b:.0f}_{y:.1f}',col)
  cursor=start
  for hole in sorted(wall.get('holes',[]),key=lambda h:h['a']):
   a=max(start,hole['a']);b=min(end,hole['b'])
   if a>cursor:segment(cursor,a)
   if hole['type']=='window':
    segment(a,b,.79);segment(a,b,height-2.12,2.12)
    segment(a,b,1.30,.79,'#7FA0B3',.028)
   else:
    segment(a,b,height-2.15,2.15)
    if hole['type']=='balcony':segment(a,b,2.04,0,'#7FA0B3',.026)
   cursor=max(cursor,b)
  if cursor<end:segment(cursor,end)
 return sc

def add_furniture(sc,m,stage='now',scenario='daily'):
 count=[0]
 def add(mesh,k,label):
  col=m[k] if k in m else k
  mesh.visual.vertex_colors=np.tile(rgba(col),(len(mesh.vertices),1));count[0]+=1
  sc.add_geometry(mesh,node_name=f'custom_{k}_{label}_{count[0]:04d}')
 def B(x,z,w,d,h,k,y=0,label='box'):
  o=trimesh.creation.box(extents=(w,h,d));o.apply_translation((x/SCALE,y+h/2,z/SCALE));add(o,k,label)
 def R(x,z,w,d,h,k,y=0,label='rounded'):
  o=trimesh.creation.icosphere(subdivisions=1,radius=1);o.apply_scale((w/2,h/2,d/2));o.apply_translation((x/SCALE,y+h/2,z/SCALE));add(o,k,label)
 def C(x,z,r,h,k,y=0,label='cylinder',segments=16):
  o=trimesh.creation.cylinder(radius=r,height=h,sections=segments);o.apply_transform(rotation_matrix(math.pi/2,(1,0,0)));o.apply_translation((x/SCALE,y+h/2,z/SCALE));add(o,k,label)
 def plant(x,z,s=.65):
  C(x,z,.16*s,.28*s,'wood',.02,'planter')
  C(x,z,.02*s,.44*s,'woodDark',.24*s,'stem',8)
  for j in range(7):
   a=j*2.38;rr=.13*s;o=trimesh.creation.icosphere(subdivisions=1,radius=1);o.apply_scale([.125*s,.05*s,.07*s]);o.apply_transform(rotation_matrix(a,(0,1,0)))
   o.apply_translation(((x+rr*SCALE*math.cos(a))/SCALE,.5*s+.06*(j%3),(z+rr*SCALE*math.sin(a))/SCALE));add(o,'green','leaf')
 # KITCHEN/LIVING ~15.4 m²: linear cabinetry against south wall, clear door on east at z540..625.
 B(405,747,4.03,.58,.87,'cabinet',0.02,'kitchen_lower')
 B(405,746,4.08,.63,.05,'white',.9,'kitchen_worktop')
 for k in range(5):
  xx=245+76*k;B(xx,774,.72,.28,.56,'woodDark',1.53,'upper_cabinet')
  B(xx,758,.70,.011,.011,'accent',1.57,'under_cabinet_led')
 B(338,744,.65,.4,.015,'black',.956,'electric_hob')
 for xx in (317,350):
  for zz in (730,753):C(xx,zz,.055,.012,'metal',.974,'hob_ring',16)
 B(526,741,.58,.41,.035,'metal',.95,'sink');C(534,749,.025,.30,'metal',1.0,'tap',12)
 B(593,740,.55,.63,1.94,'cabinet',0,'fridge')
 B(253,743,.48,.024,.54,'black',.21,'oven_door')
 B(255,741,.43,.012,.37,'glass',.27,'oven_window')
 # Couch along west, TV at east wall on solid panel below door. Daily vs guest layout.
 B(226,616,.60,1.67,.62,'fabric',.08,'sofa_base')
 B(205,615,.18,1.68,.74,'fabric',.10,'sofa_back')
 for zz in (557,614,671):R(231,zz,.59,.50,.11,'soft',.52,'sofa_seat')
 for zz in (561,615,668):R(211,zz,.17,.43,.37,'soft',.52,'sofa_cushion')
 if scenario=='guest':
  B(317,616,1.22,1.68,.31,'fabric',.11,'unfolded_guest_bed')
  B(319,617,1.16,1.57,.08,'soft',.40,'guest_mattress')
 else:
  for zz in (557,666):R(239,zz,.23,.23,.20,'accent',.59,'cushion')
 # expandible table set in spare north half, dedicated bench seats in guest mode
 if scenario=='dinner':
  B(403,567,1.56,.86,.065,'wood',.72,'dinner_table_six')
  for xx in (332,473):
   for zz in (524,610):B(xx,zz,.42,.40,.45,'fabric',.03,'chair')
 else:
  B(420 if scenario=='daily' else 465,515,1.12 if scenario=='daily' else .82,.74 if scenario=='daily' else .53,.055,'wood',.73,'folding_table')
  if scenario=='daily':
   for xx in (372,470):B(xx,465,.40,.39,.44,'fabric',.03,'chair')
 # TV + soundbar on east solid panel below entry gap (z roughly 630..780)
 B(627,692,.055,1.30,.75,'black',1.03,'main_tv')
 B(621,694,.10,1.10,.055,'metal',.94,'soundbar')
 # The projection screen is stored near the ceiling and rolls down over the TV.
 B(611,693,.08,1.54,.09,'metal',2.16,'ceiling_projector_cassette')
 B(611,693,.025,1.48,1.18,'white',.96,'feature_screen_fabric')
 B(610,693,.06,1.51,.025,'metal',.95,'feature_screen_bottom_rail')
 B(617,690,.22,.65,.24,'woodDark',.11,'floating_media')
 # Hidden laptop workspace above dining: not for soldering, unfurls under supervision
 # Closed, pull-out peninsula works below the existing countertop, not a permanent island.
 # The in-browser viewer translates the feature meshes by -0.68m toward the room.
 B(487,736,.88,.97,.055,'wood',.815,'feature_peninsula_top')
 B(509,736,.075,.84,.57,'metal',.225,'feature_peninsula_support')
 B(477,737,.73,.18,.075,'woodDark',.76,'feature_peninsula_apron')
 # Laptop flap is vertical while closed and rotates 90 degrees to form a 0.48m desk.
 # Its pivot is at x=5.43, y=.76m, z=4.78m in apartment coordinates.
 B(543,478,.77,.033,.48,'wood',.76,'feature_laptop_flap')
 B(543,455,.80,.045,.81,'cabinet',.96,'storage_work_niche')
 B(543,476,.81,.08,.045,'metal',.735,'workbench_hinge')
 plant(289,470,.55)
 # PARENTS 13.8m² lower-left. Bed 180x200, TV65, vanity, a temporary crib.
 B(400,1005,2.08,2.20,.018,'rug',.02,'bedroom_rug')
 B(396,1000,1.80,2.00,.25,'woodDark',.16,'king_bed_frame')
 B(396,1001,1.76,1.95,.23,'white',.38,'king_mattress')
 B(395,1066,1.70,.64,.10,'fabric',.62,'duvet')
 B(395,1112,2.05,.12,.99,'wood',.18,'headboard')
 for xx in (351,436):R(xx,932,.56,.35,.13,'soft',.64,'bed_pillow')
 for xx in (280,512):B(xx,1070,.33,.41,.52,'woodDark',.05,'bedside')
 B(396,803,1.46,.045,.85,'black',1.05,'bedroom_TV_65')
 B(532,855,.72,.38,.75,'wood',.02,'makeup_vanity')
 B(532,844,.64,.03,.65,'glass',.88,'makeup_mirror')
 B(534,905,.43,.39,.46,'fabric',.01,'makeup_stool')
 B(233,971,.63,1.07,.30,'wood',.13,'temporary_cot_frame')
 B(233,974,.57,1.00,.09,'white',.43,'temporary_cot_mattress')
 for zz in (932,1006):B(206,zz,.025,.11,.50,'woodDark',.20,'cot_rail')
 B(254,843,.42,.53,.16,'soft',.03,'dog_bed_1')
 B(550,1044,.42,.53,.16,'soft',.03,'dog_bed_2')
 # WALK-THROUGH CLOSET: avoid both entrance arcs. Shelves on east and south boundaries only.
 B(734,1053,.18,.90,2.20,'woodDark',0,'closet_east_storage')
 B(694,1111,.46,.18,1.75,'wood',0,'closet_south_storage')
 # Sliding furniture front (not an entrance door): leaves both existing entrances untouched.
 B(720,1050,.045,.75,1.80,'woodDark',.12,'feature_wardrobe_sliding_front')
 for level in (.38,.83,1.28):B(735,1050,.23,.74,.036,'accent',level,'closet_shelf')
 # CHILD ROOM 12.2m² upper-centre. No tall beds at toddler stage.
 if stage=='now':
  B(490,298,.75,1.53,.31,'kids',.12,'low_child_bed')
  B(489,303,.68,1.46,.09,'white',.45,'child_mattress')
  B(593,234,1.65,1.60,.013,'rug',.02,'play_mat')
  for j,(xx,zz) in enumerate(((585,205),(635,273),(606,297))):C(xx,zz,.14,.045,'accent',.02,f'toy_{j}')
 elif stage=='two':
  # Both beds low while the children are small. No upper bunks at this stage.
  for xx in (490,606):
   B(xx,255,.74,1.53,.22,'wood',.07,'second_stage_low_bed')
   B(xx,256,.70,1.48,.10,'white',.31,'second_stage_mattress')
  B(550,350,1.08,.60,.012,'rug',.02,'shared_play_zone')
 else:
  # Two raised sleeping positions planned for later school years; clear headroom must be measured.
  B(493,225,.92,2.0, .23,'wood',1.48,'loft_bed_upper')
  B(492,226,.83,1.92,.11,'white',1.71,'loft_mattress')
  B(492,224,.98,.09,.52,'woodDark',1.77,'loft_guard')
  B(606,224,.92,2.0,.24,'wood',.27,'second_bed_low')
  B(605,225,.83,1.92,.11,'white',.5,'second_mattress')
  for xx in (492,605):B(xx,351,.96,.46,.08,'woodDark',.71,'study_desk')
  for xx in (493,605):B(xx,375,.43,.40,.44,'kids',.05,'study_chair')
 B(717,337,.35,1.13,1.68,'cabinet',.01,'child_storage')
 plant(727,126,.5)
 # HALL / bath & WC
 B(750,709,.23,1.02,1.9,'cabinet',.03,'hall_coats')
 B(737,927,.60,.31,.47,'woodDark',.02,'hall_shoes')
 B(862,498,1.50,.73,.49,'white',.04,'bathtub')
 B(865,499,1.37,.57,.035,'tile',.54,'bathtub_recess')
 B(927,593,.55,.47,.78,'wood',.02,'bath_vanity')
 C(927,593,.18,.06,'white',.82,'washbasin')
 C(868,719,.20,.39,'white',.02,'toilet_bowl')
 B(873,740,.38,.44,.13,'white',.37,'toilet_tank')
 # washer in bathroom, not obstructing bath access in schematic
 B(812,592,.54,.55,.84,'white',.02,'washing_machine')
 C(812,592,.16,.014,'glass',.86,'washing_door')
 # LODGIA: FDM case + hydroponic plant rack; photopolymer deliberately EXCLUDED pending extraction.
 B(238,332,.62,.52,1.25,'cabinet',.03,'sealed_FDM_3d_printer_cabinet')
 B(238,332,.47,.38,.55,'glass',.51,'FDM_case_view')
 B(350,330,.45,.34,1.80,'metal',.02,'hydroponics_rack')
 for lev in (.38,.75,1.15,1.52):
  B(350,330,.50,.35,.058,'white',lev,'plant_tray')
  for dx in (-14,0,14):R(350+dx,330,.13,.14,.18,'green',lev+.075,'herbs')
 # linear LEDs along kitchen, headboard and study, avoid inventing structural ceiling positions
 B(406,770,3.7,.017,.015,'accent',1.51,'kitchen_LED')
 B(393,1105,1.85,.017,.014,'accent',1.01,'headboard_LED')
 return sc

def gen():
 for stage in ('now','two','school'):
  for style,m in STYLES.items():
   for scenario in ('daily','guest','dinner'):
    sc=shell(m['floor'],m['wall'],m['tile']);add_furniture(sc,m,stage,scenario)
    p=OUT/f'kvartira-{style}-{stage}-{scenario}.glb';sc.export(p)
    print('GLB',p.name,len(sc.graph.nodes_geometry),round(p.stat().st_size/1024),'KB')
 # bare shell one model
 sc=shell(STYLES['warm']['floor'],STYLES['warm']['wall'],STYLES['warm']['tile'])
 sc.export(OUT/'kvartira-planirovka.glb')

if __name__=='__main__':gen()
