#!/usr/bin/env node
const fs=require('fs');
const path=require('path');
const postcss=require('postcss');
const rootDir=path.resolve(__dirname,'..');
const sourcePath=path.join(rootDir,'styles','site-source.css');
const outPath=path.join(rootDir,'site.css');
const css=fs.readFileSync(sourcePath,'utf8');
const usedClasses=new Set(['is-loaded','is-visible','open','new-window-note','sr-only']);
const usedIds=new Set();
const htmlFiles=[];
function walk(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){if(entry.name.startsWith('.')||entry.name==='node_modules'||entry.name==='styles')continue;const full=path.join(dir,entry.name);if(entry.isDirectory())walk(full);else if(entry.name.endsWith('.html'))htmlFiles.push(full)}}
walk(rootDir);
for(const file of htmlFiles){const text=fs.readFileSync(file,'utf8');for(const m of text.matchAll(/class=["']([^"']+)["']/g))for(const c of m[1].split(/\s+/))if(c)usedClasses.add(c);for(const m of text.matchAll(/id=["']([^"']+)["']/g))usedIds.add(m[1])}
const js=fs.readFileSync(path.join(rootDir,'site.js'),'utf8');
for(const m of js.matchAll(/classList\.add\(["']([\w-]+)/g))usedClasses.add(m[1]);
for(const m of js.matchAll(/className\s*=\s*["']([^"']+)/g))for(const c of m[1].split(/\s+/))usedClasses.add(c);
for(const m of js.matchAll(/getElementById\(["']([^"']+)/g))usedIds.add(m[1]);
function splitSelectors(s){const out=[];let cur='',depth=0,quote='';for(const ch of s){if(quote){cur+=ch;if(ch===quote)quote='';continue}if(ch==='"'||ch==="'"){quote=ch;cur+=ch;continue}if(ch==='('||ch==='[')depth++;if(ch===')'||ch===']')depth=Math.max(0,depth-1);if(ch===','&&depth===0){if(cur.trim())out.push(cur.trim());cur=''}else cur+=ch}if(cur.trim())out.push(cur.trim());return out}
function selectorUsed(sel){if(sel.includes('[data-')||sel.includes('[aria-')||sel.includes(':root')||sel.includes('::selection'))return true;const classes=[...sel.matchAll(/\.([_a-zA-Z][\w-]*)/g)].map(m=>m[1]);const ids=[...sel.matchAll(/#([_a-zA-Z][\w-]*)/g)].map(m=>m[1]);if(classes.some(c=>!usedClasses.has(c)))return false;if(ids.some(i=>!usedIds.has(i)))return false;return true}
const ast=postcss.parse(css,{from:sourcePath});
ast.walkComments(c=>c.remove());
ast.walkRules(rule=>{if(rule.parent&&rule.parent.type==='atrule'&&/keyframes$/i.test(rule.parent.name))return;const kept=splitSelectors(rule.selector).filter(selectorUsed);if(!kept.length)rule.remove();else rule.selector=kept.join(',')});
function dedupe(container){const seen=new Map();const nodes=[...(container.nodes||[])];for(let i=nodes.length-1;i>=0;i--){const n=nodes[i];if(n.type==='rule'){const key=n.selector+'{'+(n.nodes||[]).map(d=>d.toString()).join(';')+'}';if(seen.has(key))n.remove();else seen.set(key,true)}if(n.nodes)dedupe(n)}}
dedupe(ast);
ast.walkAtRules(at=>{if(at.nodes&&at.nodes.length===0)at.remove()});
const animationNames=new Set();ast.walkDecls(d=>{if(d.prop==='animation-name')for(const n of d.value.split(','))animationNames.add(n.trim());if(d.prop==='animation'){for(const token of d.value.split(/\s|,/))if(/^[A-Za-z_][\w-]*$/.test(token)&&!['ease','linear','infinite','forwards','both','none','normal','reverse','alternate'].includes(token))animationNames.add(token)}});ast.walkAtRules(at=>{if(/keyframes$/i.test(at.name)&&!animationNames.has(at.params.trim()))at.remove()});
let output=ast.toString();
fs.writeFileSync(outPath,output);
console.log(JSON.stringify({htmlFiles:htmlFiles.length,sourceBytes:Buffer.byteLength(css),outputBytes:Buffer.byteLength(output),classes:usedClasses.size},null,2));
