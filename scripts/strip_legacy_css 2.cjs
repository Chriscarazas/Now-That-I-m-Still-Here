#!/usr/bin/env node
const fs=require('fs');
const postcss=require('/opt/nvm/versions/node/v22.16.0/lib/node_modules/postcss/lib/postcss.js');
const path=require('path');
const rootDir=path.resolve(__dirname,'..');
const src=path.join(rootDir,'styles','site-source.css');
let text=fs.readFileSync(src,'utf8');
const marker='/* ============ V6.6 CONSOLIDATED EDITORIAL SYSTEM ============ */';
const idx=text.indexOf(marker);
if(idx<0) throw new Error('V6.6 marker missing');
const legacy=text.slice(0,idx); const modern=text.slice(idx);
const ast=postcss.parse(legacy);
const controlled=[
  '.site-header','.nav-wrap','.brand','.primary-nav','.nav-toggle','.header-book-cta','.nav-progress',
  '.art-hero','.hero-canvas','.home-art-hero','.home-hero','.home-title-block','.home-art-plate','.home-cover-plate','.home-note','.home-film-meta',
  '.book-art-hero','.book-title-block','.book-art-plate','.book-cover-overlap','.book-margin',
  '.road-art-hero','.road-title-block','.road-art-plate','.road-margin',
  '.writing-art-hero','.writing-title-block','.writing-art-plate','.writing-margin',
  '.reviews-art-hero','.reviews-title-block','.reviews-art-plate',
  '.podcast-art-hero','.podcast-title-block','.podcast-art-plate',
  '.buy-art-hero','.buy-title-block','.buy-art-plate',
  '.gazette-art-hero','.gazette-title-block','.gazette-art-plate',
  '.about-art-hero','.about-hero','.about-title-block','.about-art-plate','.about-cinematic-plate','.about-archive-overlay','.measurement-rule'
];
ast.walkRules(r=>{if(r.selector.includes('::first-letter')||controlled.some(x=>r.selector.includes(x)))r.remove()});
ast.walkAtRules(at=>{if(at.nodes&&at.nodes.length===0)at.remove()});
fs.writeFileSync(src,ast.toString().trim()+'\n\n'+modern.trim()+'\n');
console.log('Legacy header, hero, and drop-cap rules removed; canonical V6.6 system retained.');
