#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from bs4 import BeautifulSoup, Tag
import json, re, textwrap

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://chriscarazas.com'
EDITION = 'XI'
CSS_VERSION = '6.6'
NAV = [
    ('Home','/'),('Book','/book/'),('Buy','/buy/'),('Road to 2,000','/road-to-2000/'),
    ('Writing','/writing/'),('Gazette','/gazette/'),('Reviews','/reviews/'),
    ('Podcasts','/podcasts/'),('About','/about/')
]
PAGES = {
    '/': {'label':'Home','plate':'01','plate_name':'THE WITNESS','hero':'full'},
    '/book/': {'label':'Book','plate':'02','plate_name':'THE OPEN DOOR','hero':'split'},
    '/road-to-2000/': {'label':'Road to 2,000','plate':'03','plate_name':'THE ROAD','hero':'split'},
    '/writing/': {'label':'Writing','plate':'04','plate_name':'THE WRITING DESK','hero':'split'},
    '/reviews/': {'label':'Reviews','plate':'05','plate_name':'READER MARGINALIA','hero':'split'},
    '/podcasts/': {'label':'Podcasts','plate':'06','plate_name':'THE MICROPHONE','hero':'split'},
    '/about/': {'label':'About','plate':'07','plate_name':'THE AUTHOR AND THE WITNESS','hero':'full'},
    '/buy/': {'label':'Buy','plate':'08','plate_name':'THE OBJECT','hero':'split'},
    '/gazette/': {'label':'Gazette','plate':'09','plate_name':'THE EXTRAORDINARY EDITION','hero':'split'},
    '/evidence-that-i-mattered/': {'label':'Katie Archive','plate':'10','plate_name':'EVIDENCE THAT I MATTERED','hero':'compact'},
    '/meet-katie/': {'label':'Meet Katie','plate':'11','plate_name':'THE GIRL WHO STAYED','hero':'compact'},
    '/meet-shadow/': {'label':'Meet Shadow','plate':'12','plate_name':'THE SILENT SENTRY','hero':'full'},
    '/sample/': {'label':'Read a Sample','plate':'S1','plate_name':'THE QUIET AFTER THE STORM','hero':'compact'},
    '/plates/': {'label':'Table of Plates','plate':'CAT','plate_name':'TABLE OF PLATES','hero':'compact'},
    '/indexes/': {'label':'General Index','plate':'IDX','plate_name':'GENERAL INDEX','hero':'compact'},
    '/press/': {'label':'Press','plate':'P1','plate_name':'PRESS FILE','hero':'compact'},
    '/privacy/': {'label':'Privacy','plate':'COL','plate_name':'COLOPHON','hero':'compact'},
    '/writing/autism-and-identity/': {'label':'Autism and Identity','plate':'04A','plate_name':'AUTISM AND IDENTITY','hero':'compact'},
    '/writing/care-and-love/': {'label':'Care and Love','plate':'04B','plate_name':'CARE AND LOVE','hero':'compact'},
    '/writing/grief-and-survival/': {'label':'Grief and Survival','plate':'04C','plate_name':'GRIEF AND SURVIVAL','hero':'compact'},
    '/writing/field-notes/': {'label':'Field Notes','plate':'04D','plate_name':'FIELD NOTES','hero':'compact'},
    '/writing/the-diagnosis-ceremony/': {'label':'The Diagnosis Ceremony','plate':'04E','plate_name':'THE DIAGNOSIS CEREMONY','hero':'compact'},
    '/writing/losing-your-identity-after-loss/': {'label':'Losing Your Identity After Loss','plate':'04F','plate_name':'LOSING YOUR IDENTITY AFTER LOSS','hero':'compact'},
    '/gazette/latest/': {'label':'Latest Gazette Edition','plate':'09A','plate_name':'THE EARTH HAS RETAINED LEGAL COUNSEL','hero':'compact'},
    '/podcasts/unmasked-late-diagnosis/': {'label':'Unmasked: The Late Diagnosis Conversation','plate':'06A','plate_name':'UNMASKED','hero':'compact'},
    '/podcasts/surviving-the-mask/': {'label':'Surviving the Mask','plate':'06B','plate_name':'SURVIVING THE MASK','hero':'compact'},
    '/podcasts/still-here-conversation/': {'label':'Still Here','plate':'06C','plate_name':'STILL HERE','hero':'compact'},
}

