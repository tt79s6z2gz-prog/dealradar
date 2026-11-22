"use strict";
const el=id=>document.getElementById(id);
const state={view:"discover",search:"",category:"",data:{products:[],history:{},alerts:[]},saved:new Set()};
try{state.saved=new Set(JSON.parse(localStorage.getItem("dealradar.saved")||"[]"))}catch{}
const euro=c=>typeof c==="number"?(c/100).toLocaleString("de-DE",{style:"currency",currency:"EUR"}):"–";
const date=s=>s?new Date(s).toLocaleString("de-DE",{dateStyle:"short",timeStyle:"short"}):"–";
const node=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
function empty(heading,msg){const e=node("div","empty");e.append(node("strong","",heading),node("p","",msg));return e}
function card(p){const x=node("article","card"),top=node("div","cardTop"),body=node("div"),btn=node("button","save",state.saved.has(p.id)?"♥":"♡");
body.append(node("div","cat",p.category||"Sonstiges"),node("h3","",p.name));btn.type="button";btn.setAttribute("aria-label","Merkliste ändern");btn.onclick=()=>{if(state.saved.has(p.id))state.saved.delete(p.id);else state.saved.add(p.id);localStorage.setItem("dealradar.saved",JSON.stringify([...state.saved]));render()};top.append(body,btn);x.append(top);
const pr=node("div","price",euro(p.best_price_cents));x.append(pr);if(p.best_price_cents===null||p.best_price_cents===undefined)x.append(node("small","muted","Preis derzeit nicht auslesbar"));else if(!p.fresh)x.append(node("small","muted","Letzter bekannter Preis – nicht frisch geprüft"));
else x.append(node("small","muted","Günstigster gelesener Shop: "+(p.best_shop||"–")));
const matching=state.data.alerts.find(a=>a.product_id===p.id);if(matching){x.append(node("span","pill","−"+matching.drop_pct+" % Preisalarm"))}
if(Array.isArray(p.offers)&&p.offers.length){const ul=node("div","muted",p.offers.length+" erfolgreich gelesene Shop-Angebote");x.append(ul)}if(Array.isArray(p.errors)&&p.errors.length){const details=node("details","muted");const summary=node("summary","","Nicht auslesbar: "+p.errors.length+" Quelle(n)");details.append(summary);for(const problem of p.errors)details.append(node("p","muted",problem));x.append(details)}
const foot=node("div","cardFoot");foot.append(node("small","muted","Stand: "+date(p.last_success_at)));if(p.best_url&&/^https:\/\//i.test(p.best_url)){const a=node("a","","Zum Shop ↗");a.href=p.best_url;a.target="_blank";a.rel="noopener noreferrer";foot.append(a)}x.append(foot);return x}
function putCards(id,items,heading,msg){const box=el(id);box.replaceChildren();if(!items.length){box.append(empty(heading,msg));return}for(const p of items)box.append(card(p))}
function savings(p){const a=state.data.alerts.find(x=>x.product_id===p.id);return a?a.drop_pct:0}
function renderHistory(){const h=el("history");h.replaceChildren();const id=el("historySelect").value,series=(state.data.history[id]||[]).filter(x=>Number.isInteger(x.price_cents));if(!series.length){h.append(empty("Noch keine Daten","Der Preisverlauf entsteht nach erfolgreichen Prüfungen."));return}
const values=series.map(x=>x.price_cents);const min=Math.min(...values),max=Math.max(...values),range=Math.max(100,max-min);h.append(node("div","muted","Letzter erfasster Preis"),node("div","price",euro(values.at(-1))));
const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");svg.setAttribute("viewBox","0 0 320 150");svg.setAttribute("role","img");svg.setAttribute("aria-label","Preisverlauf");const line=document.createElementNS(svg.namespaceURI,"polyline");const points=values.map((v,i)=>[16+(288*(series.length===1?.5:i/(series.length-1))),134-(v-min)/range*118]);line.setAttribute("points",points.map(p=>p.join(",")).join(" "));line.setAttribute("fill","none");line.setAttribute("stroke","#7ee1b5");line.setAttribute("stroke-width","3");svg.append(line);h.append(svg);const labels=node("div","chartLabels");labels.append(node("span","",date(series[0].time)),node("span","",date(series.at(-1).time)));h.append(labels);h.append(node("p","muted","Tief: "+euro(min)+" · Hoch: "+euro(max)+" · "+series.length+" Messungen"))}
function render(){const d=state.data,products=d.products||[];el("count").textContent=String(products.length);el("alarmCount").textContent=String((d.alerts||[]).length);document.querySelectorAll(".page").forEach(x=>x.classList.toggle("hidden",x.id!=="view-"+state.view));document.querySelectorAll(".nav button").forEach(x=>x.classList.toggle("selected",x.dataset.view===state.view));let cats=[...new Set(products.map(x=>x.category||"Sonstiges"))].sort();const current=el("category").value;el("category").replaceChildren(new Option("Alle Kategorien",""),...cats.map(x=>new Option(x,x)));el("category").value=cats.includes(current)?current:"";const found=products.filter(p=>(!state.category||p.category===state.category)&&(p.name+" "+p.category).toLocaleLowerCase("de").includes(state.search));found.sort((a,b)=>savings(b)-savings(a));putCards("deals",found,"Noch keine Produkte","Tippe auf „Produkt beobachten“, füge einen Link ein und bestätige ihn auf GitHub.");putCards("saved",products.filter(x=>state.saved.has(x.id)),"Noch keine Favoriten","Tippe auf ♡ bei einem Produkt, um es zu merken.");const sel=el("historySelect"),old=sel.value;sel.replaceChildren(...products.map(p=>new Option(p.name,p.id)));if(products.some(p=>p.id===old))sel.value=old;renderHistory()}
async function load(){
  el("status").textContent="Preisdaten werden geladen …";
  try{
    const urls=[
      "https://raw.githubusercontent.com/tt79s6z2gz-prog/dealradar/main/docs/data/prices.json?v="+Date.now(),
      "./data/prices.json?v="+Date.now()
    ];
    const outcomes=await Promise.all(urls.map(async u=>{try{
      const r=await fetch(u,{cache:"no-store"});
      if(!r.ok)return null;
      const value=await r.json();
      return Array.isArray(value.products)?value:null;
    }catch{return null}}));
    const data=outcomes.filter(Boolean).sort((a,b)=>String(b.generated_at||"").localeCompare(String(a.generated_at||"")));
    if(!data.length)throw Error("Noch keine Preisdaten verfügbar.");
    const d=data[0];
    state.data=d;
    const count=Number(d.summary?.checked)||0;
    const success=Number(d.summary?.successful)||0;
    const when=d.generated_at?"Letzte Prüfung: "+date(d.generated_at):"Noch keine Preisprüfung";
    el("status").textContent=when+(count?" · "+success+"/"+count+" Quellen erfolgreich":"")+(count>success?" · "+(count-success)+" fehlgeschlagen":"");
    render();
  }catch(err){
    el("status").textContent=state.data.products.length?"Online-Aktualisierung momentan nicht erreichbar. Letzte Daten sichtbar.":"Noch keine Online-Preisdaten verfügbar.";
    render();
  }
}
function guessCategory(name,url){
  const s=(name+" "+url).toLocaleLowerCase("de");
  if(/lego|playmobil|tonies?|ravensburger|barbie|puppe|spielzeug|spielset|hot wheels/.test(s))return "Kinderspielzeug";
  if(/xgimi|beamer|projektor|iphone|ipad|samsung|smartphone|fernseher|laptop|tablet|kopfhörer|monitor|ssd|kamera/.test(s))return "Elektronik";
  if(/waschmaschine|kühlschrank|staubsauger|geschirrspüler|trockner|kaffeemaschine/.test(s))return "Haushaltsgeräte";
  if(/ps5|playstation|switch|xbox|gaming/.test(s))return "Gaming";
  if(/bohrer|akkuschrauber|säge|werkzeug/.test(s))return "Werkzeug";
  return "Sonstiges";
}
function make(){
  const status=el("copyMessage");
  const url=el("url").value.trim();
  let host;
  try {
    const u=new URL(url);
    if(u.protocol!=="https:"||!u.hostname||u.username||u.password)throw Error("HTTPS");
    host=u.hostname.replace(/^www\./,"");
  }catch{status.textContent="Bitte einen vollständigen HTTPS-Produktlink eingeben.";return}
  if(url.length>1200){status.textContent="Bitte einen kürzeren Link ohne Tracking-Parameter verwenden.";return}
  let name=el("name").value.trim();
  if(!name){
    const u=new URL(url);
    let slug=u.pathname.split("/").filter(Boolean).at(-1)||"";
    try{slug=decodeURIComponent(slug)}catch{}
    name=slug.replace(/\.(html?|php|aspx)$/i,"").replace(/[-_]+/g," ").trim();
    if(name.length<3||/^\d+$/.test(name))name="Produkt bei "+host;
  }
  name=name.slice(0,120);
  const selected=el("cat").value;
  const category=selected==="Automatisch"?guessCategory(name,url):selected;
  const shop=(el("shop").value.trim()||host).slice(0,80);
  const body="DEALRADAR_PRODUCT_V1\n"+JSON.stringify({name,category,shop,url});
  const title="[DealRadar] "+name.slice(0,85);
  const issueUrl="https://github.com/tt79s6z2gz-prog/dealradar/issues/new?"+new URLSearchParams({title,body}).toString();
  status.textContent="GitHub wird geöffnet. Dort „Submit new issue“ bestätigen.";
  window.location.assign(issueUrl);
}
document.addEventListener("DOMContentLoaded",()=>{document.querySelectorAll(".nav button").forEach(b=>b.onclick=()=>{state.view=b.dataset.view;render();window.scrollTo(0,0)});el("refresh").onclick=load;el("quickAdd").onclick=()=>{state.view="more";render();window.scrollTo(0,0);el("url").focus()};el("search").oninput=e=>{state.search=e.target.value.toLocaleLowerCase("de");render()};el("category").onchange=e=>{state.category=e.target.value;render()};el("historySelect").onchange=renderHistory;el("make").onclick=make;load();document.addEventListener("visibilitychange",()=>{if(!document.hidden)load()});window.addEventListener("focus",load);setInterval(()=>{if(!document.hidden)load()},60*1000);if("serviceWorker" in navigator&&location.protocol==="https:")navigator.serviceWorker.register("./sw.js").catch(()=>{})});
