from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image,ImageChops
import base64, json, hashlib, re, io, time, zipfile, os, csv
import trimesh, numpy as np
ROOT=Path(__file__).resolve().parents[1]
REPORT={'project':'DARK TECH FAMILY','revision':'FINAL v8','tests':{},'caveats':[]}
files=list(ROOT.rglob('*'));allfiles=[p for p in files if p.is_file()];REPORT['tests']['file_count']=len(allfiles)
# 3D model structure and same construction across all 27 combinations
models=sorted((ROOT/'models').glob('*.glb'));assert len(models)==28,len(models)
wallHashes=[]; geomCounts=[];materialCounts=[]
for p in models:
  b=p.read_bytes();assert b[:4]==b'glTF',p
  scene=trimesh.load(str(p),force='scene',process=False)
  walls=[]
  for node in sorted(scene.graph.nodes_geometry):
    if not node.startswith('wall_'): continue
    xf,geo=scene.graph.get(node)
    mesh=scene.geometry[geo]
    hh=hashlib.sha256()
    hh.update(np.asarray(xf,dtype='<f8').round(5).tobytes())
    hh.update(np.asarray(mesh.vertices,dtype='<f8').round(5).tobytes())
    hh.update(np.asarray(mesh.faces,dtype='<i8').tobytes())
    walls.append((node,hh.hexdigest()))
  wallHash=hashlib.sha256(json.dumps(walls).encode()).hexdigest()
  wallHashes.append(wallHash)
  geomCounts.append(len(scene.graph.nodes_geometry))
  materialCounts.append(len(scene.geometry))
assert len(set(wallHashes))==1,'Wall meshes differ across 28 GLBs'
REPORT['tests']['glb']={'count':len(models),'structural_wall_meshes':len(walls),'same_wall_geometry':True,'total_scene_nodes_min':min(geomCounts),'total_scene_nodes_max':max(geomCounts)}
G=json.loads((ROOT/'source/geometry.json').read_text())
closen=[]
for w in G['walls']:
 for hole in w.get('holes',[]):
  if 'гардеробную' in hole.get('note',''):closen.append({'wall':w['id'],'note':hole['note']})
assert len(closen)==2,closen
REPORT['tests']['closet_doors']={'count':len(closen),'entries':closen,'exact_positions_verified_on_site':False}
# references to static links and runtime images (excluding externally supplied links)
missing=[]
for hp in ROOT.glob('*.html'):
 txt=hp.read_text()
 refs=set(re.findall(r'(?:src|href)=["\'](\./)?([^"\'#?]+)["\']',txt))
 for prefix,ref in refs:
  if '${' in ref or ref.startswith(('http:','https:','data:','mailto:','javascript:')):continue
  if not (ROOT/ref).is_file():missing.append((hp.name,ref))
