from pathlib import Path
from math import cos,sin,pi
import json,html,random,zipfile,shutil,os
from shapely.geometry import box as shpbox
import cairosvg
from PIL import Image,ImageOps,ImageDraw,ImageFont

ROOT=Path('/mnt/data/DARK_TECH_FAMILY_Planning_v3')
PLANS=ROOT/'plans'; PLANS.mkdir(exist_ok=True)
SRC=ROOT/'source'; ASSET=ROOT/'reference'; ASSET.mkdir(exist_ok=True)
G=json.loads((SRC/'geometry.json').read_text(encoding='utf8'))

P={
 'bg':'#0B111A','surface':'#151E2A','surface2':'#1C2836','grid':'#2D3B48','wall':'#EBEEF2','secondary':'#A8B4C4',
 'amber':'#E9B77E','cyan':'#66C9D6','sage':'#83B9A3','rose':'#D48E96','line':'#647385','dark':'#141E29'}

def esc(x):return html.escape(str(x),quote=True)
def rect(x,y,w,h,fill,rx=0,stroke='none',sw=0,opacity=1,more=''):
 return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}" {more}/>'
def line(x1,y1,x2,y2,color,width=2,dash=None,opacity=1):
 return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}" opacity="{opacity}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def text(x,y,t,size=18,color='#E9EDF3',weight=400,anchor='start',letter=0,opacity=1):
 return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}" letter-spacing="{letter}" opacity="{opacity}">{esc(t)}</text>'
def circle(x,y,r,fill,opacity=1,stroke='none',sw=0):
 return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>'
