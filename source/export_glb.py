"""Create genuine glTF binary meshes using the exact wall and floor JSON used by the browser."""
import json, math, os
import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import triangulate
root='/mnt/data/apartment3d'
g=json.load(open(root+'/data/geometry.json'))
s=g['calibration']['pixels_per_meter']
colors={'exterior':'#e9e4d8','interior':'#f4f0e7','rail':'#9dbabd','parapet':'#e8e3d8','glass':'#8eb9d3'}
def rgb(h,alpha=255):return np.array([int(h[i:i+2],16) for i in (1,3,5)]+[alpha],dtype=np.uint8)
def floor_mesh(points):
    poly=Polygon([(x/s,z/s) for x,z in points]); vs=[];fs=[]
    def emit_tri(tri,y,up):
        pts=np.array(tri,dtype=float)
        a=np.array([pts[0,0],y,pts[0,1]]);b=np.array([pts[1,0],y,pts[1,1]]);c=np.array([pts[2,0],y,pts[2,1]])
        if (np.cross(b-a,c-a)[1]>0)!=up: b,c=c,b
        n=len(vs);vs.extend([a,b,c]);fs.append([n,n+1,n+2])
    for tri in triangulate(poly):
        if not poly.covers(tri.representative_point()):continue
        coords=list(tri.exterior.coords)[:3]; emit_tri(coords,0.02,True);emit_tri(coords,-.055,False)
    pts=list(poly.exterior.coords)[:-1]
    for i,(x,z) in enumerate(pts):
        nx,nz=pts[(i+1)%len(pts)];n=len(vs)
        vs.extend([(x,.02,z),(nx,.02,nz),(nx,-.055,nz),(x,-.055,z)])
        fs.extend([[n,n+1,n+2],[n,n+2,n+3]])
    return trimesh.Trimesh(vertices=vs,faces=fs,process=False)
def boxmesh(center,extents,color,angle=0):
    mesh=trimesh.creation.box(extents=extents)
    if angle:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(angle,(0,1,0)))
    mesh.apply_translation(center);mesh.visual.vertex_colors=np.tile(rgb(color), (len(mesh.vertices),1));return mesh

def new_scene(furnished=False):
 scene=trimesh.Scene()
 counter=[0]
 def add(mesh,name):
  counter[0]+=1;scene.add_geometry(mesh,node_name=f'{name}_{counter[0]:03d}')
 def B(x,z,w,d,h,col,y=0):add(boxmesh((x/s,y+h/2,z/s),(w,h,d),col),'furniture')
 for room in g['rooms']:
  mesh=floor_mesh(room['polygon']);mesh.visual.vertex_colors=np.tile(rgb(room['color']), (len(mesh.vertices),1));add(mesh,room['id'])
 for wall in g['walls']:
  x1,z1=wall['a'];x2,z2=wall['b']; horizontal=z1==z2
  # The inputs are axis aligned and increase along their varying coordinate.
  start=x1 if horizontal else z1;end=x2 if horizontal else z2
  typ=wall['type'];height=1.07 if typ=='rail' else .9 if typ=='parapet' else g['wall_height_m']
  thick=.245 if typ=='exterior' else .052 if typ=='rail' else .17 if typ=='parapet' else .116
  def segment(a,b,h=height,y=0,col=None,thickness=thick):
   if b-a<0.1 or h<.01:return
   xm=(a+b)/2 if horizontal else x1;zm=z1 if horizontal else (a+b)/2
   angle=0 if horizontal else -math.pi/2
   add(boxmesh((xm/s,y+h/2,zm/s),((b-a)/s,h,thickness),col or colors[typ],angle),'wall_'+wall['id'])
  cursor=start
  for hole in sorted(wall.get('holes',[]),key=lambda h:h['a']):
   a=max(start,hole['a']);b=min(end,hole['b'])
   if a>cursor:segment(cursor,a)
   if hole['type']=='window':
    segment(a,b,.79,0);segment(a,b,height-2.12,2.12)
    segment(a,b,1.3,.79,'#86b8cf',.035)
   else:
    segment(a,b,height-2.15,2.15)
    if hole['type']=='balcony':segment(a,b,2.04,0,'#86b8cf',.032)
   cursor=max(cursor,b)
  if cursor<end:segment(cursor,end)
 if furnished:
  # The exported model has the same layout and a representative, simplified furniture set.
  B(585,239,1.66,2.03,.30,'#b99c79',.12); B(585,239,1.58,1.95,.24,'#e5dfd2',.38)
  B(585,128,1.72,.16,.87,'#928e87',.02); B(475,192,.57,1.64,2.13,'#b99c79',.01)
  B(408,740,3.76,.59,.86,'#e5dfd2',.01);B(408,740,3.82,.65,.04,'#303c3f',.87)
  B(422,563,1.38,.76,.08,'#b99c79',.74)
  for cx in (365,480):
   for cz in (545,583):B(cx,cz,.40,.42,.45,'#5d7767',.02)
  B(603,511,.53,.6,1.91,'#e5dfd2',.0)
  B(394,1020,2.18,.81,.62,'#b5b6a8',.12);B(394,1057,2.20,.18,.72,'#b5b6a8',.11)
  B(391,920,1.05,.56,.31,'#b99c79',.09)
  B(395,814,1.2,.045,.7,'#303c3f',.86)
  B(876,500,1.54,.70,.53,'#d9e4e2',.02);B(909,598,.48,.48,.84,'#e5dfd2',.02)
  B(873,718,.45,.66,.48,'#e5dfd2',.01)
  B(666,715,.3,.84,1.25,'#b99c79',.02);B(725,921,.8,.33,.44,'#a8a099',.02)
  B(638,1053,.28,1.12,2.10,'#b99c79',0);B(720,1044,.24,.95,2.10,'#e5dfd2',0)
 return scene
for furnished,name in ((False,'kvartira-planirovka.glb'),(True,'kvartira-interier.glb')):
 path=root+'/'+name;new_scene(furnished).export(path)
 print(path,os.path.getsize(path))
