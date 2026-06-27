// NAV scroll
const nav=document.getElementById('mainNav');
window.addEventListener('scroll',()=>nav.classList.toggle('scrolled',window.scrollY>60));

// QUOTE SLIDESHOW
(function(){
  const slides = document.querySelectorAll('#qsSlides .qs-slide');
  if(!slides.length) return;
  const dotsContainer = document.getElementById('qsDots');
  const prevBtn = document.getElementById('qsPrev');
  const nextBtn = document.getElementById('qsNext');
  let current = 0, timer;

  // Create dots
  slides.forEach((_,i)=>{
    const d = document.createElement('button');
    d.className = 'qs-dot' + (i===0?' active':'');
    d.addEventListener('click',()=>{ goTo(i); resetTimer(); });
    dotsContainer.appendChild(d);
  });

  function goTo(n){
    slides[current].classList.remove('active');
    dotsContainer.children[current].classList.remove('active');
    current = (n + slides.length) % slides.length;
    slides[current].classList.add('active');
    dotsContainer.children[current].classList.add('active');
  }

  function startTimer(){ timer = setInterval(()=>goTo(current+1), 4500); }
  function resetTimer(){ clearInterval(timer); startTimer(); }

  const section = document.querySelector('.qs-section');
  if(section){
    section.addEventListener('mouseenter',()=>clearInterval(timer));
    section.addEventListener('mouseleave', startTimer);
  }

  if(prevBtn) prevBtn.addEventListener('click',()=>{ goTo(current-1); resetTimer(); });
  if(nextBtn) nextBtn.addEventListener('click',()=>{ goTo(current+1); resetTimer(); });

  startTimer();
})();

// REVIEWS SLIDESHOW
(function(){
  const slides = document.querySelectorAll('#rSlides .rslide');
  if(!slides.length) return;
  const dotsWrap = document.getElementById('rDots');
  const prev = document.getElementById('rPrev');
  const next = document.getElementById('rNext');
  let cur = 0, timer;
  slides.forEach((_,i)=>{
    const d = document.createElement('button');
    d.className = 'rslide-dot' + (i===0?' rslide-dot-active':'');
    d.addEventListener('click',()=>{ goTo(i); reset(); });
    dotsWrap.appendChild(d);
  });
  function goTo(n){
    slides[cur].classList.remove('rslide-active');
    dotsWrap.children[cur].classList.remove('rslide-dot-active');
    cur = (n + slides.length) % slides.length;
    slides[cur].classList.add('rslide-active');
    dotsWrap.children[cur].classList.add('rslide-dot-active');
  }
  function start(){ timer = setInterval(()=>goTo(cur+1), 5000); }
  function reset(){ clearInterval(timer); start(); }
  const wrap = document.querySelector('.rslideshow-wrap');
  if(wrap){
    wrap.addEventListener('mouseenter',()=>clearInterval(timer));
    wrap.addEventListener('mouseleave', start);
  }
  if(prev) prev.addEventListener('click',()=>{ goTo(cur-1); reset(); });
  if(next) next.addEventListener('click',()=>{ goTo(cur+1); reset(); });
  start();
})();

// SCROLL REVEAL
(function(){
  const els = document.querySelectorAll('.fade-up');
  if(!els.length) return;
  const obs = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting){ e.target.classList.add('visible'); obs.unobserve(e.target); }
    });
  },{threshold:0.12});
  els.forEach(el=>obs.observe(el));
})();