def path(d,fill='none',stroke='#FFF',sw=2,dash=None):
 return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def svg(content,w=1440,h=930):
 return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>text{{font-family:Arial,'DejaVu Sans',sans-serif}}.note{{font-size:16px}}</style>{rect(0,0,w,h,P['bg'])}{content}</svg>'''

# room coordinates meters, measured from kitchen upper-left reference.
S=140.; OX=113.; OY=245.; W=4.54; H=3.47
def X(v):return OX+S*v
def Y(v):return OY+S*v

def label_box(x,y,w,h,label,fill,sz=15,letter=0):
 v=[rect(x,y,w,h,fill,8)]
 if label:
  v.append(text(x+w/2,y+h/2+sz*.32,label,sz,'#F6F8FA',600,'middle',letter))
 return ''.join(v)
def furniture(x,y,w,h,fill,name,sz=14,edge=P['amber'],ghost=False):
 xx,yy,ww,hh=X(x),Y(y),S*w,S*h
 return rect(xx,yy,ww,hh,fill,7,edge,1.8,.24 if ghost else 1)+text(xx+ww/2,yy+hh/2+sz/3,name,sz,'#F6F8FA',600,'middle')

def dim(x1,y1,x2,y2,lab,anchor='middle'):
 v=line(x1,y1,x2,y2,P['secondary'],1.2)
 if abs(x2-x1)>abs(y2-y1):
  v+=line(x1,y1-6,x1,y1+6,P['secondary'],1)+line(x2,y2-6,x2,y2+6,P['secondary'],1)
  v+=text((x1+x2)/2,y1-10,lab,15,P['secondary'],500,'middle')
 else:
  v+=line(x1-6,y1,x1+6,y1,P['secondary'],1)+line(x2-6,y2,x2+6,y2,P['secondary'],1)
  v+=text(x1-12,(y1+y2)/2,lab,15,P['secondary'],500,'end')
 return v

def room_base():
 out=[]
 out.append(rect(OX,OY,S*W,S*H,P['surface2']))
 for xx in [1,2,3,4]:out.append(line(X(xx),Y(0),X(xx),Y(H),P['grid'],1,'4 10',.6))
 for yy in [1,2,3]:out.append(line(X(0),Y(yy),X(W),Y(yy),P['grid'],1,'4 10',.6))
 # room walls, drawn as segments around actual wall openings
 out.extend([
  line(X(0),Y(0),X(.84),Y(0),P['wall'],8), line(X(1.81),Y(0),X(W),Y(0),P['wall'],8),
  line(X(0),Y(0),X(0),Y(.73),P['wall'],8),line(X(0),Y(1.21),X(0),Y(H),P['wall'],8),
  line(X(W),Y(0),X(W),Y(1.01),P['wall'],8),line(X(W),Y(1.86),X(W),Y(H),P['wall'],8),
  line(X(0),Y(H),X(W),Y(H),P['wall'],8),
  line(X(.84),Y(0),X(1.81),Y(0),P['cyan'],5),
  line(X(0),Y(.73),X(0),Y(1.21),P['cyan'],5),
  line(X(W),Y(1.01),X(W),Y(1.86),P['amber'],3,'4 5')
 ])
 out += [text(X(1.32),Y(0)+22,'ВЫХОД НА ЛОДЖИЮ',13,P['cyan'],600,'middle'),
         text(X(0)-9,Y(.98),'ОКНО',13,P['cyan'],600,'end'),
         text(X(W)+12,Y(1.5),'ВХОД',13,P['amber'],600),
         dim(X(0),Y(0)-16,X(W),Y(0)-16,'4,54 м по чертежу'),
         dim(X(0)-52,Y(0),X(0)-52,Y(H),'3,47 м по чертежу'),
         text(X(2.3),Y(1.5),'',11)]
 # hall entrance protection zone is a *non-furniture overlay*, not a door leaf or swing assertion
 out.append(rect(X(3.73),Y(1.01),S*.81,S*.84,'none',0,P['amber'],1.3,.8,'stroke-dasharray="7 5"'))
 out.append(text(X(4.16),Y(1.54),'ПРОХОД',10,P['amber'],600,'middle'))
 return ''.join(out)

def cabinetry():
 t=[]
 units=[(0.03,.60,'ХОЛОД'),(.63,1.1,'СТОЛЕШ.'),(1.73,.8,'ПЛИТА'),(2.53,.66,'СТОЛЕШ.'),(3.19,.66,'МОЙКА'),(3.85,.60,'П/М')]
 for x,w,name in units:
  t.append(furniture(x,2.83,w,.56,'#355A65',name,11,edge='#6BA7B7'))
 t+= [circle(X(2.13),Y(3.10),10,'none',1,'#C3D9DA',2),circle(X(2.23),Y(3.10),10,'none',1,'#C3D9DA',2),
      rect(X(3.33),Y(2.96),S*.38,S*.31,'#193740',5,'#88B6C3',1.2),
      text(X(2.28),Y(3.74),'ЛИНЕЙНАЯ КУХНЯ · техника остаётся у исходной стены',13,P['secondary'],400,'middle')]
 return ''.join(t)

def theater():
 # screen width about 1.45m on eastern wall; exact mount dimensions unverified.
 t=[rect(X(4.39),Y(1.92),S*.09,S*1.45,'#1D3344',5,P['cyan'],2),
    text(X(4.05),Y(2.42),'ТВ 65″?',13,P['cyan'],700,'middle'),
    rect(X(4.19),Y(2.65),S*.16,S*.26,'#526677',2),
    text(X(4.08),Y(3.02),'звук',10,P['secondary'],400,'middle')]
 return ''.join(t)

def sofa(mode):
 if mode=='guest':
  x,y,w,h=.14,.95,2.01,1.67
  out=furniture(x,y,w,h,'#9B6E59','ГОСТЕВОЕ МЕСТО 1,6×2,0 м',12,'#EBC2A3')
  out+=rect(X(.95),Y(.95),S*1.2,S*1.67,'none',0,P['amber'],1.4,.8,'stroke-dasharray="9 5"')
 else:
  out=furniture(.14,.95,.86,1.67,'#946E59','ДИВАН-КРОВАТЬ',12,'#DFB18F')
  for yy in [1.13,1.66,2.17]:out+=line(X(.15),Y(yy),X(.93),Y(yy),'#D9BDA8',1.8)
 return out

def table(mode,variant):
 v=[]
 if mode=='dinner':
  # banquet format: two on sofa, three on outer side, one north. Explicitly tight.
  v.append(furniture(1.15,1.05,.86,1.75,'#B98F63','СТОЛ 6',13,'#F4C991'))
  for yy in [1.08,1.64,2.2]:v.append(rect(X(2.11),Y(yy),S*.46,S*.39,'#4B6570',8,'#9FB3BC',1))
  v.append(rect(X(1.36),Y(.46),S*.47,S*.45,'#4B6570',8,'#9FB3BC',1))
  v.append(text(X(2.79),Y(1.3),'3 стула',12,P['secondary']))
  v.append(text(X(.46),Y(2.21),'2 места на',12,'#F8E3D1',600,'middle'))
  v.append(text(X(.46),Y(2.34),'диване',12,'#F8E3D1',600,'middle'))
 elif mode=='guest':
  v.append(furniture(2.45,.18,1.05,.60,'#B98F63','СТОЛ СЛОЖЕН',11,'#F4C991'))
 else:
  v.append(furniture(2.15,.25,1.18,.75,'#B98F63','СТОЛ 2–4',13,'#F4C991'))
 return ''.join(v)

def accessories(variant,mode):
 v=[]
 if variant=='B':
  v.append(furniture(3.57,.16,.83,.48,'#5C6584','НОУТБУК',11,'#B7C0DA'))
  if mode=='daily':
   v.append(rect(X(3.30),Y(.70),S*1.10,S*.30,'none',0,'#B7C0DA',1.3,1,'stroke-dasharray="5 4"'))
   v.append(text(X(3.8),Y(.91),'откидная полка',11,'#B7C0DA',400,'middle'))
 if variant=='C':
  if mode=='daily':
   v.append(furniture(3.01,2.16,.60,.66,'#566E5E','ВЫДВИЖ.',11,'#B1D0A1'))
   v.append(text(X(2.95),Y(2.10),'+0,4 м²',11,P['sage'],600,'middle'))
  else:
   v.append(rect(X(3.01),Y(2.73),S*.60,S*.08,'#566E5E',3,'#B1D0A1',1))
 return ''.join(v)

VAR={
 'A': {'name':'Кинотеатр','big':'СЕМЕЙНЫЙ КИНОЗАЛ','tag':'Максимум для отдыха','lines':['Диван-кровать 1,67 м у боковой стены.','Линейная кухня 4,4 м; ТВ 65″ — под вопросом.','Стол раскладывается для 6 через диван-банкетку.'], 'safety':['Гостевое место нельзя использовать одновременно с сервировкой на шестерых.','У окна и ТВ нужна очная проверка створок и креплений.'], 'decision':'Лучший баланс для семьи'},
 'B': {'name':'Трансформер','big':'СКРЫТАЯ РАБОЧАЯ ЗОНА','tag':'Работа + гости','lines':['Дополнительная откидная ноутбук-полка.','Стол перемещается между режимами.','Акустическая ниша и хранение без стационарных мониторов.'], 'safety':['Разложенная рабочая полка и шесть мест за столом — разные сценарии.','Для записи вокала нужна акустика, а не только звукопоглощающая отделка.'], 'decision':'Лучший для домашней студии'},
 'C': {'name':'Кулинарный центр','big':'ГОТОВИМ ВМЕСТЕ','tag':'Дополнительная столешница','lines':['Выдвижная поверхность добавляет около 0,4 м².','Свободная полоса у входа около 0,9 м.','Большой остров не помещается без потери прохода.'], 'safety':['Выдвижная столешница убирается перед раскладыванием гостевого места.','Уточнить электрику, высокие модули и расположение стояков.'], 'decision':'Лучший для совместной готовки'},
}
MOD={ 'daily':('ПОВСЕДНЕВНО','2–4 места · диван сложен'), 'guest':('ГОСТЬ НОЧУЕТ','диван разложен · стол сложен'), 'dinner':('УЖИН НА ШЕСТЕРЫХ','стол расширен · диван сложен')}

def kitchen_svg(var,mode):
 d=VAR[var]; m,m2=MOD[mode]
 out=[]
 out.append(rect(42,38,1356,851,'#101925',24,'#2B3948',1.4))
 out.append(text(105,93,'ATELIER   /   DARK TECH FAMILY',18,P['amber'],600,letter=3))
 out.append(text(105,145,'0'+str('ABC'.index(var)+1)+'   '+d['big'],34,'#F5F5F5',700))
 out.append(text(105,184,f'{m}  /  {m2}',17,P['secondary'],400))
 out.append(room_base())
 out.append(cabinetry())
 out.append(theater())
 out.append(sofa(mode))
 out.append(table(mode,var))
 out.append(accessories(var,mode))
 # scale bar
 out.append(line(X(.15),Y(3.84),X(1.15),Y(3.84),'#E9EDF3',4))
 out.append(line(X(.15),Y(3.79),X(.15),Y(3.89),'#E9EDF3',2))
 out.append(line(X(1.15),Y(3.79),X(1.15),Y(3.89),'#E9EDF3',2))
 out.append(text(X(.65),Y(4.03),'1 м / масштабный отрезок',13,P['secondary'],400,'middle'))
 out.append(text(112,861,'Обмерные размеры 4,54 × 3,47 м. Стены и оконные проёмы не изменены.',13,P['secondary']))
 # side panel
 sx=825;out.append(rect(sx,215,508,565,'#1D2937',18,'#344657',1.5))
 out.append(text(sx+30,257,d['tag'].upper(),16,P['amber'],700,letter=1.6))
 out.append(text(sx+30,302,d['name'],30,'#F4F5F6',700))
 y=350
 for a in d['lines']:
  out.append(circle(sx+38,y-5,4,P['cyan']))
  out.append(text(sx+54,y,a,15,'#D7E0E9'));y+=46
 out.append(line(sx+30,y-10,sx+476,y-10,P['grid'],1));y+=32
 out.append(text(sx+30,y,'КОМПРОМИССЫ И ПРОВЕРКИ',15,P['rose'],700));y+=35
 for item in d['safety']:
  # wrap short hardcoded at 48 chars
  pieces=[];cur=''
  for word in item.split():
   if len(cur+' '+word)>51 and cur: pieces.append(cur);cur=word
   else:cur=(cur+' '+word).strip()
  if cur:pieces.append(cur)
  for p in pieces:out.append(text(sx+30,y,p,14,'#C0CBD9'));y+=23
  y+=18
 out.append(rect(sx+30,719,450,40,'#294339',9))
 out.append(text(sx+255,747,d['decision'],16,'#D5F4E2',600,'middle'))
 # simple notes on spatial constraints
 out.append(text(838,840,'Важно: схема — масштабный эскиз по двум изображениям,',13,P['secondary']))
 out.append(text(838,862,'не монтажный план. Дверные створки и высота уточняются.',13,P['secondary']))
 return svg(''.join(out),1440,930)

def global_plan_svg():
 # drawing at scale 0.93 from source pixel coords
 w,h=1600,1600;x0,y0=125,205;scale=1.00
 def xp(x):return x0+(x-159)*scale
 def yp(y):return y0+(y-20)*scale
 def item(x,y,ww,hh,name,fill,size=15):
  return rect(xp(x),yp(y),ww*scale,hh*scale,fill,5,'#C0CFD9',1.3)+text(xp(x+ww/2),yp(y+hh/2)+5,name,size,'#FFF',600,'middle')
 s=[rect(0,0,w,h,P['bg']),rect(36,35,w-72,h-70,'#111C28',28,'#304052',2)]
 s+=[text(90,99,'DARK TECH FAMILY / МАСШТАБНАЯ СХЕМА',23,P['amber'],700,letter=2.3),text(90,147,'Распределение функций — стены и проёмы из исходной геометрии v7',17,P['secondary'])]
 for r in G['rooms']:
  pts=' '.join(f'{xp(x):.2f},{yp(y):.2f}' for x,y in r['polygon'])
  fill={'bedroom':'#2C425C','kitchen':'#273F44','living':'#3B3443','hall':'#2B3243','bath':'#2A4150','wc':'#28424A','closet':'#514638','balcony':'#2E443E'}[r['id']]
  s.append(f'<polygon points="{pts}" fill="{fill}" stroke="none"/>')
  names={'bedroom':'ДЕТСКАЯ · 12,2 м²','kitchen':'КУХНЯ-ГОСТИНАЯ · 15,4 м²','living':'РОДИТЕЛИ · 13,8 м²','hall':'КОРИДОР · 7,8 м²','bath':'ВАННА','wc':'С/У','closet':'ГАРД.','balcony':'ЛОДЖИЯ · 3,4 м²'}
  lx,ly=r['label'] if 'label' in r else (r['polygon'][0][0],r['polygon'][0][1])
  if r['id'] in ('kitchen','living','bedroom'):
   s.append(text(xp(300),yp(665),names[r['id']],18,'#E7EEF4',700,'start') if r['id']=='kitchen' else text(xp(lx),yp(ly)-80,names[r['id']],20,'#E7EEF4',700,'middle'))
  else:
   s.append(text(xp(lx),yp(ly),names[r['id']],13,'#E7EEF4',700,'middle'))
 # structural walls and holes in pixel axes, split by absolute hole loc
 for wall in G['walls']:
  a=wall['a'];b=wall['b']; holes=wall.get('holes',[])
  ishor=abs(a[1]-b[1])<3; axis=0 if ishor else 1
  lo=min(a[axis],b[axis]);hi=max(a[axis],b[axis]); starts=[lo]+[v for hole in holes for v in (hole['a'],hole['b'])]+[hi]
  last=lo
  for hole in sorted(holes,key=lambda h:h['a']):
   if hole['a']>last:
    if ishor:s.append(line(xp(last),yp(a[1]),xp(hole['a']),yp(a[1]),P['wall'],7))
    else:s.append(line(xp(a[0]),yp(last),xp(a[0]),yp(hole['a']),P['wall'],7))
   if ishor:
    s.append(line(xp(hole['a']),yp(a[1]),xp(hole['b']),yp(a[1]),P['cyan'] if hole['type']=='window' else P['amber'],4))
   else:
    s.append(line(xp(a[0]),yp(hole['a']),xp(a[0]),yp(hole['b']),P['cyan'] if hole['type']=='window' else P['amber'],4))
   last=hole['b']
  if last<hi:
   if ishor:s.append(line(xp(last),yp(a[1]),xp(hi),yp(a[1]),P['wall'],7))
   else:s.append(line(xp(a[0]),yp(last),xp(a[0]),yp(hi),P['wall'],7))
 # furnishing, measured room sizes in source x,y pixels
 s.append(item(182+14,438+95,86,167,'ДИВАН', '#8D715D',13))
 s.append(item(182+215,438+25,118,75,'СТОЛ', '#A5855C',14))
 s.append(item(183,438+283,445,56,'КУХНЯ · 4,4 м', '#32626D',15))
 s.append(item(182+439,438+192,9,145,'ТВ', '#6D94AE',11))
 # parents bed: 180x200, access from right upper
 s.append(item(182+113,800+120,180,200,'КРОВАТЬ 180×200', '#856B78',15))
 s.append(item(182+15,800+145,65,125,'КРОВАТКА', '#967E70',12))
 s.append(item(182+45,800+18,102,49,'СТОЛИК', '#866D5D',13))
 s.append(item(182+221,800+7,145,12,'ТВ 65″', '#6D94AE',12))
 # kids 12.2: now and future note
 s.append(item(438+22,36+200,76,138,'КРОВАТЬ', '#617B9B',13))
 s.append(item(438+230,36+100,43,156,'ХРАН.', '#5A8B89',12))
 s.append(rect(xp(438+115),yp(36+110),118,170,'none',12,P['sage'],3,1,'stroke-dasharray="11 6"'))
 s.append(text(xp(438+175),yp(36+190),'ИГРЫ',19,P['sage'],700,'middle'))
 # balcony: concept only, mark zones
 s.append(item(176,288,66,54,'FDM', '#667C7A',13))
 s.append(item(274,288,103,45,'ЗЕЛЕНЬ', '#477858',13))
 s.append(text(xp(270),yp(365),'РЕЗИН: НЕ СОГЛАСОВАН',11,P['rose'],700,'middle'))
 # legend in side block
 bx=1030
 s.append(rect(bx,230,480,730,'#1D2A38',24,'#34475A',1.5))
 s.append(text(bx+34,280,'НАЗНАЧЕНИЕ КОМНАТ',20,'#FFF',700))
 txts=[('01','Кухня-гостиная','15,4 м²'),('02','Спальня родителей','13,8 м²'),('03','Детская для двоих','12,2 м²'),('04','Гардероб родителей','≈1,8 м²'),('05','Лоджия — мастерская*','≈3,4 м²')]
 for i,(id,n,area) in enumerate(txts):
  yy=337+i*70
  s.append(text(bx+34,yy,id,20,P['amber'],700))
  s.append(text(bx+77,yy,n,17,'#E7EFF5',500))
  s.append(text(bx+420,yy,area,15,P['secondary'],500,'end'))
 s.append(line(bx+32,720,bx+447,720,P['grid'],2))
 for i,t in enumerate(['Синие линии — оконные проёмы.','Песочные линии — двери и выход.','Проёмы на части стен условные.','*Лоджия требует отдельной инженерной проверки.']):
  s.append(text(bx+34,762+i*31,t,14,P['secondary']))
 s.append(text(95,1385,'ИСПРАВЛЕНО: ДВА СУЩЕСТВУЮЩИХ ВХОДА В ГАРДЕРОБНУЮ',18,P['amber'],700))
 s.append(text(95,1416,'Из коридора и из родительской спальни. Точная ширина второго проёма уточняется.',16,P['secondary']))
 s.append(text(95,1468,'Двери, стояки, высота потолка и некоторые санузлы — требуют натурного уточнения.',16,P['secondary']))
 s.append(text(95,1515,'100 px ≈ 1 метр исходного чертежа; мебель проектная. Эскиз не является рабочим проектом.',16,'#8498AA'))
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>text{{font-family:Arial,DejaVu Sans,sans-serif}}</style>{"".join(s)}</svg>'

# Run
for var in VAR:
 for mode in MOD:
  name=f'kitchen_{var}_{mode}'
  f=PLANS/f'{name}.svg';f.write_text(kitchen_svg(var,mode),encoding='utf8')
  cairosvg.svg2png(url=str(f),write_to=str(PLANS/f'{name}.png'),output_width=1080)
print('Wrote',len(list(PLANS.glob('kitchen_*.svg'))),'detail plans')
full=PLANS/'apartment_zoning.svg';full.write_text(global_plan_svg(),encoding='utf8')
cairosvg.svg2png(url=str(full),write_to=str(PLANS/'apartment_zoning.png'),output_width=1200)

# visual comparison contact for the 3 everyday layouts
thumbs=[]
for v in VAR:
 im=Image.open(PLANS/f'kitchen_{v}_daily.png').convert('RGB')
 # top half image contains plan and side explanation; keep full image for comparison
 thumbs.append(im)
out=Image.new('RGB',(1080,3*700+160),(10,17,26)); d=ImageDraw.Draw(out)
try:f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25)
except:f=ImageFont.load_default()
d.text((35,28),'DARK TECH FAMILY  •  3 ПЛАНИРОВОЧНЫХ РЕШЕНИЯ',fill=(230,183,126),font=f)
for i,im in enumerate(thumbs):
 im=ImageOps.contain(im,(1060,675));out.paste(im,(10,90+i*700))
out.save(PLANS/'compare_3_options.jpg',quality=90)

# reproducible checks, not a guarantee of practical ergonomics
room=shpbox(0,0,W,H)
fixed=[('cabinets',shpbox(.03,2.83,4.45,3.39)),('door_keep_clear',shpbox(3.73,1.01,4.54,1.85))]
checks={}
for v in VAR:
 checks[v]={}
 for mode in MOD:
  furniture_rects=[('sofa',shpbox(.14,.95,2.15 if mode=='guest' else 1.00,2.62)),('table',shpbox(*( (1.15,1.05,2.01,2.80) if mode=='dinner' else (2.45,.18,3.5,.78) if mode=='guest' else (2.15,.25,3.33,1.0))))]
  if v=='B':furniture_rects.append(('desk',shpbox(3.57,.16,4.40,.64)))
  if v=='C' and mode=='daily':furniture_rects.append(('pullout_prep',shpbox(3.01,2.16,3.61,2.82)))
  issues=[]
  for name,r in furniture_rects:
   if not room.covers(r):issues.append(f'{name} outside room')
   for fname,fr in fixed:
    if r.intersection(fr).area>.00001:issues.append(f'{name} conflicts with {fname}')
  for i,(an,a) in enumerate(furniture_rects):
   for bn,b in furniture_rects[i+1:]:
    if a.intersection(b).area>.00001:issues.append(f'{an} intersects {bn}')
  checks[v][mode]={'hard_rect_overlap':issues,'limitations':['Door swings and human circulation not surveyed; unfolded sofa is near kitchen fronts','6-seat mode limits balcony use']}
(ROOT/'data').mkdir(exist_ok=True)
(ROOT/'data'/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'data'/'options.json').write_text(json.dumps({'concept':'DARK TECH FAMILY','room_m':{'width':W,'depth':H,'source':'measured plan and existing geometry calibration'},'options':VAR,'modes':MOD},ensure_ascii=False,indent=2),encoding='utf8')
print('collision reports:',checks)

# ─── Bedroom and nursery: same measured geometry, furniture scenarios ───
def small_room_svg(kind,stage):
 if kind=='parents':
  width,depth=4.23,3.27; heading='СПАЛЬНЯ РОДИТЕЛЕЙ';sub='Кровать 180×200 · детская кроватка · ТВ 65″ · туалетный столик'
  spec=['Гардеробная 1,8 м²: два входа, из коридора и спальни.','Кроватка у окна: высоту подоконника и створки проверить.','Столик супруги в комнате, перенос в гардеробную не подтверждён.']
 else:
  width,depth=3.17,3.84;heading='ДЕТСКАЯ НА ДВОИХ'
  sub={'now':'ЭТАП 1  /  малыш 1,5 года · максимум места для игр','two':'ЭТАП 2  /  двое маленьких детей · две низкие кровати','school':'ЭТАП 3  /  школьный возраст · двухъярусная система'}[stage]
  spec={'now':['Никаких верхних спальных мест для маленьких детей.','Низкое закрытое хранение, защита острых углов.','Свободный центр комнаты для игр и движения.'],
        'two':['Отдельные низкие кровати для каждого ребёнка.','Не блокировать вход и оконную зону.','Мобильные шкафы и трансформируемое хранение.'],
        'school':['Верхняя кровать — только для ребёнка подходящего возраста.','Высоту и расстояния до потолка проверить обмерами.','Стол для каждого, индивидуальное освещение и хранение.']}[stage]
 origin_x,origin_y=130,230;sc=120 if kind=='parents' else 145
 def x(a):return origin_x+sc*a
 def y(a):return origin_y+sc*a
 v=[rect(36,34,1368,858,'#111A26',22,'#314152',1.5),text(90,86,'ATELIER / DARK TECH FAMILY',17,P['amber'],600,letter=2.2),text(90,143,heading,38,'#F7F7F7',700),text(90,183,sub,17,P['secondary'])]
 v.append(rect(x(0),y(0),width*sc,depth*sc,P['surface2']))
 for i in range(1,int(width)+1):v.append(line(x(i),y(0),x(i),y(depth),P['grid'],1,'5 8',.6))
 for i in range(1,int(depth)+1):v.append(line(x(0),y(i),x(width),y(i),P['grid'],1,'5 8',.6))
 if kind=='parents':
  # Main bedroom and adjacent *existing* walk-through wardrobe. The hall door and bedroom door are distinct.
  # Door centres are approximate because full door opening dimensions are missing from measured survey.
  v.extend([line(x(0),y(0),x(width),y(0),P['wall'],8),line(x(0),y(depth),x(width+1.27),y(depth),P['wall'],8),
    line(x(0),y(0),x(0),y(.77),P['wall'],8),line(x(0),y(.77),x(0),y(2.56),P['cyan'],5),line(x(0),y(2.56),x(0),y(depth),P['wall'],8),
    line(x(width),y(0),x(width),y(.12),P['wall'],8),line(x(width),y(.12),x(width),y(1.0),P['amber'],4,'5 6'),
    line(x(width),y(1.0),x(width),y(2.03),P['wall'],8),
    line(x(width),y(2.03),x(width),y(2.78),P['amber'],5,'5 5'),
    line(x(width),y(2.78),x(width),y(depth),P['wall'],8)])
  # Bedroom-wardrobe opening is on shared east wall. Corridor-wardrobe opening is on wardrobe north wall.
  v.append(rect(x(width+.12),y(depth-1.47),1.15*sc,1.47*sc,'#514638',0))
  v += [line(x(width+.12),y(depth-1.47),x(width+.22),y(depth-1.47),P['wall'],7),
        line(x(width+.22),y(depth-1.47),x(width+.97),y(depth-1.47),P['amber'],5,'5 5'),
        line(x(width+.97),y(depth-1.47),x(width+1.27),y(depth-1.47),P['wall'],7),
        line(x(width+1.27),y(depth-1.47),x(width+1.27),y(depth),P['wall'],7),
        text(x(width+0.72),y(depth-1.47)+36,'ВХОД С КОРИДОРА',12,P['amber'],700,'middle'),
        text(x(width+0.75),y(2.55),'ГАРД.',16,'#F6E1C1',700,'middle'),
        text(x(3.80),y(2.30),'В ГАРД.',10,P['amber'],600,'middle')]
  # Shelving deliberately kept to the east edge; both openings shown free.
  v.append(rect(x(width+1.03),y(2.25),.17*sc,.69*sc,'#896F57',3,'#C0A37E',1))
  v.append(text(x(width+.68),y(3.08),'1,8 м²',13,'#DBC9B7',400,'middle'))
 else:
  v.extend([line(x(0),y(0),x(.72),y(0),P['wall'],8),line(x(.72),y(0),x(2.53),y(0),P['cyan'],5),line(x(2.53),y(0),x(width),y(0),P['wall'],8),
    line(x(0),y(0),x(0),y(depth),P['wall'],8),line(x(width),y(0),x(width),y(depth),P['wall'],8),
    line(x(0),y(depth),x(2.22),y(depth),P['wall'],8),line(x(2.22),y(depth),x(3.10),y(depth),P['amber'],4,'5 6'),line(x(3.10),y(depth),x(width),y(depth),P['wall'],8)])
 v += [dim(x(0),y(-.10),x(width),y(-.10),f'{width:.2f} м'),dim(x(-.22),y(0),x(-.22),y(depth),f'{depth:.2f} м')]
 def it(a,b,c,d,n,col,fs=14):
  v.append(rect(x(a),y(b),c*sc,d*sc,col,8,'#C7CED6',1.4))
  v.append(text(x(a+c/2),y(b+d/2)+fs/3,n,fs,'#FFF',600,'middle'))
 if kind=='parents':
  it(1.45,1.22,1.80,2.0,'КРОВАТЬ 180×200','#806878',15)
  it(.25,1.34,.70,1.28,'ДЕТСКАЯ', '#8F7B69',14)
  it(.34,.15,1.10,.48,'ТУАЛЕТНЫЙ СТОЛ', '#5F6F77',13)
  it(2.01,.08,1.45,.09,'ТВ 65″','#497E91',12)
  it(.36,2.75,.49,.35,'СОБАКА', '#546A60',10)
  it(3.53,2.73,.48,.35,'СОБАКА','#546A60',10)
  v.append(text(x(3.82),y(.76),'ВХОД ИЗ КОРИДОРА',11,P['amber'],600,'middle'))
  v.append(text(x(.35),y(1.08),'ОКНО',12,P['cyan'],600))
 else:
  if stage=='now':
   it(.18,2.05,.76,1.42,'КРОВАТЬ','#647E9E',13)
   it(2.65,.90,.40,1.45,'ХРАНЕНИЕ','#537B77',11)
   v.append(rect(x(1.02),y(.90),1.45*sc,1.98*sc,'none',14,P['sage'],2,1,'stroke-dasharray="11 6"'))
   v.append(text(x(1.72),y(1.87),'ИГРОВАЯ',22,P['sage'],700,'middle'))
  elif stage=='two':
   it(.13,1.45,.78,1.65,'КРОВАТЬ 1','#647E9E',12)
   it(1.34,1.45,.78,1.65,'КРОВАТЬ 2','#8D798B',12)
   it(2.61,.73,.43,1.50,'ШКАФ','#537B77',12)
   v.append(text(x(1.45),y(.93),'ИГРЫ',19,P['sage'],700,'middle'))
  else:
   it(.13,.95,1.01,2.03,'ДВУХЪЯРУС.','#647E9E',12)
   it(1.40,.33,1.46,.56,'РАБОЧИЙ СТОЛ 1','#617B7E',12)
   it(1.40,2.72,1.38,.51,'РАБОЧИЙ СТОЛ 2','#617B7E',12)
   it(2.62,1.17,.41,1.15,'ШКАФ','#537B77',11)
   v.append(text(x(.66),y(1.78),'УЧЁБА',12,P['sage'],700,'middle'))
  v.append(text(x(2.68),y(3.58),'ВХОД',12,P['amber'],600,'middle'))
  v.append(text(x(1.65),y(.25),'ОКНО',12,P['cyan'],600,'middle'))
 # info
 bx=800;v.append(rect(bx,235,540,472,'#1D2A38',20,'#344757',1.4))
 v.append(text(bx+32,280,'ПОЯСНЕНИЯ ДИЗАЙНЕРА',18,P['amber'],700))
 yy=338
 for part in spec:
  pieces=[];cur=''
  for word in part.split():
   if len(cur+' '+word)>53 and cur:pieces.append(cur);cur=word
   else:cur=(cur+' '+word).strip()
  if cur:pieces.append(cur)
  for i,p in enumerate(pieces):v.append(text(bx+32,yy,p,15,'#DAE2EB'));yy+=23
  yy+=32
 v.append(line(835,770,985,770,'#E7ECF3',4))
 v.append(text(910,796,'масштаб: 1 метр',15,P['secondary'],400,'middle'))
 v.append(text(95,820,'Геометрия — по обмерам + уточнение пользователя о второй двери; мебель — предложение.',17,'#AAB7C7'))
 v.append(text(95,853,'Два входа в гардеробную подтверждены. Их ширину и точные координаты нужно проверить.',15,'#71899B'))
 return svg(''.join(v),1440,930)

for kind,states in [('parents',['now']),('children',['now','two','school'])]:
 for state in states:
  n=f'{kind}_{state}'
  f=PLANS/f'{n}.svg';f.write_text(small_room_svg(kind,state),encoding='utf8')
  cairosvg.svg2png(url=str(f),write_to=str(PLANS/f'{n}.png'),output_width=1080)
print('Added rooms',len(list(PLANS.glob('parents_*.svg')))+len(list(PLANS.glob('children_*.svg'))))
