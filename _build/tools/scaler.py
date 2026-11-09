from chrome import write
import sys

CSS = r"""
.lay{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:28px;align-items:start}
@media (max-width:900px){.lay{grid-template-columns:minmax(0,1fr)}}
.who{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:16px}
.who label{display:flex;flex-direction:column;gap:6px}
.who span{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#6B716A}
.factor{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 18px}
.factor .n{font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;font-size:clamp(48px,6vw,72px);line-height:.9;color:#C2461B}
.warn{background:#F9EEDA;border-left:4px solid #D9A520;padding:12px 14px;font-size:16px;margin:14px 0 0}
table{width:100%;border-collapse:collapse;font-size:16px}
th{text-align:left;font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#6B716A;font-weight:500;padding:0 8px 8px 0;border-bottom:1.5px solid #16201C}
td{padding:10px 8px 10px 0;border-bottom:1px solid #DDD5C3;vertical-align:top}
td.amt{font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}
td.note{font-size:14px;color:#5A635D}
td.note b{color:#A93F17;font-weight:600}
.was{display:block;font-size:12.5px;color:#8A8F87;font-weight:400}
@media (max-width:560px){td.note{display:block;padding-top:0;border-bottom:0}tr{display:block;border-bottom:1px solid #DDD5C3;padding:6px 0}td{display:inline-block;border:0;padding:4px 8px 4px 0}td.amt{min-width:7.5em}}
@media print{.noprint{display:none!important}body{background:#fff}.lay{display:block}.panel{border:0;padding:0}}
"""

BODY = r"""
  <div class="lay">
    <section class="panel noprint" aria-labelledby="r-h">
      <h2 id="r-h" class="label">Paste the ingredients</h2>
      <label for="rec" style="position:absolute;left:-9999px">Ingredients, one per line</label>
      <textarea id="rec" style="min-height:260px">2 ripe bananas
2 large eggs
1 cup rolled oats
1/2 cup milk
1 tsp baking powder
1/2 tsp cinnamon
1 1/2 tbsp butter, for the pan
pinch of salt</textarea>
      <p class="private" style="margin-top:8px">One ingredient per line, any format: 1 1/2 cups, 1½ cups, 3 Tbsp, 200 g, 2 large eggs.</p>
      <div class="who">
        <label><span>Recipe serves</span><input id="serves" type="number" min="1" step="1" value="4"></label>
        <label><span>Grown-ups</span><input id="adults" type="number" min="0" step="1" value="2"></label>
        <label><span>Kids</span><input id="kids" type="number" min="0" step="1" value="20"></label>
      </div>
      <p class="private" style="margin-top:8px">A kid counts as half a portion. Set grown-ups to the whole group if everyone eats like a grown-up.</p>
    </section>

    <section class="panel" aria-labelledby="o-h" aria-live="polite">
      <div class="factor"><span class="n" id="fac"></span><span id="facl" style="font-size:18px;font-weight:600"></span></div>
      <div id="warn"></div>
      <div class="noprint" id="batchrow" style="margin-top:14px" hidden><div class="chips" role="group" aria-label="Show amounts for"><button type="button" class="chip" data-b="all" aria-pressed="true">The whole amount</button><button type="button" class="chip" data-b="one" aria-pressed="false">One batch</button></div></div>
      <h2 id="o-h" style="margin:20px 0 10px;font-size:22px">What to measure</h2>
      <table><thead><tr><th scope="col">Amount</th><th scope="col">Ingredient</th><th scope="col">Good to know</th></tr></thead><tbody id="out"></tbody></table>
      <div class="noprint" style="display:flex;flex-wrap:wrap;gap:12px;margin-top:18px">
        <button type="button" class="btn" id="copy">Copy the shopping list</button>
        <button type="button" class="btn ghost" id="print">Print it</button>
      </div>
      <p class="private" style="margin-top:10px">This scales amounts. It does not check allergens: a person who knows the kids does that. Nothing you paste here leaves this page.</p>
    </section>
  </div>
"""