PLATE_LEDGER = [
    ('I','01','The Witness','/'),('II','02','The Open Door','/book/'),('III','03','The Road','/road-to-2000/'),
    ('IV','04','The Writing Desk','/writing/'),('V','05','Reader Marginalia','/reviews/'),('VI','06','The Microphone','/podcasts/'),
    ('VII','07','The Author and the Witness','/about/'),('VIII','08','The Object','/buy/'),('IX','09','The Extraordinary Edition','/gazette/'),
    ('X','10','Evidence That I Mattered','/evidence-that-i-mattered/'),('XI','11','The Girl Who Stayed','/meet-katie/'),
    ('XII','12','The Silent Sentry','/meet-shadow/')
]

# Canonical publication ledger. Defaults above keep the script portable, while this
# file is the single source editors update for navigation and primary plate order.
CONFIG_PATH = ROOT / 'data' / 'site.json'
if CONFIG_PATH.exists():
    _config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    EDITION = _config.get('edition', EDITION)
    NAV = [tuple(item) for item in _config.get('navigation', NAV)]
    PLATE_LEDGER = [(item['roman'], item['number'], item['title'], item['url']) for item in _config.get('plates', [])] or PLATE_LEDGER
    for _roman, _number, _title, _url in PLATE_LEDGER:
        if _url in PAGES:
            PAGES[_url]['plate'] = _number
            PAGES[_url]['plate_name'] = _title.upper()

SOCIALS = [
    ('Instagram','https://www.instagram.com/christophercarazas/'),('Facebook','https://www.facebook.com/christopher.carazas.2025'),
    ('Threads','https://www.threads.com/@christophercarazas'),('X / Twitter','https://twitter.com/christheaspie'),
    ('Bluesky','https://bsky.app/profile/ccarazas.bsky.social'),('Substack','https://ccarazas.substack.com'),
    ('Email','mailto:chris@chriscarazas.com')
]

def route_for(path: Path) -> str:
    rel = path.relative_to(ROOT)
    if rel.name == 'index.html':
        parent = rel.parent.as_posix()
        return '/' if parent == '.' else f'/{parent}/'
    if rel.name == '404.html': return '/404.html'
    return '/' + rel.as_posix()

def make_header(soup: BeautifulSoup, route: str) -> Tag:
    header = soup.new_tag('header', **{'class':'site-header','data-header':''})
    wrap = soup.new_tag('div', **{'class':'shell nav-wrap'})
    brand = soup.new_tag('a', href='/', **{'class':'brand'}); brand.string='Christopher Carazas'; wrap.append(brand)
    toggle = soup.new_tag('button', type='button', **{'class':'nav-toggle','aria-controls':'primary-nav','aria-expanded':'false'})
    sr=soup.new_tag('span', **{'class':'sr-only'}); sr.string='Open menu'; toggle.append(sr)
    for _ in range(3): toggle.append(soup.new_tag('i'))
    wrap.append(toggle)
    nav=soup.new_tag('nav', id='primary-nav', **{'class':'primary-nav','aria-label':'Primary navigation'})
    for label,href in NAV:
        a=soup.new_tag('a',href=href); a.string=label
        if (route==href) or (href!="/" and route.startswith(href) and href not in ['/buy/']): a['aria-current']='page'
        if route=='/buy/' and href=='/buy/': a['aria-current']='page'
        nav.append(a)
    wrap.append(nav)
    cta=soup.new_tag('a',href='/buy/',**{'class':'header-book-cta','data-event':'header_buy_click'}); cta.string='Get the Book'; wrap.append(cta)
    header.append(wrap)
    prog=soup.new_tag('div',**{'class':'nav-progress','aria-hidden':'true'}); prog.append(soup.new_tag('span')); header.append(prog)
    return header