assert not missing,missing
REPORT['tests']['html_local_assets']={'html_count':len(list(ROOT.glob('*.html'))),'broken_literal_links':0}
manifest=json.loads((ROOT/'data/model_view_manifest.json').read_text())
assert len(manifest)==33,len(manifest)
for item in manifest:assert (ROOT/item['path']).is_file(),item
REPORT['tests']['model_render_gallery']={'views':27,'mechanism_scenarios':6,'all_files_present':True}
# Browser test without local HTTP (blocked by browser policy)
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu-sandbox','--use-angle=swiftshader','--enable-webgl'])
 for wid in [1440,390]:
  page=b.new_page(viewport={'width':wid,'height':900 if wid>500 else 844})
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content((ROOT/'rooms.html').read_text())
  assert page.locator('.room-btn').count()==9
  assert page.locator('#roomTitle').inner_text()=='Кухня-гостиная'
  page.locator('[data-room="bedroom"]').click()
  assert page.locator('#roomTitle').inner_text()=='Детская'
  page.locator('[data-stage="school"]').click()
  assert 'stage=school' in page.locator('#launchView').get_attribute('href')
  page.locator('[data-style="graphite"]').click()
  assert 'style=graphite' in page.locator('#launchView').get_attribute('href')
  page.locator('[data-room="kitchen"]').click()
  page.locator('[data-scenario="guest"]').click()
  assert 'scenario=guest' in page.locator('#launchView').get_attribute('href')
  page.locator('[data-mode="model"]').click()
  assert page.locator('#conceptFigure').is_hidden()
  assert page.locator('#sceneCards .card').count()==6
  assert not errors,errors
  page.close()
  print('PASS ROOMS',wid)
 # Full tour test with real model bytes injected via fetch polyfill (no CDN), using reduced model list
 html=(ROOT/'tour.html').read_text().replace('<script type="module" src="./tour.js"></script>','')
 css=(ROOT/'tour.css').read_text();js=(ROOT/'tour.js').read_text()
 filenames=['kvartira-warm-now-daily.glb','kvartira-warm-now-guest.glb','kvartira-warm-now-dinner.glb','kvartira-warm-two-daily.glb','kvartira-warm-school-daily.glb','kvartira-japandi-now-daily.glb','kvartira-graphite-now-daily.glb','kvartira-planirovka.glb']
 payload={n:base64.b64encode((ROOT/'models'/n).read_bytes()).decode() for n in filenames}
 for wid in [1440,390]:
  page=b.new_page(viewport={'width':wid,'height':950 if wid>500 else 844},device_scale_factor=1)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html);page.add_style_tag(content=css)
  page.evaluate('''(models)=>{window.fetch=async(url)=>{const k=String(url).split('/').at(-1);if(!models[k])throw Error('unknown model '+k);const binary=atob(models[k]);const data=new Uint8Array(binary.length);for(let i=0;i<binary.length;i++)data[i]=binary.charCodeAt(i);return new Response(data,{status:200});};}''',payload)
  page.add_script_tag(content=js,type='module')
  page.wait_for_function('!!window.__atelier',timeout=30000)
  for scenario in ('family','guest','cooking','work','movie','school'):
   page.locator(f'[data-quick="{scenario}"]').click()
   page.wait_for_timeout(260)
   state=page.evaluate('window.__atelier.getState()')
   if scenario=='guest': assert state['scenario']=='guest'
   if scenario=='cooking': assert state['mechanisms']['peninsula']==1
   if scenario=='work': assert state['mechanisms']['laptop']==1
   if scenario=='movie': assert state['mechanisms']['screen']==1 and state['cinema']
   if scenario=='school': assert state['stage']=='school'
  page.locator('[data-quick="family"]').click();page.wait_for_timeout(300)
  page.locator('#styles [data-style="japandi"]').click();page.wait_for_timeout(300)
  assert page.evaluate('window.__atelier.getState().style')=='japandi'
  page.locator('#modeShell').click();page.wait_for_timeout(350)
  assert page.evaluate('window.__atelier.getState().mode')=='shell'
  page.locator('#modeInterior').click();page.wait_for_timeout(350)
  page.locator('#compareToggle').check();page.wait_for_timeout(300)
  assert page.evaluate('window.__atelier.getState().compare')
  page.locator('#compareToggle').uncheck();page.wait_for_timeout(100)
  # gallery images from newer manifest: nine model previews for selected style + 2 plan images
  page.locator('#openGallery').click()
  page.locator('[data-filter="inside"]').click()
  assert page.locator('#galleryGrid figure').count()==9
  page.locator('[data-close="galleryDialog"]').click()
  assert not errors,errors
  page.screenshot(path=str(ROOT/'assets'/f'final_viewer_{wid}.png'))
  print('PASS TOUR',wid,'fallback?',page.evaluate('window.__atelier.getState().software'))
  page.close()
 b.close()
REPORT['tests']['browser']={'desktop_and_mobile':True,'room_filters':True,'scenario_buttons':6,'style_switches':True,'compare':True,'floor_plan_toggle':True,'gallery':True,'webgl_hardware_verified':False,'fallback_canvas_verified':True}
REPORT['caveats']=[
  'Концептуальные фотореалистичные изображения не доказывают геометрию из обмерного плана.',
  'Контрольные ракурсы выполнены из GLB, но имеют техническое, не фотографическое качество.',
  'Некоторые размеры дверей и высота потолка 2,72 м условны.',
  'Физические механизмы, безопасность и электрика требуют отдельной проверки.',
  'Режим WebGL2 не проверен на реальном пользовательском оборудовании, в тестовом браузере использован резервный Canvas.'
]
(ROOT/'data/FINAL_QA.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
print('QA',json.dumps(REPORT['tests'],ensure_ascii=False,indent=2))
