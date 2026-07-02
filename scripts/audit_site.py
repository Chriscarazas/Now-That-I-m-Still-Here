#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json, re, sys, xml.etree.ElementTree as ET
import tinycss2

ROOT=Path(__file__).resolve().parents[1]
errors=[]; warnings=[]
html_pages=sorted(ROOT.rglob('*.html'))
config=json.loads((ROOT/'data/site.json').read_text())
expected_nav=[href for _,href in config['navigation']]
main_plates={item['url']:item['number'] for item in config['plates']}
seen_ids={}


def route_for(page:Path)->str:
    rel=page.relative_to(ROOT)
    if rel.name=='index.html':
        parent=rel.parent.as_posix()
        return '/' if parent=='.' else f'/{parent}/'
    return '/' + rel.as_posix()

for page in html_pages:
    rel=page.relative_to(ROOT); route=route_for(page)
    soup=BeautifulSoup(page.read_text(encoding='utf-8'),'html.parser')
    noindex=bool(soup.find('meta',attrs={'name':'robots','content':re.compile('noindex',re.I)}))
    if not soup.title or not soup.title.get_text(strip=True): errors.append(f'{rel}: missing title')
    if not noindex and page.name!='404.html':
        for label,tag in [('description',soup.find('meta',attrs={'name':'description'})),('canonical',soup.find('link',rel='canonical'))]:
            if not tag: errors.append(f'{rel}: missing {label}')
        if len(soup.find_all('h1'))!=1: errors.append(f'{rel}: expected one H1, found {len(soup.find_all("h1"))}')
        if not soup.find('main'): errors.append(f'{rel}: missing main')
        if not soup.find('a',class_='skip-link'): errors.append(f'{rel}: missing skip link')
    # Shared navigation consistency.
    if route not in ['/books/','/impact/','/404.html']:
        nav=soup.select_one('#primary-nav')
        if not nav: errors.append(f'{rel}: missing primary navigation')
        else:
            links=[a.get('href') for a in nav.find_all('a',recursive=False)]
            if links!=expected_nav: errors.append(f'{rel}: navigation mismatch {links}')
        cta=soup.select_one('.header-book-cta[href="/buy/"]') or soup.select_one('.header-book-cta.getbook[data-getbook]')
        if not cta: errors.append(f'{rel}: missing header book CTA')
    # Plate consistency.
    if route in main_plates:
        expected=main_plates[route]
        if soup.body.get('data-folio')!=expected: errors.append(f'{rel}: body folio {soup.body.get("data-folio")} != {expected}')
        hero=soup.select_one('section.art-hero,section.archive-hero,section.meet-katie-hero,section.meet-shadow-hero')
        if hero:
            fol=hero.select_one('.folio')
            if fol and f'PLATE {expected}' not in fol.get_text(' ',strip=True): errors.append(f'{rel}: visible folio does not match {expected}')
    # IDs and anchors.
    ids=[tag.get('id') for tag in soup.find_all(id=True)]
    duplicates={i for i in ids if ids.count(i)>1}
    if duplicates: errors.append(f'{rel}: duplicate IDs {sorted(duplicates)}')
    idset=set(ids)
    for anchor in soup.find_all('a',href=True):
        href=anchor['href']
        if href.startswith('#') and href[1:] not in idset: errors.append(f'{rel}: broken local anchor {href}')
        if href.startswith('/') and not href.startswith('//'):
            clean=href.split('#',1)[0].split('?',1)[0]
            if clean:
                target=ROOT/clean.lstrip('/')
                if clean.endswith('/'): target=target/'index.html'
                if not target.exists(): errors.append(f'{rel}: missing internal link {href}')
    # Images and canonical presentation categories.
    for img in soup.find_all('img'):
        src=img.get('src','')
        if not img.has_attr('alt'): errors.append(f'{rel}: image missing alt {src}')
        if src.startswith('/') and not (ROOT/src.lstrip('/')).exists(): errors.append(f'{rel}: missing image {src}')
        if not img.get('width') or not img.get('height'): errors.append(f'{rel}: image missing dimensions {src}')
        fig=img.find_parent('figure')
        if fig and not any(c in fig.get('class',[]) for c in ['media--cinematic','media--museum','media--artifact','media--contact']):
            warnings.append(f'{rel}: figure lacks canonical media class {src}')
    for source in soup.find_all('source'):
        for candidate in source.get('srcset','').split(','):
            src=candidate.strip().split(' ')[0]
            if src.startswith('/') and not (ROOT/src.lstrip('/')).exists(): errors.append(f'{rel}: missing srcset asset {src}')
    for tag,attr in [('link','href'),('script','src')]:
        for node in soup.find_all(tag):
            val=node.get(attr,'')
            if val.startswith('/') and not val.startswith('//'):
                clean=val.split('?',1)[0]; target=ROOT/clean.lstrip('/')
                if clean.endswith('/'): target=target/'index.html'
                if not target.exists(): errors.append(f'{rel}: missing {tag} asset {val}')
    # JSON-LD validity and duplicate breadcrumb protection.
    breadcrumb_count=0
    for script in soup.find_all('script',attrs={'type':'application/ld+json'}):
        try:
            data=json.loads(script.string or '')
            nodes=data.get('@graph',[]) if isinstance(data,dict) else []
            breadcrumb_count+=sum(1 for n in nodes if isinstance(n,dict) and n.get('@type')=='BreadcrumbList')
        except Exception as exc: errors.append(f'{rel}: invalid JSON-LD {exc}')
    if breadcrumb_count>1: errors.append(f'{rel}: duplicate BreadcrumbList schema')
    # Cache key and public contact consistency.
    css_links=[l.get('href','') for l in soup.find_all('link',rel='stylesheet') if '/site.css' in l.get('href','')]
    if css_links and any('v=6.6' not in l for l in css_links): errors.append(f'{rel}: stale CSS cache key')
    emails=set(re.findall(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',page.read_text()))
    if emails and emails!={'ccarazaswrites@gmail.com'}: errors.append(f'{rel}: unexpected public email {emails}')

# Required files and data.
for name in ['sitemap.xml','image-sitemap.xml','robots.txt','site.css','site.js','data/substack-posts.json','data/site.json','scripts/build_site.py','scripts/build_css.cjs','scripts/build_sitemaps.py']:
    if not (ROOT/name).exists(): errors.append(f'missing {name}')
try:
    data=json.loads((ROOT/'data/substack-posts.json').read_text())
    if not data.get('posts'): errors.append('Substack cache contains no posts')
    for post in data.get('posts',[]):
        if post.get('title') in {'The Diagnosis Ceremony','Losing Your Identity After Loss','The Plymouth Sentinel & Canine Gazette'} and not post.get('internalPath'):
            errors.append(f'RSS post missing internalPath: {post.get("title")}')
except Exception as exc: errors.append(f'invalid Substack cache: {exc}')
for xmlname in ['sitemap.xml','image-sitemap.xml']:
    try: ET.parse(ROOT/xmlname)
    except Exception as exc: errors.append(f'invalid {xmlname}: {exc}')

# CSS syntax and maintainability report.
css=(ROOT/'site.css').read_text()
parsed=tinycss2.parse_stylesheet(css,skip_comments=True,skip_whitespace=True)
for token in parsed:
    if token.type=='error': errors.append(f'CSS parse error: {token.message}')
important=len(re.findall(r'!important',css,re.I))
media=len(re.findall(r'@media',css))
versioned=len(re.findall(r'\.(?:[\w-]*v\d+[\w-]*)',css))
if important>250: warnings.append(f'Production CSS still has {important} !important declarations')
if media>70: warnings.append(f'Production CSS still has {media} media blocks')
if versioned: warnings.append(f'Production CSS contains {versioned} versioned class references')

# Sitemap coverage.
ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
locs={e.text.replace('https://chriscarazas.com','') or '/' for e in ET.parse(ROOT/'sitemap.xml').findall('.//s:loc',ns)}
for required in ['/sample/','/writing/the-diagnosis-ceremony/','/writing/losing-your-identity-after-loss/','/gazette/latest/']:
    if required not in locs: errors.append(f'sitemap missing {required}')

for item in sorted(set(warnings)): print('WARNING:',item)
for item in sorted(set(errors)): print('ERROR:',item)
print(f'Checked {len(html_pages)} HTML pages: {len(set(errors))} errors, {len(set(warnings))} warnings.')
print(f'Production CSS: {len(css.encode())} bytes, {media} media blocks, {important} !important declarations.')
sys.exit(1 if errors else 0)