def make_footer(soup: BeautifulSoup) -> Tag:
    footer=soup.new_tag('footer',**{'class':'site-footer'})
    spread=soup.new_tag('div',**{'class':'shell footer-spread'})
    ident=soup.new_tag('div',**{'class':'footer-identity'})
    mono=soup.new_tag('div',**{'class':'footer-monogram'}); mono.string='CJC'; ident.append(mono)
    st=soup.new_tag('strong'); st.string='Christopher Carazas'; ident.append(st)
    p=soup.new_tag('p'); p.string="Author, analyst, and Shadow's administrative staff."; ident.append(p); spread.append(ident)
    nav=soup.new_tag('nav',**{'class':'footer-index','aria-label':'Footer navigation'})
    lab=soup.new_tag('span',**{'class':'catalogue-label'}); lab.string='Index'; nav.append(lab)
    links=NAV + [('Read a Sample','/sample/'),('Substack','https://ccarazas.substack.com/'),('Press','/press/'),('Katie Archive','/evidence-that-i-mattered/'),('Table of Plates','/plates/'),('Meet Katie','/meet-katie/'),('Meet Shadow','/meet-shadow/'),('Privacy','/privacy/')]
    for label,href in links:
        a=soup.new_tag('a',href=href); a.string=label
        if href.startswith('http'): a['target']='_blank'; a['rel']='noopener'
        nav.append(a)
    spread.append(nav); footer.append(spread)
    social=soup.new_tag('div',**{'class':'footer-social shell'})
    for label,href in SOCIALS:
        a=soup.new_tag('a',href=href); a.string=label
        if href.startswith('http'): a['target']='_blank'; a['rel']='noopener'
        social.append(a)
    footer.append(social)
    col=soup.new_tag('div',**{'class':'shell site-colophon'})
    for label,text in [
        (f'Digital edition {EDITION}','Christopher J. Carazas · Sentinel House Press'),
        ('Typography','Oswald · EB Garamond · Courier Prime · original handwriting fragments by Katie'),
        ('Provenance','Kingston, Massachusetts · Personal archive · Revised July 2026 · Responsive collected edition')]:
        d=soup.new_tag('div'); sp=soup.new_tag('span',**{'class':'colophon-label'}); sp.string=label; d.append(sp); pp=soup.new_tag('p'); pp.string=text; d.append(pp); col.append(d)
    footer.append(col)
    bottom=soup.new_tag('div',**{'class':'shell footer-bottom'}); s1=soup.new_tag('span'); s1.append('© '); yr=soup.new_tag('span',**{'data-year':''}); s1.append(yr); s1.append(' Christopher Carazas'); bottom.append(s1); s2=soup.new_tag('span'); s2.string='Sentinel House Press'; bottom.append(s2); footer.append(bottom)
    return footer

def breadcrumbs_for(route: str):
    if route.startswith('/writing/') and route != '/writing/': return [('Home','/'),('Writing','/writing/'),(PAGES.get(route,{}).get('label','Essay'),None)]
    if route.startswith('/podcasts/') and route != '/podcasts/': return [('Home','/'),('Podcasts','/podcasts/'),(PAGES.get(route,{}).get('label','Episode'),None)]
    if route == '/gazette/latest/': return [('Home','/'),('Gazette','/gazette/'),('Latest Edition',None)]
    if route in ['/meet-katie/','/evidence-that-i-mattered/']: return [('Home','/'),('About','/about/'),(PAGES[route]['label'],None)]
    if route == '/meet-shadow/': return [('Home','/'),('About','/about/'),('Meet Shadow',None)]
    return [('Home','/'),(PAGES.get(route,{}).get('label','Page'),None)] if route!='/' else []

def replace_breadcrumb(soup: BeautifulSoup, route: str):
    old=soup.select_one('nav.breadcrumbs')
    crumbs=breadcrumbs_for(route)
    if not crumbs:
        if old: old.decompose()
        return
    nav=soup.new_tag('nav',**{'class':'breadcrumbs shell','aria-label':'Breadcrumb'}); ol=soup.new_tag('ol')
    for label,href in crumbs:
        li=soup.new_tag('li')
        if href:
            a=soup.new_tag('a',href=href); a.string=label; li.append(a)
        else:
            li['aria-current']='page'; li.string=label
        ol.append(li)
    nav.append(ol)
    if old: old.replace_with(nav)
    else:
        main=soup.find('main'); main.insert(0,nav)

def breadcrumb_schema(route: str):
    crumbs=breadcrumbs_for(route)
    if not crumbs: return None
    items=[]
    for i,(name,href) in enumerate(crumbs,1):
        item={'@type':'ListItem','position':i,'name':name}
        item['item']=SITE+(href if href else route)
        items.append(item)
    return {'@type':'BreadcrumbList','itemListElement':items}

