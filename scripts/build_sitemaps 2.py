#!/usr/bin/env python3
from pathlib import Path
from bs4 import BeautifulSoup
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace
from datetime import date
import re
ROOT=Path(__file__).resolve().parents[1]
BASE='https://chriscarazas.com'
TODAY='2026-07-02'

register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
register_namespace('image', 'http://www.google.com/schemas/sitemap-image/1.1')
NS='http://www.sitemaps.org/schemas/sitemap/0.9'
IMG='http://www.google.com/schemas/sitemap-image/1.1'

def route(p:Path)->str:
    rel=p.relative_to(ROOT)
    if rel.name=='index.html':
        parent=rel.parent.as_posix()
        return '/' if parent=='.' else f'/{parent}/'
    return '/' + rel.as_posix()

pages=[]
for p in sorted(ROOT.rglob('*.html')):
    if p.name=='404.html': continue
    soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    robots=soup.find('meta',attrs={'name':'robots'})
    if robots and 'noindex' in robots.get('content','').lower(): continue
    canonical=soup.find('link',rel='canonical')
    url=canonical.get('href') if canonical else BASE+route(p)
    r=route(p)
    if r in ['/books/','/impact/']: continue
    priority='1.0' if r=='/' else '0.9' if r in ['/book/','/buy/','/sample/','/writing/'] else '0.8' if r in ['/road-to-2000/','/reviews/','/podcasts/','/about/','/gazette/'] else '0.6'
    images=[]; seen=set()
    for img in soup.find_all('img'):
        src=img.get('src','')
        if not src.startswith('/assets/images/'): continue
        if src.endswith('.svg') or 'icon-' in src or 'favicon' in src or 'apple-touch' in src: continue
        # Prefer a stable 1200/1440 source where present.
        candidate=src
        srcset=''
        picture=img.find_parent('picture')
        if picture:
            source=picture.find('source',attrs={'type':'image/webp'})
            if source: srcset=source.get('srcset','')
        if srcset:
            opts=[]
            for item in srcset.split(','):
                parts=item.strip().split()
                if parts and parts[0].startswith('/assets/images/'):
                    width=int(parts[1][:-1]) if len(parts)>1 and parts[1].endswith('w') and parts[1][:-1].isdigit() else 0
                    opts.append((width,parts[0]))
            if opts: candidate=max(opts)[1]
        if candidate in seen: continue
        seen.add(candidate)
        alt=img.get('alt','').strip()
        if not alt: continue
        images.append((BASE+candidate,alt))
    pages.append((url,r,priority,images))

urlset=Element(f'{{{NS}}}urlset')
for url,r,priority,images in pages:
    u=SubElement(urlset,f'{{{NS}}}url')
    SubElement(u,f'{{{NS}}}loc').text=url
    SubElement(u,f'{{{NS}}}lastmod').text=TODAY
    SubElement(u,f'{{{NS}}}priority').text=priority
ElementTree(urlset).write(ROOT/'sitemap.xml',encoding='utf-8',xml_declaration=True)

imgset=Element(f'{{{NS}}}urlset')
for url,r,priority,images in pages:
    if not images: continue
    u=SubElement(imgset,f'{{{NS}}}url'); SubElement(u,f'{{{NS}}}loc').text=url
    for loc,caption in images[:20]:
        ii=SubElement(u,f'{{{IMG}}}image')
        SubElement(ii,f'{{{IMG}}}loc').text=loc
        SubElement(ii,f'{{{IMG}}}caption').text=caption
ElementTree(imgset).write(ROOT/'image-sitemap.xml',encoding='utf-8',xml_declaration=True)
print(f'Wrote {len(pages)} sitemap URLs and {sum(bool(i) for *_,i in pages)} image-bearing pages')
