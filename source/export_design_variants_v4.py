"""Detailed color-PBR-ready portable GLB furniture for the *same* measured shell.
All locations are in measurement-plan pixel coordinates, converted at 100.5 px/m.
Nonstructural furnishings and finishes are conceptual. No wall geometry modified.
"""
from pathlib import Path
import math, sys, json
import trimesh, numpy as np
from trimesh.transformations import rotation_matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from export_glb import new_scene, rgb
ROOT=Path(__file__).parent; SCALE=100.5
STYLES={
'warm':{'floor':'#bea37d','floorLine':'#b49a74','wall':'#eae6df','stone':'#d6cfc4','marble':'#eee9e1','rug':'#d9cabb','fabric':'#d3c4b1','white':'#faf5ed','wood':'#ab865e','woodDark':'#786249','accent':'#b3a38d','cabinet':'#e4dccd','metal':'#a68c63','black':'#303639','green':'#54775b','tile':'#c6c7be','glass':'#88adb6'},
'japandi':{'floor':'#af926b','floorLine':'#a78962','wall':'#e4e2d9','stone':'#c8cabd','marble':'#e4e1d6','rug':'#d7d5c9','fabric':'#aeb9a4','white':'#f3f0e7','wood':'#9c7852','woodDark':'#5f513f','accent':'#83957c','cabinet':'#bda98f','metal':'#666b5d','black':'#303c37','green':'#587458','tile':'#c4c8bd','glass':'#86a9a5'},
'graphite':{'floor':'#8d705b','floorLine':'#745b49','wall':'#dbd9d3','stone':'#bfbab1','marble':'#d9d5cf','rug':'#b5aaa0','fabric':'#a6a3a0','white':'#e6e2de','wood':'#775740','woodDark':'#4f3b31','accent':'#908775','cabinet':'#454b4e','metal':'#b19a73','black':'#1d2225','green':'#4d6b51','tile':'#bcb9b4','glass':'#7e9da8'}}