def base_person():
    return {'@type':'Person','@id':SITE+'/#christopher-carazas','name':'Christopher J. Carazas','url':SITE+'/',
            'jobTitle':['Author','Social Impact Analyst'],
            'image':SITE+'/assets/images/christopher-carazas-shadow-kingston.webp',
            'email':'mailto:chris@chriscarazas.com',
            'sameAs':[u for _,u in SOCIALS if u.startswith('http')]}

def book_schema():
    return {'@type':'Book','@id':SITE+'/book/#book','name':"Now That I'm Still Here: A Memoir of Ruin and Resurrection",
            'url':SITE+'/book/','author':{'@id':SITE+'/#christopher-carazas'},'publisher':{'@type':'Organization','name':'Sentinel House Press'},
            'datePublished':'2025-09-01','numberOfPages':204,'inLanguage':'en','genre':['Memoir','Autism','Mental Health','Grief'],
            'description':'A literary memoir about late-diagnosed autism, masking, emotional abuse, psychiatric collapse, grief, and choosing life after survival stops feeling like enough.',
            'image':SITE+'/assets/images/now-that-im-still-here-book-cover.webp',
            'workExample':[
                {'@type':'Book','bookFormat':'https://schema.org/Hardcover','isbn':'979-8-218-75064-0'},
                {'@type':'Book','bookFormat':'https://schema.org/Paperback','isbn':'979-8-218-76118-9'},
                {'@type':'Book','bookFormat':'https://schema.org/EBook','isbn':'979-8-218-75486-0'}]}

def set_schema(soup: BeautifulSoup, route: str):
    for sc in soup.find_all('script',attrs={'type':'application/ld+json'}): sc.decompose()
    graph=[]
    if route=='/':
        graph=[{'@type':'WebSite','@id':SITE+'/#website','url':SITE+'/','name':'Christopher Carazas','inLanguage':'en'},base_person(),{'@type':'Organization','@id':SITE+'/#sentinel-house-press','name':'Sentinel House Press','url':SITE+'/'},book_schema()]
    elif route in ['/book/','/buy/','/sample/']:
        graph=[book_schema()]
        if route=='/buy/':
            graph.append({'@type':'Product','name':"Now That I'm Still Here, Signed Copy",'image':SITE+'/assets/images/now-that-im-still-here-book-cover.webp','brand':{'@type':'Brand','name':'Sentinel House Press'},'offers':{'@type':'Offer','url':'https://book.stripe.com/00w9AS358bIfbsp53p28802','availability':'https://schema.org/LimitedAvailability','price':'19.99','priceCurrency':'USD'}})
        if route=='/sample/':
            graph.append({'@type':'Article','headline':'The Quiet After the Storm: Read a Sample','datePublished':'2025-09-01','author':{'@id':SITE+'/#christopher-carazas'},'isPartOf':{'@id':SITE+'/book/#book'},'mainEntityOfPage':SITE+'/sample/'})
    elif route=='/plates/':
        graph=[{'@type':'CollectionPage','name':'Table of Plates','url':SITE+'/plates/','description':'A catalogue of the principal images, objects, and narrative thresholds in the digital collected edition.',
                'hasPart':[{'@type':'CreativeWork','position':i+1,'name':title,'url':SITE+url,'identifier':plate} for i,(_,plate,title,url) in enumerate(PLATE_LEDGER)]}]
    elif route.startswith('/writing/') and route not in ['/writing/','/writing/autism-and-identity/','/writing/care-and-love/','/writing/grief-and-survival/','/writing/field-notes/']:
        title=PAGES[route]['label']; graph=[{'@type':'Article','headline':title,'url':SITE+route,'author':{'@id':SITE+'/#christopher-carazas'},'datePublished':'2026-07-01' if 'diagnosis' in route else '2026-06-30','image':SITE+'/assets/images/writing-desk-og.jpg'}]
    elif route=='/gazette/latest/':
        graph=[{'@type':'Article','headline':'The Plymouth Sentinel & Canine Gazette','url':SITE+route,'author':{'@id':SITE+'/#christopher-carazas'},'datePublished':'2026-06-28','image':SITE+'/assets/images/shadow-bow-tie-sky.webp'}]
    else:
        label=PAGES.get(route,{}).get('label') or (soup.title.get_text().split('|')[0].strip() if soup.title else 'Page')
        graph=[{'@type':'WebPage','name':label,'url':SITE+route,'isPartOf':{'@id':SITE+'/#website'},'dateModified':'2026-07-02'}]
        if route=='/about/': graph[0]={'@type':'ProfilePage','name':'About Christopher Carazas','url':SITE+route,'mainEntity':base_person(),'dateModified':'2026-07-02'}
    bc=breadcrumb_schema(route)
    if bc: graph.append(bc)
    script=soup.new_tag('script',type='application/ld+json'); script.string=json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False,separators=(',',':'))
    head=soup.head; defer=head.find('script',src='/site.js')
    if defer: defer.insert_before(script)
    else: head.append(script)

