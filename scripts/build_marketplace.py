import json, re, os
from collections import Counter
import datetime
BASE=os.path.dirname(os.path.abspath(__file__))   # scripts/
ROOT=os.path.dirname(BASE)                         # repo root
DATA=os.path.join(ROOT,"data")
DATE=datetime.date.today().isoformat()
TOP_LEVEL={"Agriculture & Animal Science","Biotechnology","Communications","Computer",
"Energy","Engineering","Environment","Imaging","Materials & Chemicals","Medical",
"Nanotechnology","Optics and Photonics","Research Tools","Security and Defense",
"Semiconductors","Sensors & Instrumentation","Transportation","Veterinary"}

tech=json.load(open(os.path.join(DATA,"tech_full.json")))
vent=json.load(open(os.path.join(DATA,"startups.json")))
try:
    summ=json.load(open(os.path.join(DATA,"tech_summaries.json")))
except Exception:
    summ={}

def maturity(t):
    blob=" ".join((p.get("type","") for p in (t.get("patents") or []))).lower()+" "+(t.get("patent_status") or "").lower()
    if "issued" in blob or "granted" in blob: return "issued"
    if any(k in blob for k in ("application","pending","filed","provisional")): return "pending"
    return None

T=[]
for t in tech:
    T.append({"id":t["id"],"t":t["title"],"rid":int(t["id"]),
      "url":t.get("url") or ("https://techtransfer.universityofcalifornia.edu/NCD/"+str(t["id"])+".html"),
      "top":[c for c in (t.get("categories") or []) if c in TOP_LEVEL],
      "cats":t.get("categories") or [],
      "d":t.get("description") or "","a":t.get("advantages") or "",
      "inv":t.get("inventors") or [],"case":t.get("uc_case") or "",
      "cy":t.get("case_year"),
      "s":summ.get(t["id"]) or ((t.get("description") or "")[:115].rstrip()+("…" if len(t.get("description") or "")>115 else "")),
      "pat":t.get("patents") or [],"mat":maturity(t)})

V=[]
for v in vent:
    ind=(v.get("industry") or "").replace("﻿","").strip()
    V.append({"co":v["company"],"about":v.get("about") or "","status":v.get("status") or "",
      "web":v.get("website") or "","yr":v.get("founding_year"),
      "founders":v.get("founders") or [],"ind":ind,"lic":bool(v.get("licenses_ucsb_ip")),
      "cap":v.get("capital_raised") or "","musd":v.get("capital_raised_musd")})

catc=Counter()
for t in T:
    for c in t["top"]: catc[c]+=1
CATS=sorted(catc.items(), key=lambda x:-x[1])
SECT=sorted(set(v["ind"] for v in V if v["ind"]))

DATA=json.dumps({"tech":T,"vent":V,"cats":CATS,"sectors":SECT})
LIB=open(os.path.join(BASE,"vendor","chart.umd.js")).read().replace("</script>","<\\/script>")