def export_style(style):
    M=STYLES[style];sc=new_scene(False);count=[0]
    # Style-aware floor colors and walls, structural positions untouched.
    for node in sc.graph.nodes_geometry:
        transform,key=sc.graph[node]
        mesh=sc.geometry[key]
        k=node.split('_')[0]
        col=M['tile'] if k in ('bath','wc','hall','closet','balcony') else M['floor'] if k in ('kitchen','bedroom','living') else None
        if col is None and node.startswith('wall_'):
            col=M['wall']
        if col:
            mesh.visual.vertex_colors=np.tile(rgb(col),(len(mesh.vertices),1))
    def add(mesh,mat,prefix):
        mesh.visual.vertex_colors=np.tile(rgb(M.get(mat,mat)),(len(mesh.vertices),1))
        count[0]+=1;sc.add_geometry(mesh,node_name=f'custom_{mat}_{prefix}_{count[0]:04d}')
    def B(x,z,w,d,h,mat,y=0):
        mesh=trimesh.creation.box(extents=(w,h,d));mesh.apply_translation((x/SCALE,y+h/2,z/SCALE));add(mesh,mat,'box')
    def C(x,z,r,h,mat,y=0,sections=24):
        mesh=trimesh.creation.cylinder(radius=r,height=h,sections=sections)
        mesh.apply_transform(rotation_matrix(math.pi/2,(1,0,0)))
        mesh.apply_translation((x/SCALE,y+h/2,z/SCALE));add(mesh,mat,'cyl')
    def S(x,z,r,mat,y=0):
        mesh=trimesh.creation.icosphere(subdivisions=1,radius=r)
        mesh.apply_translation((x/SCALE,y,z/SCALE));add(mesh,mat,'sphere')
    def R(x,z,w,d,h,mat,y=0,subdivisions=2):
        """A rounded, soft volume (ellipse/loft in true 3D, not a painted sprite)."""
        mesh=trimesh.creation.icosphere(subdivisions=subdivisions,radius=1)
        mesh.apply_scale([w/2,h/2,d/2])
        mesh.apply_translation((x/SCALE,y+h/2,z/SCALE))
        add(mesh,mat,'soft')
    def chair(x,z,towards=0):
        B(x,z,.47,.45,.095,'fabric',.43)
        B(x,z+towards*23,.46,.085,.44,'wood',.50)
        R(x,z,.43,.41,.090,'fabric',.49)
        R(x,z+towards*22,.43,.075,.37,'fabric',.55)
        for xx in (x-17,x+17):
            for zz in (z-16,z+16):C(xx,zz,.025,.43,'woodDark',.015,8)
    def plant(x,z,s=1):
        C(x,z,.16*s,.35*s,'stone',.01)
        C(x,z,.035*s,.45*s,'woodDark',.33*s,9)
        for i in range(12):
            angle=i*2.40;rr=(.07+.17*(i%3)) *s
            leaf=trimesh.creation.icosphere(subdivisions=1,radius=1)
            leaf.apply_scale([.13*s,.047*s,.065*s]);leaf.apply_transform(rotation_matrix(angle,(0,1,0)))
            leaf.apply_translation(((x+rr*SCALE*math.cos(angle))/SCALE,(.63+.12*(i%4))*s,(z+rr*SCALE*math.sin(angle))/SCALE))
            add(leaf,'green','leaf')
    def lamp(x,z,y=2.0):
        C(x,z,.14,.12,'metal',y-.14)
        C(x,z,.085,.025,'white',y-.16)
    def cupboard(x,z,w,d,h):
        B(x,z,w,d,h,'cabinet',.015)
    # Strips physically mark wood board pattern, while staying inside existing room floors.
    for x1,x2,z1,z2 in ((182,637,438,781),(182,606,800,1129),(438,756,36,421)):
        zz=z1+16
        while zz<z2-14:
            B((x1+x2)/2,zz,(x2-x1)/SCALE-.065,.012,.003,'floorLine',.025)
            zz+=22
    # Bedroom: bed, duvet, pillows, headboard, bedside and wardrobe.
    B(594,246,2.46,2.87,.018,'rug',.025)
    B(593,237,1.92,2.17,.20,'woodDark',.14)
    B(593,237,1.78,2.10,.29,'white',.34)
    B(593,263,1.74,1.34,.13,'fabric',.63)
    B(594,123,2.08,.17,1.07,'accent',.24)
    for x in (545,638):
        B(x,158,.64,.41,.13,'white',.66);B(x,149,.58,.14,.05,'fabric',.80)
    for x in (485,700):
        B(x,158,.44,.48,.52,'wood',.04);B(x,151,.44,.49,.05,'woodDark',.53)
        C(x,153,.10,.22,'white',.58); C(x,153,.065,.028,'metal',.80)
    cupboard(470,283,.42,1.42,2.25)
    for z in (242,294,346):B(491,z,.02,.016,1.75,'woodDark',.28)
    B(708,356,.62,.31,.42,'wood',.025);plant(708,400,.68)
    # Kitchen: full run along original south wall, backsplash and overhead cabinets.
    cupboard(411,749,4.05,.58,.85)
    B(412,747,4.13,.64,.056,'marble',.87)
    for i in range(6):
        xx=239+i*68;B(xx,720,.63,.03,.67,'cabinet' if i%2 else 'wood',.09)
        B(xx,711,.16,.012,.010,'metal',.65)
    B(413,779,4.12,.038,.56,'tile',.98)
    for i in range(5):cupboard(246+i*80,783,.74,.28,.57)
    B(338,734,.72,.41,.011,'black',.934)
    for xx,zz in ((320,722),(358,722),(320,748),(358,748)):C(xx,zz,.064,.009,'metal',.949)
    B(533,733,.56,.4,.012,'metal',.941)
    B(533,733,.47,.33,.023,'stone',.948)
    C(546,754,.024,.31,'metal',.956,10)
    cupboard(602,509,.57,.61,2.11)
    B(400,562,2.9,1.94,.016,'rug',.028)
    B(400,559,1.64,.84,.067,'marble',.76)
    for x in (339,461):
        for z in (498,613):chair(x,z,-1 if z<560 else 1)
    C(404,559,.09,.02,'metal',.83);S(404,558,.06,'green',.91)
    for x in (342,400,459):lamp(x,559,2.25)
    plant(584,470,.70)
    # Living room: sofa clearly faces TV, rug, coffee tables, ottoman and plants.
    B(398,942,2.9,2.0,.018,'rug',.025)
    B(399,1034,2.52,.89,.22,'woodDark',.16)
    B(399,1035,2.42,.80,.32,'fabric',.39)
    B(399,1072,2.42,.19,.55,'fabric',.33)
    for xx in (322,399,476):
        B(xx,1009,.70,.57,.14,'white',.65)
        B(xx,1059,.68,.125,.31,'fabric',.66)
    for xx in (269,528):B(xx,1028,.19,.82,.48,'fabric',.34)
    for xx in (319,472):B(xx,1064,.23,.19,.13,'accent',.87)
    C(393,925,.42,.08,'marble',.38,32);C(393,925,.32,.30,'woodDark',.08)
    C(456,921,.20,.045,'wood',.38);S(397,915,.07,'green',.52)
    B(399,814,2.1,.33,.43,'wood',.04)
    B(399,798,1.79,.045,1.20,'metal',.77)
    B(399,794,1.68,.067,1.07,'black',.84)
    cupboard(544,909,.70,.69,.39);B(543,940,.65,.12,.38,'fabric',.40)
    plant(545,1090,.86)
    B(216,858,.24,.59,1.3,'wood',.018)
    for i in range(4):B(216,838+18*i,.30,.04,.04,'marble',.28+i*.28)
    # bathroom: bathtub porcelain with interior insert, vanity and toilet
    B(871,501,1.59,.74,.51,'white',.04)
    B(871,501,1.42,.61,.02,'stone',.535)
    cupboard(924,586,.52,.53,.83)
    B(924,586,.55,.54,.071,'marble',.88)
    C(924,586,.19,.07,'white',.95)
    B(925,439,.59,.025,.66,'glass',1.09)
    C(872,710,.235,.46,'white',.035)
    B(872,736,.45,.53,.14,'white',.43)
    # Entrance, wardrobe and balcony (indicative)
    cupboard(663,681,.29,1.09,1.24)
    B(712,933,.82,.36,.43,'fabric',.02)
    B(706,944,1.0,.52,.022,'rug',.023)
    cupboard(637,1051,.25,1.21,2.22)
    cupboard(725,1051,.22,1.12,2.22)
    for i in range(4):B(678,1004+35*i,.74,.051,.045,'wood',.31+i*.44)
    C(359,329,.17,.45,'wood',.02)
    plant(359,328,.57)
    B(284,313,.58,.37,.39,'fabric',.03)
    # v4: soft furniture and finish details — strictly furniture/decor, never walls or windows.
    # Linen upholstery overlays, piping and throws, placed within existing furniture footprint.
    for xx in (322,399,476):
        R(xx,1009,.72,.58,.13,'fabric',.715)
        R(xx,1060,.65,.10,.28,'fabric',.72)
    for xx in (325,477):
        R(xx,1034,.37,.27,.24,'accent',.68)
    R(393,1040,.47,.52,.018,'white',.72)  # throw blanket
    # Gently rounded bed linen and pillows.
    R(593,265,1.73,1.32,.13,'fabric',.65)
    for xx in (545,638):
        R(xx,158,.59,.38,.14,'white',.72)
        R(xx,148,.47,.14,.09,'accent',.83)
    R(593,322,1.71,.18,.047,'white',.60)  # folded sheet edge
    # Kitchen cabinet joints, under-cabinet LED and tiled backsplash.
    for xx in (275,344,412,481,548):
        B(xx,751,.014,.035,.67,'woodDark',.13)
    for xx in (246,326,406,486,566):
        B(xx,770,.013,.013,.54,'woodDark',1.36)
    B(410,772,3.94,.036,.013,'white',1.59)
    # Integrated oven and realistic hob markers. All fixed to the original kitchen run.
    B(338,715,.64,.027,.57,'black',.17)
    B(338,713,.58,.015,.41,'glass',.25)
    B(338,712,.46,.011,.012,'metal',.64)
    for x in (315,351):
        for z in (726,743):
            C(x,z,.064,.012,'black',.952,28)
            C(x,z,.043,.013,'metal',.966,24)
    # Cylindrical dinner pendants and soft diffuser, centred over the exact same dining table.
    for x in (340,403,461):
        C(x,560,.009,.52,'black',1.72,10)
        C(x,560,.125,.14,'metal',1.56,32)
        C(x,560,.106,.035,'white',1.555,32)
    # Curtains positioned at the actual window walls in the given room polygons.
    # Decorative strips are intentionally behind furniture and do not create/relocate openings.
    for z in (827,864,901,938,975,1012,1049):
        B(205,z,.024,.22,1.90,'fabric',.27)
    for z in (482,525,568,611,654,697,740):
        B(207,z,.022,.20,1.86,'white',.33)
    for x in (477,512,548,584,620,656,692):
        B(x,58,.20,.024,1.77,'white',.31)
    # Bookcases, rounded ceramics and display accessories.
    for h in (.46,.72,.98,1.24):
        B(219,854,.25,.41,.026,'wood',h)
    for x in (208,220,233):
        for k in range(3):
            B(x,854,.035,.17,.23,'accent' if k%2 else 'woodDark',.50+k*.28)
    # Table styling: tray, vases and art; no dimensions of the apartment changed.
    C(404,558,.16,.020,'wood',.83,32)
    C(412,559,.058,.17,'stone',.86,24)
    S(415,561,.055,'green',1.06)
    C(393,924,.087,.018,'metal',.47,32)
    C(392,925,.060,.16,'stone',.49,24)
    # Vanity mirror and wall finish in existing bathroom.
    B(923,443,.62,.035,.68,'metal',1.06)
    B(923,440,.53,.011,.59,'glass',1.09)
    C(871,501,.21,.012,'white',.57,32)
    # Layered accent lighting in bedrooms and living (fittings only, no new windows).
    for x,z in ((490,155),(696,154),(548,1067)):
        C(x,z,.12,.08,'metal',1.60,28)
        C(x,z,.10,.028,'white',1.58,28)
    output=ROOT/f'kvartira-{style}.glb';sc.export(output)
    print(style,'nodes',len(sc.graph.nodes_geometry),'bytes',output.stat().st_size)

if __name__=='__main__':
    for k in STYLES:export_style(k)