def classify_figures(soup: BeautifulSoup):
    for fig in soup.find_all('figure'):
        classes=set(fig.get('class',[]))
        if any(c in classes for c in ['home-art-plate','book-art-plate','road-art-plate','writing-art-plate','reviews-art-plate','podcast-art-plate','about-art-plate','buy-art-plate','gazette-art-plate']):
            classes.add('media--cinematic')
        elif any(c in classes for c in ['artifact-card','artifact-entry','card-object','existence-card']):
            classes.add('media--artifact')
        elif any('contact' in c for c in classes): classes.add('media--contact')
        elif fig.find('img'): classes.add('media--museum')
        fig['class']=sorted(classes)

def normalize_page(path: Path):
    route=route_for(path)
    soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    # shared structure
    if soup.body:
        soup.body['data-edition']=EDITION
        info=PAGES.get(route)
        if info:
            soup.body['data-folio']=info['plate']
            cls=set(soup.body.get('class',[])); cls.add(f"hero-{info['hero']}"); soup.body['class']=sorted(cls)
    if route not in ['/books/','/impact/','/404.html']:
        old=soup.find('header',class_='site-header')
        new=make_header(soup,route)
        if old: old.replace_with(new)
        elif soup.body: soup.body.insert(1,new)
        oldf=soup.find('footer',class_='site-footer'); newf=make_footer(soup)
        if oldf: oldf.replace_with(newf)
        elif soup.body: soup.body.append(newf)
        replace_breadcrumb(soup,route)
    # CSS cache and edition
    for link in soup.find_all('link',href=re.compile(r'^/site\.css')): link['href']=f'/site.css?v={CSS_VERSION}'
    for txt in soup.find_all(string=re.compile(r'Digital edition\s+[IVXLCDM]+',re.I)):
        txt.replace_with(re.sub(r'Digital edition\s+[IVXLCDM]+',f'Digital edition {EDITION}',txt,flags=re.I))
    # page plate labels and hero classes
    info=PAGES.get(route)
    if info:
        hero=soup.select_one('section.art-hero, section.archive-hero, section.meet-katie-hero, section.meet-shadow-hero, section.ink-section.plate-catalogue-hero')
        if hero:
            hcls=set(hero.get('class',[])); hcls.add(f"hero--{info['hero']}"); hero['class']=sorted(hcls)
            fol=hero.select_one('.folio')
            if fol: fol.string=f"PLATE {info['plate']} · {info['plate_name']}"
    # ornaments use one family
    for orn in soup.select('.printer-ornament'): orn.string='❦'
    classify_figures(soup)
    # ensure narrative drop caps only on selected prose, never headings
    for el in soup.select('h1,h2,h3,.display,.display-hero'): 
        cls=set(el.get('class',[])); cls.add('no-dropcap'); el['class']=sorted(cls)
    if route in ['/meet-katie/','/meet-shadow/','/about/','/sample/']:
        first=soup.select_one('main section:not(.art-hero) p:not(.eyebrow):not(.folio)')
        if first:
            cls=set(first.get('class',[])); cls.add('narrative-dropcap'); first['class']=sorted(cls)
    set_schema(soup,route)
    path.write_text(str(soup),encoding='utf-8')

for p in sorted(ROOT.rglob('*.html')):
    normalize_page(p)