HTML=r'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>UCSB Innovation Marketplace — Technologies & Ventures</title>
<style>
:root{--navy:#003660;--navy2:#09508a;--gold:#febc11;--ink:#1c2530;--bg:#f5f7fa;--card:#fff;--line:#d4dbe6;--green:#2f6a2a;--blue:#09508a;--grey:#586273;--focus:#0a5fd6}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--ink);font-size:16px;line-height:1.5}
a{color:var(--navy2)}a:hover{text-decoration:underline}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
.skip-link{position:absolute;left:8px;top:-44px;background:var(--navy);color:#fff;padding:10px 14px;border-radius:0 0 8px 8px;z-index:60;transition:top .15s;font-weight:700}
.skip-link:focus{top:0;text-decoration:none}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px;border-radius:5px}
button{font:inherit}
header{background:linear-gradient(120deg,var(--navy),#062c4d);color:#fff;padding:24px 32px;border-bottom:4px solid var(--gold)}
header h1{margin:0;font-size:24px;font-weight:800}
header p{margin:5px 0 0;color:#eef4fb;font-size:14px}
header .contact{margin-top:8px;font-size:13.5px;color:#eef4fb}header .contact a{color:var(--gold);font-weight:700}
header a:focus-visible{outline-color:var(--gold)}
.tablist{display:flex;gap:0;background:var(--navy);padding:0 24px;border-bottom:1px solid #0a2a47}
.tablist [role=tab]{background:none;border:none;color:#dbe7f3;font-size:15px;font-weight:600;padding:14px 20px;cursor:pointer;border-bottom:3px solid transparent}
.tablist [role=tab][aria-selected=true]{color:#fff;border-bottom-color:var(--gold)}
.tablist [role=tab]:hover{color:#fff}
.tablist [role=tab]:focus-visible{outline:3px solid var(--gold);outline-offset:-3px}
main{display:block}
.wrap{max-width:1300px;margin:0 auto;padding:24px 28px 70px}
[role=tabpanel]:focus{outline:none}
.lead{font-size:15px;color:#33405a;margin:4px 0 18px;max-width:780px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:13px;margin:14px 0 22px;padding:0;list-style:none}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px 17px}
.kpi .n{font-size:26px;font-weight:800;color:var(--navy)}.kpi .l{font-size:12px;color:var(--grey);margin-top:3px;text-transform:uppercase;letter-spacing:.03em}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:860px){.grid2{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.card h3{margin:0 0 12px;font-size:15px;color:var(--navy)}
.chartbox{position:relative;height:300px}
.toolbar{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:16px}
.toolbar .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
.toolbar .row:last-child{margin-bottom:0}
input[type=text],select{padding:9px 12px;border:1px solid #767f90;border-radius:8px;font-size:14px;font-family:inherit;color:var(--ink);background:#fff}
input[type=text]{flex:1;min-width:210px}
.lbl{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--grey)}
fieldset{border:none;padding:0;margin:0;display:flex;gap:7px;flex-wrap:wrap;align-items:center}
legend{float:left;margin-right:7px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--grey);padding:6px 0}
.chip{display:inline-flex;align-items:center;min-height:30px;border:1px solid #767f90;background:#fff;color:#33405a;border-radius:20px;padding:4px 12px;font-size:13px;cursor:pointer}
.chip:hover{border-color:var(--navy2)}
.chip[aria-pressed=true]{background:var(--navy);color:#fff;border-color:var(--navy)}
.chip .c{color:#5a6573;font-size:11.5px;margin-left:5px;font-weight:600}
.chip[aria-pressed=true] .c{color:#dbe7f3}
.count{font-size:13px;color:var(--grey)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(335px,1fr));gap:14px;padding:0;list-style:none}
.item{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px 16px;display:flex;flex-direction:column}
.titlebtn{background:none;border:none;text-align:left;padding:0;font-size:15px;font-weight:700;color:var(--navy);line-height:1.3;cursor:pointer}
.titlebtn:hover{color:var(--navy2);text-decoration:underline}
.item .meta{font-size:12.5px;color:var(--grey);margin:5px 0}
.item .desc{font-size:13.5px;color:#33405a;line-height:1.45;margin:8px 0;flex:1}
.tagrow{margin:6px 0;display:flex;flex-wrap:wrap;gap:4px}
.tag{display:inline-block;background:#e8eef7;color:#234a86;border:1px solid #c5d4ea;border-radius:20px;padding:1px 9px;font-size:11.5px}
.badge{display:inline-block;border-radius:5px;padding:2px 8px;font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.03em}
.b-issued{background:#e3efdf;color:var(--green)}.b-pending{background:#fbedcb;color:#7a5400}
.b-active{background:#e3efdf;color:var(--green)}.b-acquired{background:#dde9f7;color:var(--blue)}.b-inactive{background:#e6e6ea;color:#4d4d57}
.acts{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}
.btn{border:1px solid transparent;border-radius:8px;padding:9px 14px;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;display:inline-block;min-height:38px}
.btn-primary{background:var(--navy);color:#fff}.btn-primary:hover{background:var(--navy2);text-decoration:none;color:#fff}
.btn-ghost{background:#eaf0f8;color:var(--navy);border-color:#cdd9ea}.btn-ghost:hover{background:#dde7f4;text-decoration:none}
.empty{padding:40px;text-align:center;color:var(--grey);font-size:14px}
.drawer-overlay{position:fixed;inset:0;background:rgba(10,20,40,.45);opacity:0;visibility:hidden;transition:opacity .2s;z-index:40}
.drawer-overlay.on{opacity:1;visibility:visible}
.drawer{position:fixed;top:0;right:0;height:100%;width:min(580px,96vw);background:#fff;box-shadow:-8px 0 32px rgba(0,0,0,.22);transform:translateX(100%);transition:transform .25s;z-index:41;overflow-y:auto;padding:26px 28px 48px}
.drawer.on{transform:translateX(0)}
.drawer-close{position:absolute;top:14px;right:16px;border:1px solid #cdd9ea;background:#eef2f8;border-radius:8px;width:40px;height:40px;font-size:20px;cursor:pointer;color:#1c2530;line-height:1}
.drawer-close:hover{background:#dde7f4}
.d-eyebrow{font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--navy2);font-weight:700;margin:0}
.d-title{font-size:21px;color:var(--navy);margin:4px 0 10px;padding-right:44px;line-height:1.3}
.drawer h3{font-size:12.5px;text-transform:uppercase;letter-spacing:.03em;color:var(--grey);margin:18px 0 5px}
.drawer p{font-size:14px;line-height:1.55;margin:0;color:#28313d}
.drawer table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:4px}
.drawer th,.drawer td{border:1px solid var(--line);padding:5px 7px;text-align:left}
.drawer th{background:#eef2f8;color:var(--navy)}
.cta-big{display:block;text-align:center;margin-top:22px;background:var(--gold);color:#332600;padding:13px;border-radius:9px;font-weight:800;font-size:15px}
.cta-big:hover{background:#ffca3a;text-decoration:none;color:#332600}
.foot{font-size:12.5px;color:var(--grey);margin-top:24px;line-height:1.6}
.draftbar{background:#fff3d6;border-bottom:1px solid #e6cf8f;color:#5a4500;padding:9px 24px;font-size:13px}.draftbar a{color:#234a86;font-weight:700}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
</style></head><body>
<a class="skip-link" href="#main">Skip to main content</a>
<header>
 <h1>UCSB Innovation Marketplace</h1>
 <p>Explore technologies available for licensing and ventures emerging from UC&nbsp;Santa&nbsp;Barbara.</p>
 <p class="contact">Questions or interest? Contact UC Santa Barbara's Innovation &amp; Entrepreneurship Team: <a href="mailto:info@innovation.ucsb.edu">info@innovation.ucsb.edu</a></p>
</header>
<div class="draftbar" role="note"><strong>Draft preview.</strong> Built from public UCSB data for feedback — not an official UCSB page. Data updated __DATE__. Feedback: <a href="mailto:caylor@ucsb.edu?subject=UCSB%20Innovation%20Marketplace%20feedback">caylor@ucsb.edu</a></div>
<nav class="tablist" role="tablist" aria-label="Choose a view">
 <button role="tab" id="tab-overview" aria-selected="true" aria-controls="lens-overview" tabindex="0">Overview</button>
 <button role="tab" id="tab-license" aria-selected="false" aria-controls="lens-license" tabindex="-1">License a Technology</button>
 <button role="tab" id="tab-invest" aria-selected="false" aria-controls="lens-invest" tabindex="-1">Explore Ventures</button>
</nav>
<main id="main">
<div class="wrap">

<section class="lens" id="lens-overview" role="tabpanel" aria-labelledby="tab-overview" tabindex="0">
 <h2 class="sr-only">Overview</h2>
 <ul class="kpis" id="ovkpis"></ul>
 <div class="grid2">
  <div class="card"><h3 id="cCatH">Technologies available by field</h3><div class="chartbox"><canvas id="cCat" aria-hidden="true"></canvas></div><div class="sr-only" id="cCatSR"></div></div>
  <div class="card"><h3 id="cSectH">Active ventures by sector</h3><div class="chartbox"><canvas id="cSect" aria-hidden="true"></canvas></div><div class="sr-only" id="cSectSR"></div></div>
 </div>
 <p class="foot">Two public datasets: technologies available for licensing (UCOP technology-transfer portal) and UCSB ventures (TIA Startup Database). Choose a view above to explore and get in touch. Data updated __DATE__.</p>
</section>

<section class="lens" id="lens-license" role="tabpanel" aria-labelledby="tab-license" tabindex="0" hidden>
 <h2 class="sr-only">License a technology</h2>
 <p class="lead">Browse UCSB inventions available for licensing. Filter by field, sort by newest, open any item for the full description, then request licensing information in one click.</p>
 <div class="toolbar">
  <div class="row">
   <label class="sr-only" for="lq">Search technologies</label>
   <input type="text" id="lq" placeholder="Search technologies by keyword, title, or Tech ID…">
   <label class="lbl" for="lsort">Sort</label>
   <select id="lsort"><option value="listed">Recently listed</option><option value="disc">Newest disclosure</option><option value="discold">Oldest disclosure</option><option value="az">Title A–Z</option></select>
   <label class="lbl" for="lpat">Patent</label>
   <select id="lpat"><option value="">Any</option><option value="issued">Issued</option><option value="pending">Pending</option></select>
   <label class="lbl" for="lyear">Disclosed after</label>
   <select id="lyear"><option value="">Any year</option></select>
  </div>
  <div class="row"><fieldset id="lfacets"><legend>Field</legend></fieldset></div>
  <div class="row"><span class="count" id="lcount" role="status" aria-live="polite"></span></div>
 </div>
 <ul class="cards" id="lcards"></ul>
</section>

<section class="lens" id="lens-invest" role="tabpanel" aria-labelledby="tab-invest" tabindex="0" hidden>
 <h2 class="sr-only">Explore ventures</h2>
 <p class="lead">Explore ventures founded on UCSB research and by UCSB innovators. Filter to active companies by sector and founding year, sort by capital raised, and request a warm introduction through UCSB.</p>
 <div class="toolbar">
  <div class="row">
   <label class="sr-only" for="vq">Search ventures</label>
   <input type="text" id="vq" placeholder="Search ventures by name, founder, or description…">
   <label class="lbl" for="vstatus">Status</label>
   <select id="vstatus"><option value="Active">Active</option><option value="">All</option><option value="Acquired">Acquired</option><option value="Inactive">Inactive</option></select>
   <label class="lbl" for="vsort">Sort</label>
   <select id="vsort"><option value="cap">Capital raised</option><option value="recent">Newest</option><option value="az">Company A–Z</option></select>
  </div>
  <div class="row">
   <label style="font-size:13.5px"><input type="checkbox" id="vlic"> Licenses UCSB IP only</label>
   <label class="lbl" for="vyear">Founded after</label>
   <select id="vyear"><option value="">Any year</option></select>
  </div>
  <div class="row"><fieldset id="vfacets"><legend>Sector</legend></fieldset></div>
  <div class="row"><span class="count" id="vcount" role="status" aria-live="polite"></span></div>
 </div>
 <ul class="cards" id="vcards"></ul>
</section>

</div>
</main>
<div id="drawer-overlay" class="drawer-overlay" hidden></div>
<aside id="drawer" class="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title" hidden>
 <button class="drawer-close" id="drawerClose" aria-label="Close details">&times;</button>
 <div id="drawer-body"></div>
</aside>

<script>/*__CHARTJS__*/</script>
<script>
const DATA=__DATA__;const TECH=DATA.tech,VENT=DATA.vent,CATS=DATA.cats,SECT=DATA.sectors;
const CONTACT="info@innovation.ucsb.edu";
const NAVY="#003660",GOLD="#febc11",ACC="#09508a";
const esc=s=>(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
function money(v){if(v==null)return '—';if(v>=1000)return '$'+(v/1000).toFixed(2)+'B';if(v>=1)return '$'+(v<10?v.toFixed(2):Math.round(v))+'M';if(v>0)return '$'+Math.round(v*1000)+'K';return '$0';}
function mailto(subject,body){return 'mailto:'+CONTACT+'?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);}
function techMail(t){
 const subject='Licensing interest: '+t.t+(t.case?(' (UC Case '+t.case+')'):'')+' — Tech ID '+t.id;
 const body='Hello UCSB Office of Technology & Industry Alliances,\n\nOur organization would like to learn more about licensing the following UCSB technology:\n\n'+
  '• Technology: '+t.t+'\n• Tech ID: '+t.id+'\n'+(t.case?('• UC Case: '+t.case+'\n'):'')+(t.cy?('• Disclosed: '+t.cy+'\n'):'')+
  (t.top&&t.top.length?('• Field(s): '+t.top.join(', ')+'\n'):'')+(t.inv&&t.inv.length?('• Inventor(s): '+t.inv.join(', ')+'\n'):'')+'• Listing: '+t.url+'\n\n'+
  'So we can route your inquiry, please share:\n• Company / organization: \n• Your name & title: \n• Email & phone: \n• Intended field of use / application: \n• Stage & desired timeline: \n\nThank you!';
 return {subject,body};
}
function ventMail(v){
 const subject='Investor interest: '+v.co;
 const body='Hello UCSB Office of Technology & Industry Alliances,\n\nWe are an investor interested in the following UCSB venture and would welcome an introduction or more information:\n\n'+
  '• Company: '+v.co+'\n'+(v.ind?('• Sector: '+v.ind+'\n'):'')+(v.yr?('• Founded: '+v.yr+'\n'):'')+(v.status?('• Status: '+v.status+'\n'):'')+
  (v.musd?('• Capital raised (disclosed): '+money(v.musd)+'\n'):'')+(v.web?('• Website: '+(v.web.startsWith('http')?v.web:'https://'+v.web)+'\n'):'')+
  '\nAbout us:\n• Fund / firm: \n• Your name & title: \n• Email: \n• Investment focus & typical check size: \n• Timeline: \n\nThank you!';
 return {subject,body};
}

/* ---------- OVERVIEW ---------- */
const activeV=VENT.filter(v=>v.status==='Active');
const capTotal=VENT.filter(v=>v.musd).reduce((s,v)=>s+v.musd,0);
document.getElementById('ovkpis').innerHTML=[
 [TECH.length,'Technologies to license'],[CATS.length,'Technology fields'],
 [VENT.length,'UCSB ventures'],[activeV.length,'Active ventures'],
 [capTotal>=1000?'$'+(capTotal/1000).toFixed(1)+'B':money(capTotal),'Capital raised (disclosed)'],
].map(k=>`<li class="kpi"><div class="n">${k[0]}</div><div class="l">${k[1]}</div></li>`).join('');

/* ---------- LICENSE LENS ---------- */
let lFacets=new Set();
function renderLFacets(){
 document.getElementById('lfacets').innerHTML='<legend>Field</legend>'+
  CATS.map(([c,n])=>`<button type="button" class="chip" aria-pressed="${lFacets.has(c)}" data-c="${esc(c)}">${esc(c)}<span class="c">${n}</span></button>`).join('');
 document.querySelectorAll('#lfacets .chip').forEach(b=>b.onclick=()=>{const c=b.dataset.c;lFacets.has(c)?lFacets.delete(c):lFacets.add(c);renderLFacets();renderL();});
}
function renderL(){
 const q=document.getElementById('lq').value.toLowerCase();
 const sort=document.getElementById('lsort').value, pat=document.getElementById('lpat').value;
 const yr=parseInt(document.getElementById('lyear').value)||0;
 let r=TECH.filter(t=>{
  if(q && !(t.t.toLowerCase().includes(q)||t.id.includes(q)||(t.d||'').toLowerCase().includes(q)||(t.inv||[]).join(' ').toLowerCase().includes(q))) return false;
  if(pat && t.mat!==pat) return false;
  if(yr && (!t.cy||t.cy<yr)) return false;
  if(lFacets.size && !t.top.some(c=>lFacets.has(c))) return false;
  return true;});
 r.sort((a,b)=> sort==='az'?a.t.localeCompare(b.t):sort==='disc'?(((b.cy||0)-(a.cy||0))||(b.rid-a.rid)):sort==='discold'?(((a.cy||9999)-(b.cy||9999))||(a.rid-b.rid)):b.rid-a.rid);
 document.getElementById('lcount').textContent=r.length+' of '+TECH.length+' technologies shown';
 document.getElementById('lcards').innerHTML = r.length? r.map(t=>{
  const badge=t.mat==='issued'?'<span class="badge b-issued">Patent issued</span>':t.mat==='pending'?'<span class="badge b-pending">Patent pending</span>':'';
  const m=techMail(t);
  return `<li class="item">
   <button type="button" class="titlebtn" data-id="${t.id}" aria-label="View details for ${esc(t.t)}">${esc(t.t)}</button>
   <div class="meta">Tech ID ${t.id}${t.cy?' · Disclosed '+t.cy:''}${t.case?' · UC Case '+esc(t.case):''} ${badge}</div>
   <div class="tagrow">${t.top.slice(0,3).map(c=>'<span class="tag">'+esc(c)+'</span>').join('')}</div>
   <p class="desc">${esc(t.s||'')}</p>
   <div class="acts"><button type="button" class="btn btn-ghost" data-id="${t.id}" aria-label="Details for ${esc(t.t)}">Details</button>
   <a class="btn btn-primary" href="${mailto(m.subject,m.body)}" aria-label="Request licensing info for ${esc(t.t)}">Request licensing info</a></div></li>`;
 }).join('') : '<li class="empty">No technologies match these filters.</li>';
 document.querySelectorAll('#lcards .titlebtn, #lcards .btn-ghost').forEach(b=>b.onclick=()=>openTech(b.dataset.id));
}

/* ---------- INVEST LENS ---------- */
let vFacets=new Set();
function renderVFacets(){
 document.getElementById('vfacets').innerHTML='<legend>Sector</legend>'+
  SECT.map(c=>`<button type="button" class="chip" aria-pressed="${vFacets.has(c)}" data-c="${esc(c)}">${esc(c)}</button>`).join('');
 document.querySelectorAll('#vfacets .chip').forEach(b=>b.onclick=()=>{const c=b.dataset.c;vFacets.has(c)?vFacets.delete(c):vFacets.add(c);renderVFacets();renderV();});
}
function renderV(){
 const q=document.getElementById('vq').value.toLowerCase();
 const st=document.getElementById('vstatus').value, sort=document.getElementById('vsort').value;
 const lic=document.getElementById('vlic').checked, yr=parseInt(document.getElementById('vyear').value)||0;
 let r=VENT.filter(v=>{
  if(st && v.status!==st) return false;
  if(q && !(v.co.toLowerCase().includes(q)||(v.about||'').toLowerCase().includes(q)||(v.founders||[]).join(' ').toLowerCase().includes(q))) return false;
  if(lic && !v.lic) return false;
  if(vFacets.size && !vFacets.has(v.ind)) return false;
  if(yr && (!v.yr||v.yr<yr)) return false;
  return true;});
 r.sort((a,b)=> sort==='az'?a.co.localeCompare(b.co):sort==='recent'?((b.yr||0)-(a.yr||0)):((b.musd||0)-(a.musd||0)));
 document.getElementById('vcount').textContent=r.length+' ventures shown';
 document.getElementById('vcards').innerHTML = r.length? r.map(v=>{
  const sb=v.status==='Active'?'b-active':v.status==='Acquired'?'b-acquired':'b-inactive';
  const m=ventMail(v);
  return `<li class="item">
   <button type="button" class="titlebtn" data-co="${esc(v.co)}" aria-label="View details for ${esc(v.co)}">${esc(v.co)}</button>
   <div class="meta"><span class="badge ${sb}">${esc(v.status||'—')}</span> ${v.yr?('· founded '+v.yr):''} ${v.musd?('· '+money(v.musd)+' raised'):''}</div>
   <div class="tagrow">${v.ind?'<span class="tag">'+esc(v.ind)+'</span>':''}${v.lic?'<span class="tag">licenses UCSB IP</span>':''}</div>
   <p class="desc">${esc(v.about||'')}</p>
   <div class="meta">${(v.founders||[]).length?('Founders: '+esc(v.founders.join(', '))):''}</div>
   <div class="acts">${v.web?('<a class="btn btn-ghost" href="'+(v.web.startsWith('http')?v.web:'https://'+v.web)+'" target="_blank" rel="noopener" aria-label="Website for '+esc(v.co)+' (opens in new tab)">Website</a>'):''}
   <a class="btn btn-primary" href="${mailto(m.subject,m.body)}" aria-label="Request an introduction to ${esc(v.co)} via UCSB">Request an intro via UCSB</a></div></li>`;
 }).join('') : '<li class="empty">No ventures match these filters.</li>';
 document.querySelectorAll('#vcards .titlebtn').forEach(b=>b.onclick=()=>openVenture(b.dataset.co));
}

/* ---------- DRAWER (accessible dialog) ---------- */
let lastFocus=null;
function openTech(id){const t=TECH.find(x=>x.id===id);if(!t)return;
 const m=techMail(t);
 let pt='';
 if(t.pat&&t.pat.length){pt='<h3>Patents</h3><table><caption class="sr-only">Patents for this technology</caption><thead><tr><th scope="col">Country</th><th scope="col">Type</th><th scope="col">Number</th><th scope="col">Dated</th></tr></thead><tbody>'+
   t.pat.map(p=>`<tr><td>${esc(p.country||'')}</td><td>${esc(p.type||'')}</td><td>${esc(p.number||'')}</td><td>${esc(p.dated||'')}</td></tr>`).join('')+'</tbody></table>';}
 document.getElementById('drawer-body').innerHTML=
  '<p class="d-eyebrow">Tech ID '+t.id+(t.cy?' · Disclosed '+t.cy:'')+(t.case?' · UC Case '+esc(t.case):'')+'</p>'+
  '<h2 class="d-title" id="drawer-title">'+esc(t.t)+'</h2>'+
  '<div>'+(t.mat==='issued'?'<span class="badge b-issued">Patent issued</span>':t.mat==='pending'?'<span class="badge b-pending">Patent pending</span>':'')+'</div>'+
  '<div class="tagrow" style="margin-top:8px">'+t.cats.map(c=>'<span class="tag">'+esc(c)+'</span>').join('')+'</div>'+
  (t.d?'<h3>Description</h3><p>'+esc(t.d)+'</p>':'')+
  (t.a?'<h3>Advantages / Applications</h3><p>'+esc(t.a)+'</p>':'')+
  (t.inv.length?'<h3>Inventors</h3><p>'+esc(t.inv.join(', '))+'</p>':'')+pt+
  '<a class="cta-big" href="'+mailto(m.subject,m.body)+'">Request licensing information</a>'+
  '<p style="margin-top:12px;font-size:12.5px;color:#586273">Full portal page: <a href="'+t.url+'" target="_blank" rel="noopener">'+esc(t.url)+' (opens in new tab)</a></p>';
 showDrawer();
}
function openVenture(co){const v=VENT.find(x=>x.co===co);if(!v)return;
 const m=ventMail(v);
 const sb=v.status==='Active'?'b-active':v.status==='Acquired'?'b-acquired':'b-inactive';
 document.getElementById('drawer-body').innerHTML=
  '<p class="d-eyebrow">UCSB Venture'+(v.lic?' · licenses UCSB IP':'')+'</p>'+
  '<h2 class="d-title" id="drawer-title">'+esc(v.co)+'</h2>'+
  '<div><span class="badge '+sb+'">'+esc(v.status||'—')+'</span> '+(v.ind?'<span class="tag">'+esc(v.ind)+'</span>':'')+'</div>'+
  (v.about?'<h3>About</h3><p>'+esc(v.about)+'</p>':'')+
  '<h3>Details</h3><p>'+(v.yr?('Founded '+v.yr+'<br>'):'')+(v.musd?('Capital raised: '+money(v.musd)+'<br>'):'')+((v.founders||[]).length?('Founders: '+esc(v.founders.join(', '))+'<br>'):'')+(v.web?('Website: <a href="'+(v.web.startsWith('http')?v.web:'https://'+v.web)+'" target="_blank" rel="noopener">'+esc(v.web)+' (opens in new tab)</a>'):'')+'</p>'+
  '<a class="cta-big" href="'+mailto(m.subject,m.body)+'">Request an introduction via UCSB</a>';
 showDrawer();
}
function showDrawer(){
 lastFocus=document.activeElement;
 const d=document.getElementById('drawer'),o=document.getElementById('drawer-overlay');
 o.hidden=false;d.hidden=false;
 requestAnimationFrame(()=>{o.classList.add('on');d.classList.add('on');});
 document.getElementById('drawerClose').focus();
 document.addEventListener('keydown',trap,true);
}
function closeDrawer(){
 const d=document.getElementById('drawer'),o=document.getElementById('drawer-overlay');
 d.classList.remove('on');o.classList.remove('on');
 document.removeEventListener('keydown',trap,true);
 setTimeout(()=>{d.hidden=true;o.hidden=true;},220);
 if(lastFocus&&lastFocus.focus)lastFocus.focus();
}
function trap(e){
 if(e.key==='Escape'){e.preventDefault();closeDrawer();return;}
 if(e.key!=='Tab')return;
 const f=document.getElementById('drawer').querySelectorAll('a[href],button,select,input,[tabindex]:not([tabindex="-1"])');
 if(!f.length)return;
 const first=f[0],last=f[f.length-1];
 if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
 else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
}
document.getElementById('drawerClose').onclick=closeDrawer;
document.getElementById('drawer-overlay').onclick=closeDrawer;

/* ---------- wiring ---------- */
['lq','lsort','lpat','lyear'].forEach(id=>document.getElementById(id).addEventListener('input',renderL));
['vq','vstatus','vsort','vlic','vyear'].forEach(id=>document.getElementById(id).addEventListener('input',renderV));
(function(){const ly=[...new Set(TECH.map(t=>t.cy).filter(Boolean))].sort((a,b)=>b-a);
 document.getElementById('lyear').innerHTML='<option value="">Any year</option>'+ly.map(y=>`<option value="${y}">${y}</option>`).join('');
 const vy=[...new Set(VENT.map(v=>v.yr).filter(Boolean))].sort((a,b)=>b-a);
 document.getElementById('vyear').innerHTML='<option value="">Any year</option>'+vy.map(y=>`<option value="${y}">${y}</option>`).join('');})();
renderLFacets();renderL();renderVFacets();renderV();

/* ---------- TAB pattern (roving tabindex + arrow keys) ---------- */
const tabs=[...document.querySelectorAll('[role=tab]')];
function selectTab(tab){
 tabs.forEach(t=>{const sel=t===tab;t.setAttribute('aria-selected',sel);t.tabIndex=sel?0:-1;
  document.getElementById(t.getAttribute('aria-controls')).hidden=!sel;});
 if(tab.id==='tab-overview') charts();
}
tabs.forEach((tab,i)=>{
 tab.addEventListener('click',()=>selectTab(tab));
 tab.addEventListener('keydown',e=>{
  let n=null;
  if(e.key==='ArrowRight'||e.key==='ArrowDown')n=tabs[(i+1)%tabs.length];
  else if(e.key==='ArrowLeft'||e.key==='ArrowUp')n=tabs[(i-1+tabs.length)%tabs.length];
  else if(e.key==='Home')n=tabs[0];else if(e.key==='End')n=tabs[tabs.length-1];
  if(n){e.preventDefault();n.focus();selectTab(n);}
 });
});

/* ---------- charts (lazy) + screen-reader equivalents ---------- */
let built={};
function srList(id,label,pairs){
 document.getElementById(id).innerHTML='<p>'+label+':</p><ul>'+pairs.map(p=>'<li>'+esc(p[0])+': '+p[1]+'</li>').join('')+'</ul>';
}
function charts(){if(built.o)return;
 const sc={};activeV.forEach(v=>{if(v.ind)sc[v.ind]=(sc[v.ind]||0)+1;});
 const se=Object.entries(sc).sort((a,b)=>b[1]-a[1]);
 srList('cCatSR','Technologies available by field',CATS);
 srList('cSectSR','Active ventures by sector',se);
 if(typeof Chart==='undefined'){
   document.querySelectorAll('.chartbox').forEach(c=>c.innerHTML='<p style="color:#586273;font-size:13px;padding:16px">Chart unavailable; see the list that follows.</p>');
   built.o=1;return;}
 built.o=1;
 new Chart(document.getElementById('cCat'),{type:'bar',data:{labels:CATS.map(c=>c[0]),datasets:[{label:'Technologies',data:CATS.map(c=>c[1]),backgroundColor:NAVY}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{precision:0}}}}});
 new Chart(document.getElementById('cSect'),{type:'bar',data:{labels:se.map(x=>x[0]),datasets:[{label:'Active ventures',data:se.map(x=>x[1]),backgroundColor:ACC}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{precision:0}}}}});
}
charts();
</script></body></html>'''
HTML=HTML.replace("/*__CHARTJS__*/",LIB).replace("__DATA__",DATA).replace("__DATE__",DATE)
out=os.path.join(ROOT,"public","index.html")
open(out,"w").write(HTML)
print("saved",out,"bytes",len(HTML),"| tech",len(T),"vent",len(V))