(function(){
  var FEED_URL = "https://ccarazas.substack.com/feed";
  var RSS2JSON_URL = "https://api.rss2json.com/v1/api.json?rss_url=" + encodeURIComponent(FEED_URL) + "&count=100";
  var ALL_ORIGINS_URL = "https://api.allorigins.win/get?url=" + encodeURIComponent(FEED_URL);
  var CORSPROXY_URL = "https://corsproxy.io/?url=" + encodeURIComponent(FEED_URL);

  function normalizeTitle(value){
    return String(value || "").replace(/\u00a0/g," ").replace(/&amp;/gi,"&").toLowerCase().replace(/&/g," and ").replace(/\s+/g," ").trim();
  }
  function titleIsGazette(title){
    return /^(?:the\s+)?plymouth\s+sentinel\s+and\s+canine\s+gazette\b/.test(normalizeTitle(title));
  }
  function titleLooksLikeLive(title, description){
    var haystack = normalizeTitle(title + " " + description);
    return /\bsubstack live\b|\blive with\b|\ba recording from\b/.test(haystack);
  }
  function formatDate(value){
    var d = new Date(value); if(isNaN(d.getTime())) return "";
    return d.toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"});
  }
  function stripHtml(value){
    var node=document.createElement("div"); node.innerHTML=value||"";
    return (node.textContent||node.innerText||"").replace(/\s+/g," ").trim();
  }
  function escapeHtml(value){
    return String(value||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
  }
  function cleanTitle(value){
    return String(value||"").replace(/[\u{1F300}-\u{1FFFF}]/gu,"").replace(/[\u{2600}-\u{27BF}]/gu,"").replace(/\s+/g," ").trim();
  }
  function newestFirst(a,b){ return (new Date(b.pubDate||0).getTime()||0)-(new Date(a.pubDate||0).getTime()||0); }
  function withTimeout(url, options, ms){
    var deadline = new Promise(function(_,reject){setTimeout(function(){reject(new Error('timeout'));}, ms||8000);});
    return Promise.race([fetch(url, options||{}), deadline]);
  }
  function postsFromXml(xmlText){
    var xml=new DOMParser().parseFromString(xmlText,"text/xml");
    if(xml.querySelector("parsererror")) throw new Error("Invalid RSS XML");
    return Array.from(xml.querySelectorAll("item")).map(function(item){
      function get(selector){var n=item.querySelector(selector);return n?n.textContent||"":"";}
      return {title:get("title"),link:get("link"),pubDate:get("pubDate"),description:get("description")};
    });
  }
  function fetchDirect(){ return withTimeout(FEED_URL,{mode:"cors"},7000).then(function(r){if(!r.ok)throw new Error("Direct feed "+r.status);return r.text();}).then(postsFromXml); }
  function fetchCorsProxy(){ return withTimeout(CORSPROXY_URL,{},8000).then(function(r){if(!r.ok)throw new Error("CorsProxy "+r.status);return r.text();}).then(postsFromXml); }
  function fetchAllOrigins(){ return withTimeout(ALL_ORIGINS_URL,{},8000).then(function(r){if(!r.ok)throw new Error("AllOrigins "+r.status);return r.json();}).then(function(d){if(!d.contents)throw new Error("No XML content");return postsFromXml(d.contents);}); }
  function fetchRss2Json(){ return withTimeout(RSS2JSON_URL,{},8000).then(function(r){if(!r.ok)throw new Error("RSS2JSON "+r.status);return r.json();}).then(function(d){if(!Array.isArray(d.items))throw new Error("No JSON items");return d.items.map(function(i){return {title:i.title||"",link:i.link||"",pubDate:i.pubDate||"",description:i.description||i.content||""};});}); }
  function getFeed(){ return fetchDirect().catch(fetchCorsProxy).catch(fetchAllOrigins).catch(fetchRss2Json); }

  function renderGazette(posts){
    var grid=document.getElementById("gazetteGrid"); if(!grid)return;
    var items=posts.filter(function(p){return titleIsGazette(p.title);}).sort(newestFirst).slice(0,3); if(!items.length)return;
    grid.innerHTML=items.map(function(p){
      var excerpt=stripHtml(p.description).slice(0,170);
      return "<article class='gazette-card feed-card'><p class='gazette-card-date'>"+escapeHtml(formatDate(p.pubDate))+"</p><h3 class='gazette-card-title'>"+escapeHtml(cleanTitle(p.title).toUpperCase())+"</h3>"+(excerpt?"<p class='gazette-card-desc'>"+escapeHtml(excerpt)+(excerpt.length>=170?"&hellip;":"")+"</p>":"")+"<a class='gazette-card-link' href='"+escapeHtml(p.link)+"' target='_blank' rel='noopener noreferrer'>Read this edition &rarr;</a></article>";
    }).join("");
    grid.setAttribute("data-feed-state","live");
  }
  function renderEssays(posts){
    var grid=document.getElementById("essayFeedGrid"); if(!grid)return;
    var items=posts.filter(function(p){return !titleIsGazette(p.title)&&!titleLooksLikeLive(p.title,p.description);}).sort(newestFirst).slice(0,3); if(!items.length)return;
    grid.innerHTML=items.map(function(p){
      var excerpt=stripHtml(p.description).slice(0,190);
      return "<article class='sub-card feed-card'><div class='sub-card-acc'></div><p class='sub-card-label'>"+escapeHtml(formatDate(p.pubDate))+"</p><h3 class='sub-card-title'>"+escapeHtml(cleanTitle(p.title).toUpperCase())+"</h3>"+(excerpt?"<p class='sub-card-desc'>"+escapeHtml(excerpt)+(excerpt.length>=190?"&hellip;":"")+"</p>":"")+"<a class='sub-card-read' href='"+escapeHtml(p.link)+"' target='_blank' rel='noopener noreferrer'>Read the essay &rarr;</a></article>";
    }).join("");
    grid.setAttribute("data-feed-state","live");
  }
  function initFeed(){
    getFeed().then(function(posts){renderGazette(posts);renderEssays(posts);}).catch(function(){/* RSS unavailable — static fallback is displayed */});
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",initFeed);else initFeed();
})();

(function(){
  var button=document.getElementById("podFeedToggle"); var list=document.getElementById("podcastFeedList");
  if(!button||!list)return;
  button.addEventListener("click",function(){
    var expanded=list.classList.toggle("expanded");
    button.setAttribute("aria-expanded",String(expanded));
    button.textContent=expanded?"Show fewer conversations":"Show all 17 conversations";
  });
})();