# Plate ledger page
plates=ROOT/'plates/index.html'; soup=BeautifulSoup(plates.read_text(),'html.parser')
index=soup.select_one('.full-plate-index')
if index:
    # preserve wrapper, rebuild all list-like content
    for child in list(index.children):
        if isinstance(child,Tag) and child.name not in ['div']:
            child.decompose()
    ol=index.find('ol')
    if not ol:
        ol=soup.new_tag('ol',**{'class':'plate-ledger-list'}); index.append(ol)
    else: ol.clear(); ol['class']='plate-ledger-list'
    for roman,num,title,url in PLATE_LEDGER:
        li=soup.new_tag('li'); a=soup.new_tag('a',href=url)
        r=soup.new_tag('span',**{'class':'plate-roman'}); r.string=roman
        t=soup.new_tag('span',**{'class':'plate-title'}); t.string=title
        dots=soup.new_tag('span',**{'class':'plate-dots','aria-hidden':'true'}); dots.string=''
        n=soup.new_tag('span',**{'class':'plate-number'}); n.string=num
        a.extend([r,t,dots,n]); li.append(a); ol.append(li)
plates.write_text(str(soup),encoding='utf-8')

# Home conversion hierarchy + copy trim
p=ROOT/'index.html'; soup=BeautifulSoup(p.read_text(),'html.parser')
hero=soup.select_one('.home-title-block .hero-actions')
if hero:
    hero.clear()
    a=soup.new_tag('a',href='https://www.lulu.com/search?adult_audience_rating=00&page=1&pageSize=10&q=Christopher+carazas&sortBy=RELEVANCE',target='_blank',rel='noopener',**{'class':'button button-amber','data-event':'direct_book_click'}); a.string='Buy Direct'; hero.append(a)
    b=soup.new_tag('a',href='/sample/',**{'class':'button button-outline','data-event':'sample_open_click'}); b.string='Read a Sample'; hero.append(b)
    c=soup.new_tag('a',href='https://books2read.com/u/bz0n1Z',target='_blank',rel='noopener',**{'class':'hero-retailer-link','data-event':'retailer_click'}); c.string='Other retailers →'; hero.append(c)
# trim premise copy without losing core
prem=soup.select_one('.home-book-premise')
if prem:
    paras=prem.select('.premise-copy p, p')
    # identify by text and replace
    for para in paras:
        t=para.get_text(' ',strip=True)
        if t.startswith('I grew up between countries'):
            para.string='I grew up between countries, languages, churches, and expectations, learning early that belonging often meant performing. By adulthood, I could read a room, manage a crisis, and disappear in plain sight. People called it maturity. I was slowly evacuating my own personality.'
        elif t.startswith('Then the marriage collapsed'):
            para.string='Then the marriage collapsed. The mask cracked. I was diagnosed with autism as an adult. In the wreckage, Shadow kept expecting breakfast, Katie loved me without asking me to become smaller, and writing became a door.'
        elif t.startswith('This is not a victory lap'):
            para.string='This is not a victory lap. It is what happens after collapse, when you are alive but not yet convinced that life belongs to you, and the people who stay make staying imaginable.'
p.write_text(str(soup),encoding='utf-8')

# Book: sample-forward hero and closing
p=ROOT/'book/index.html'; soup=BeautifulSoup(p.read_text(),'html.parser')
acts=soup.select_one('.book-title-block .hero-actions')
if acts:
    acts.clear()
    a=soup.new_tag('a',href='/sample/',**{'class':'button button-amber','data-event':'sample_open_click'}); a.string='Read the Opening Pages'; acts.append(a)
    b=soup.new_tag('a',href='/buy/',**{'class':'button button-outline','data-event':'book_buy_page_click'}); b.string='Choose an Edition'; acts.append(b)
closing=soup.select_one('.enter-story .action-stack')
if closing:
    closing.clear(); a=soup.new_tag('a',href='/sample/',**{'class':'button button-amber','data-event':'sample_open_click'}); a.string='Begin with the Prologue'; closing.append(a)
    b=soup.new_tag('a',href='/buy/',**{'class':'text-link-light','data-event':'book_buy_page_click'}); b.string='Choose an edition →'; closing.append(b)
p.write_text(str(soup),encoding='utf-8')