SCRIPT = r"""
(function(){
var UF={'½':.5,'⅓':1/3,'⅔':2/3,'¼':.25,'¾':.75,'⅕':.2,'⅖':.4,'⅗':.6,'⅘':.8,'⅙':1/6,'⅚':5/6,'⅛':.125,'⅜':.375,'⅝':.625,'⅞':.875};
var UNITS=[
 [/^(cups?|c\.?)$/i,'vol',48],[/^(tablespoons?|tbsps?\.?|tbs\.?|T)$/,'vol',3],[/^(tablespoons?|tbsps?\.?|tbs\.?)$/i,'vol',3],
 [/^(teaspoons?|tsps?\.?|t)$/,'vol',1],[/^(teaspoons?|tsps?\.?)$/i,'vol',1],[/^(fl\.? ?oz\.?|fluid ounces?)$/i,'vol',6],
 [/^(ml|milliliters?|millilitres?)$/i,'ml',1],[/^(l|liters?|litres?)$/i,'ml',1000],
 [/^(oz\.?|ounces?)$/i,'wt',1],[/^(lbs?\.?|pounds?)$/i,'wt',16],[/^(g|grams?)$/i,'g',1],[/^(kg|kilograms?)$/i,'g',1000],
 [/^(pinch(es)?|dash(es)?)$/i,'pinch',1],
 [/^(cloves?|cans?|sticks?|slices?|bunch(es)?|heads?|packages?|pkgs?\.?|packets?|jars?|bags?|sprigs?|stalks?|pieces?)$/i,'count',1]
];
var GRAMS={'flour':120,'sugar':200,'brown sugar':213,'powdered sugar':120,'rice':185,'oats':90,'rolled oats':90,'cocoa':85,'butter':227};
var st={batch:'all'};
function num(s){
  s=s.trim();var m;
  if((m=s.match(/^(\d+)\s*([¼-¾⅐-⅞])/)))return +m[1]+UF[m[2]];
  if(UF[s[0]]!=null&&s.length===1)return UF[s[0]];
  if((m=s.match(/^(\d+)\s+(\d+)\/(\d+)$/)))return +m[1]+m[2]/m[3];
  if((m=s.match(/^(\d+)\/(\d+)$/)))return m[1]/m[2];
  if((m=s.match(/^\d*\.?\d+$/)))return +s;
  return null;
}
var QTY=/^((?:\d+\s+\d+\/\d+)|(?:\d+\s*[¼-¾⅐-⅞])|(?:\d+\/\d+)|(?:\d*\.?\d+)|[¼-¾⅐-⅞])(?:\s*(?:-|to|–)\s*((?:\d+\s+\d+\/\d+)|(?:\d+\/\d+)|(?:\d*\.?\d+)|[¼-¾⅐-⅞]))?\s*/;
function parse(line){
  var raw=line.trim();if(!raw)return null;
  var m=raw.match(QTY);
  if(!m){
    var pm=raw.match(/^(a\s+)?(pinch|dash)\b\s*(of\s+)?(.*)$/i);
    if(pm)return {raw:raw,q:1,kind:'pinch',mult:1,name:pm[4]||'',unit:pm[2].toLowerCase(),wasText:'a '+pm[2].toLowerCase()};
    return {raw:raw,q:null,name:raw};
  }
  var q=num(m[1]),q2=m[2]?num(m[2]):null,rest=raw.slice(m[0].length);
  var wm=rest.match(/^([A-Za-z.]+(?:\s?oz\.?)?)\s*(.*)$/),kind='each',mult=1,unit='',name=rest;
  if(wm){
    var first=wm[1];
    for(var i=0;i<UNITS.length;i++){if(UNITS[i][0].test(first)){kind=UNITS[i][1];mult=UNITS[i][2];unit=first;name=wm[2];break}}
    if(kind==='each'&&/^fl$/i.test(first)){var w2=rest.match(/^fl\.?\s?oz\.?\s*(.*)$/i);if(w2){kind='vol';mult=6;unit='fl oz';name=w2[1]}}
  }
  name=name.replace(/^of\s+/i,'');
  return {raw:raw,q:q,q2:q2,kind:kind,mult:mult,unit:unit,name:name};
}
function frac(x,den){
  var w=Math.floor(x+1e-9),f=x-w,n=Math.round(f*den);
  if(n===den){w++;n=0}
  var g=function(a,b){return b?g(b,a%b):a},d=den;if(n){var k=g(n,d);n/=k;d/=k}
  return (w?w:'')+(w&&n?' ':'')+(n?n+'/'+d:'')||'0';
}
function volText(tsp){
  if(tsp<=0)return '0';
  if(tsp<3){var t=tsp<1?Math.max(.125,Math.round(tsp*8)/8):Math.round(tsp*4)/4;return frac(t,8)+' tsp'}
  if(tsp<12||(tsp<24&&Math.abs(tsp/12-Math.round(tsp/12))>.05&&Math.abs(tsp/16-Math.round(tsp/16))>.05)){var tb=Math.floor(tsp/3*2+1e-9)/2,r=Math.round((tsp-tb*3)*4)/4;if(r>=3){tb+=1;r=0}return frac(tb,2)+' tbsp'+(r>=.25?' + '+frac(r,4)+' tsp':'')}
  var thirds=tsp/16,quarters=tsp/12;
  if(Math.abs(thirds-Math.round(thirds))<.08&&Math.round(thirds)%3!==0)return frac(Math.round(thirds)/3,3)+' cup'+(thirds>3.01?'s':'');
  var qc=Math.floor(quarters+1e-9),rem=tsp-qc*12,rt=Math.round(rem/3*2)/2;
  if(rt>=4){qc++;rt=0}
  var cups=qc/4;
  return (cups?frac(cups,4)+' cup'+(cups>1?'s':''):'')+(rt?(cups?' + ':'')+frac(rt,2)+' tbsp':'');
}
function wtText(oz){if(oz>=16){var lb=Math.round(oz/16*4)/4;return frac(lb,4)+' lb'}return (oz<1?frac(Math.round(oz*4)/4,4):Math.round(oz*2)/2)+' oz'}
function gText(g){return g>=1000?(Math.round(g/100)/10)+' kg':(g<20?Math.round(g):Math.round(g/5)*5)+' g'}
function mlText(ml){return ml>=1000?(Math.round(ml/100)/10)+' L':Math.round(ml/5)*5+' ml'}
function gramsFor(name){var n=name.toLowerCase(),best=null;Object.keys(GRAMS).forEach(function(k){if(n.indexOf(k)>=0&&(!best||k.length>best.length))best=k});return best?GRAMS[best]:null}
function scaleLine(p,f){
  if(!p)return null;
  if(p.q==null)return {amt:'',name:p.name,note:'No amount to scale. Season to taste.'};
  var q=p.q*f,q2=p.q2!=null?p.q2*f:null,note='',was=p.raw.slice(0,p.raw.length-p.name.length).trim();
  if(p.kind==='vol'){
    var t=q*p.mult,a=volText(t);
    if(q2!=null)a=volText(t)+' to '+volText(q2*p.mult);
    var gpc=gramsFor(p.name);
    if(gpc&&t>=48)note='About '+gText(t/48*gpc)+' if you weigh it.';
    if(/butter/i.test(p.name)&&t>=24){var sk=Math.round(t/24*4)/4;note='About '+frac(sk,4)+' stick'+(sk>1?'s':'')+'.'}
    return {amt:a,name:p.name,note:note,was:was};
  }
  if(p.kind==='wt')return {amt:wtText(q*p.mult)+(q2!=null?' to '+wtText(q2*p.mult):''),name:p.name,note:'',was:was};
  if(p.kind==='g')return {amt:gText(q*p.mult)+(q2!=null?' to '+gText(q2*p.mult):''),name:p.name,note:'',was:was};
  if(p.kind==='ml')return {amt:mlText(q*p.mult)+(q2!=null?' to '+mlText(q2*p.mult):''),name:p.name,note:'',was:was};
  if(p.kind==='pinch'){was=p.wasText||was;var pn=Math.max(1,Math.round(q));return {amt:pn>=8?frac(Math.round(pn/8*8)/8,8)+' tsp':pn+' '+p.unit+(pn>1?'es':''),name:p.name,note:pn>=8?'That many pinches is about '+frac(pn/8,8)+' tsp.':'',was:was}}
  var whole=Math.ceil(q-1e-9),u=p.unit?p.unit.replace(/s$/i,''):'';
  if(Math.abs(q-whole)>.01)note='Rounded up from '+(Math.round(q*10)/10)+'.';
  if(/\beggs?\b/i.test(p.name)&&whole>=6){var dz=Math.ceil(whole/12);note=(note?note+' ':'')+'Buy '+dz+' dozen.'}
  var hi=q2!=null?Math.ceil(q2-1e-9):null,top=hi||whole;
  var label=(hi&&hi!==whole?whole+' to '+hi:String(whole))+(u?' '+u+(top>1&&!/s$/.test(u)?(/(ch|sh)$/.test(u)?'es':'s'):''):'');
  if(hi)note='';
  return {amt:label,name:p.name,note:note,was:was};
}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var lastRows=[];
function render(){
  var serves=Math.max(1,parseFloat(document.getElementById('serves').value)||1);
  var A=Math.max(0,parseFloat(document.getElementById('adults').value)||0),K=Math.max(0,parseFloat(document.getElementById('kids').value)||0);
  var portions=A+K/2,f=portions/serves,batches=f>3?Math.ceil(f/2.5):1;
  var showF=st.batch==='one'&&batches>1?f/batches:f;
  document.getElementById('fac').textContent='×'+(Math.round(f*100)/100);
  document.getElementById('facl').textContent=(Math.round(portions*10)/10)+' portions from a recipe that serves '+serves+'.';
  document.getElementById('warn').innerHTML=batches>1?'<p class="warn"><b>Make it in '+batches+' batches.</b> Most home pots, pans and mixing bowls top out at two or three times a recipe. Past that, things cook unevenly and pans crowd. Switch to "One batch" for the amounts per round.</p>':'';
  document.getElementById('batchrow').hidden=batches<2;
  if(batches<2)st.batch='all';
  document.querySelectorAll('[data-b]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.b===st.batch))});
  var rows=document.getElementById('rec').value.split(/\n/).map(parse).filter(Boolean).map(function(p){return scaleLine(p,showF)});
  lastRows=rows;
  document.getElementById('out').innerHTML=rows.map(function(r){return '<tr><td class="amt">'+esc(r.amt)+(r.was?'<span class="was">was '+esc(r.was)+'</span>':'')+'</td><td>'+esc(r.name)+'</td><td class="note">'+esc(r.note||'')+'</td></tr>'}).join('')||'<tr><td colspan="3" class="note">Paste some ingredients to start.</td></tr>';
}
document.addEventListener('click',function(e){var b=e.target.closest('[data-b]');if(b){st.batch=b.dataset.b;render()}});
['rec','serves','adults','kids'].forEach(function(id){document.getElementById(id).addEventListener('input',render)});
document.getElementById('copy').addEventListener('click',function(){djCopy(lastRows.map(function(r){return '[ ] '+(r.amt?r.amt+' ':'')+r.name+(r.note&&/Buy|stick|weigh/.test(r.note)?' ('+r.note.replace(/\.$/,'')+')':'')}).join('\n'),'Shopping list')});
document.getElementById('print').addEventListener('click',function(){window.print()});
render();
})();
"""

write(sys.argv[1], "scaler.html",
      title="Recipe Scaler",
      description="A free recipe scaler for classrooms, kitchens and events: paste any ingredient list, set grown-ups and kids, and get amounts you can actually measure, plus when to split into batches.",
      kicker="Free tool · runs in your browser",
      h1="Any recipe.<br>Any crowd.",
      lede="Paste any ingredient list and say who's eating. Kids count as half a portion. You get amounts you can actually measure, like \"1/4 cup + 2 tbsp\" instead of 0.375 cups, eggs rounded up, butter in sticks, and a heads-up when it's time to cook in batches.",
      css=CSS, body=BODY, script=SCRIPT,
      cta_h="Built from a real kitchen", cta_p="This is one trick from a cooking app I'm building for a Sonoma County children's nonprofit. If your program has a binder of recipes or lessons, start with a free 15-minute call.",
      cta_href="call.html", cta_btn="Free 15-minute call")
