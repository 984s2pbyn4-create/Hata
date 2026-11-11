from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
root=Path('/mnt/data/DARK_TECH_FAMILY_Planning_v2')
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu'])
 for kind,size in [('desktop',{'width':1400,'height':900}),('mobile',{'width':390,'height':844})]:
  page=browser.new_page(viewport=size)
  errors=[];page.on('pageerror',lambda err: errors.append(str(err)))
  def serve(route):
   rel=urlparse(route.request.url).path.lstrip('/') or 'index.html'
   local=(root/rel).resolve()
   if not str(local).startswith(str(root)) or not local.exists():return route.fulfill(status=404,body='Not found')
   mime=mimetypes.guess_type(str(local))[0] or 'application/octet-stream'
   return route.fulfill(status=200,content_type=mime,body=local.read_bytes())
  page.set_content((root/'index.html').read_text(encoding='utf8'),wait_until='domcontentloaded')
  page.locator('img#planImage').wait_for()
  page.locator('[data-variant="B"]').click()
  page.locator('[data-mode="guest"]').click()
  assert page.locator('img#planImage').get_attribute('src')=='plans/kitchen_B_guest.svg'
  page.locator('[data-variant="C"]').click()
  page.locator('[data-mode="dinner"]').click()
  assert page.locator('img#planImage').get_attribute('src')=='plans/kitchen_C_dinner.svg'
  page.locator('[data-child="school"]').click()
  assert page.locator('img#childImage').get_attribute('src')=='plans/children_school.svg'
  assert (root/page.locator('img#childImage').get_attribute('src')).exists()
  assert (root/page.locator('img#planImage').get_attribute('src')).exists()
  page.screenshot(path=str(root/'plans'/f'site_{kind}.png'),full_page=True)
  print(kind,'asset files exist, controls working, errors',errors, 'scroll width',page.evaluate('document.documentElement.scrollWidth'))
  assert not errors
  page.close()
 browser.close()