# Buy: trust details and reader proof
p=ROOT/'buy/index.html'; soup=BeautifulSoup(p.read_text(),'html.parser')
edition=soup.select_one('.edition-room')
if edition and not soup.select_one('.purchase-facts'):
    facts=BeautifulSoup('''<section class="purchase-facts ink-section" data-reveal><div class="shell purchase-facts-grid"><div><span class="folio folio-light">BOOK RECORD</span><h2>What arrives.</h2><p>A 204-page first edition from Sentinel House Press. Prices and delivery windows for printer and retailer orders appear at checkout.</p></div><dl><div><dt>Formats</dt><dd>Paperback · Hardcover · eBook</dd></div><div><dt>Paperback ISBN</dt><dd>979-8-218-76118-9</dd></div><div><dt>Hardcover ISBN</dt><dd>979-8-218-75064-0</dd></div><div><dt>eBook ISBN</dt><dd>979-8-218-75486-0</dd></div><div><dt>Signed copy</dt><dd>$19.99 USD · limited availability</dd></div><div><dt>Campaign</dt><dd>$1 from each direct signed copy is committed to the Road to 2,000.</dd></div></dl></div></section>''','html.parser').section
    edition.insert_after(facts)
if not soup.select_one('.conversion-proof'):
    target=soup.select_one('.purchase-facts') or edition
    proof=BeautifulSoup('''<section class="paper-section conversion-proof" data-reveal><div class="shell conversion-proof-grid"><blockquote>It does not just explain masking. It shows the cost.<cite>Rachel K. · Educator</cite></blockquote><blockquote>I did not expect to survive this year. This book met me where I was and did not let go.<cite>Anonymous reader</cite></blockquote><a class="text-link" href="/reviews/">Read the full reader archive →</a></div></section>''','html.parser').section
    target.insert_after(proof)
p.write_text(str(soup),encoding='utf-8')

# Road specificity and conversion labels
p=ROOT/'road-to-2000/index.html'; soup=BeautifulSoup(p.read_text(),'html.parser')
for el in soup.find_all(string=re.compile(r'Updated ledger · 212 of 2,000')): el.replace_with('Updated July 1, 2026 · 212 of 2,000')
archive=soup.select_one('.campaign-archive')
if archive:
    firstp=archive.find('p')
    if firstp: firstp.string='The public record holds dated totals, the $1-per-direct-signed-copy commitment, future donation receipts, and calculation notes in the same place.'
for a in soup.select('.road-actions a'):
    txt=a.get_text(' ',strip=True).lower()
    if 'signed' in txt: a['data-event']='signed_copy_click'
    elif 'retailer' in txt: a['data-event']='retailer_click'
    elif 'direct' in txt: a['data-event']='direct_book_click'
p.write_text(str(soup),encoding='utf-8')

# Writing: internal latest essay cards first, Substack remains continuation
p=ROOT/'writing/index.html'; soup=BeautifulSoup(p.read_text(),'html.parser')
rss=soup.select_one('#substack-posts')
if rss:
    cards=[
        ('Jul 1, 2026','The Diagnosis Ceremony','A late autism diagnosis, a twelve-question intake form, and the hidden cost of appearing to need minimal support.','/writing/the-diagnosis-ceremony/'),
        ('Jun 30, 2026','Losing Your Identity After Loss','A conversation about grief, identity, and the disorienting middle after loss.','/writing/losing-your-identity-after-loss/'),
        ('Jun 28, 2026','The Plymouth Sentinel & Canine Gazette','A Victorian canine newspaper investigates environmental absurdity and the failure of human supervision.','/gazette/latest/')]
    rss.clear()
    for date,title,desc,url in cards:
        art=soup.new_tag('article',**{'class':'rss-card'}); sp=soup.new_tag('span'); sp.string=date; art.append(sp); h=soup.new_tag('h3'); h.string=title; art.append(h); pp=soup.new_tag('p'); pp.string=desc; art.append(pp); aa=soup.new_tag('a',href=url); aa.string='Read the preview →'; art.append(aa); rss.append(art)
status=soup.select_one('#feed-status')
if status: status.string='The site keeps a static editorial selection. The live Substack feed refreshes the archive when available.'
p.write_text(str(soup),encoding='utf-8')

print('V6.6 build transformations applied.')
