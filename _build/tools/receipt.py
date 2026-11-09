from chrome import write
import sys

CSS = r"""
.lay{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,440px);gap:28px;align-items:start}
@media (max-width:900px){.lay{grid-template-columns:minmax(0,1fr)}}
.line{display:grid;grid-template-columns:minmax(0,1fr) 84px 168px 44px;gap:8px;align-items:center;padding:10px 0;border-top:1px solid #DDD5C3}
.line:first-child{border-top:0}
.line input,.line select{min-height:44px;padding:8px 10px}
.line .v{grid-column:1/-1;font-size:13px;color:#5A635D;margin-top:-2px}
.line .x{font:inherit;cursor:pointer;min-height:44px;border:1.5px solid #CFC6B2;background:transparent;border-radius:2px;font-size:20px;line-height:1;color:#5A635D}
.line .x:hover{border-color:#16201C;color:#16201C}
@media (max-width:560px){.line{grid-template-columns:minmax(0,1fr) 80px 44px}.line .per{grid-column:1/3}}
.chip.add::before{content:'+ ';font-weight:700}
.chip.used{opacity:.45}
.paper{background:#FFFDF7;color:#16201C;font-family:'JetBrains Mono',ui-monospace,monospace;font-size:14px;line-height:1.55;padding:28px 26px 34px;box-shadow:0 24px 48px rgba(22,32,28,.18),0 2px 0 rgba(22,32,28,.08);position:relative;
  -webkit-mask:linear-gradient(#000 0 0) top/100% calc(100% - 12px) no-repeat,conic-gradient(from -45deg at bottom,#0000,#000 1deg 89deg,#0000 90deg) bottom/16px 12px repeat-x;
  mask:linear-gradient(#000 0 0) top/100% calc(100% - 12px) no-repeat,conic-gradient(from -45deg at bottom,#0000,#000 1deg 89deg,#0000 90deg) bottom/16px 12px repeat-x}
.paper h2{font-family:'JetBrains Mono',monospace;font-size:16px;letter-spacing:.14em;text-align:center;margin:0}
.paper .c{text-align:center;color:#5A635D;margin:2px 0 0}
.paper hr{border:0;border-top:1.5px dashed #9AA097;margin:14px 0}
.rl{display:flex;justify-content:space-between;gap:12px}
.rl span:first-child{min-width:0;overflow-wrap:anywhere}
.rl span:last-child{white-space:nowrap;text-align:right}
.rs{color:#5A635D;font-size:12.5px;margin:0 0 8px}
.tot{font-weight:700;font-size:17px}
.big2{font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;font-size:44px;line-height:1;color:#C2461B;text-align:center;margin:6px 0 2px}
.tag2{display:inline-block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;padding:1px 6px;border:1px solid currentColor;border-radius:2px;margin-top:2px}
.t-draft{color:#1F4FA8}.t-form{color:#2E7D4F}.t-connect{color:#7A4FB0}.t-tool{color:#A93F17}.t-human{color:#5A635D}.t-look{color:#8A6A12}
@media print{.noprint{display:none!important}body{background:#fff}.lay{display:block}.paper{box-shadow:none;-webkit-mask:none;mask:none;border:1px dashed #999;max-width:440px;margin:0 auto}}
"""

BODY = r"""
  <div class="lay">
    <div style="display:flex;flex-direction:column;gap:24px;min-width:0" class="noprint">
      <section class="panel" aria-labelledby="a-h">
        <h2 id="a-h" class="label">Tap the chores that eat your week</h2>
        <div class="chips" id="presets"></div>
      </section>
      <section class="panel" aria-labelledby="b-h">
        <h2 id="b-h" class="label">How long, how often</h2>
        <p class="private" style="margin-bottom:6px">Guess. Close is good enough. Change any name to match how you'd say it.</p>
        <div id="lines"></div>
        <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin-top:16px">
          <button type="button" class="btn ghost" id="addown">+ Something else</button>
          <label style="display:flex;flex-direction:column;gap:6px;max-width:260px"><span class="label" style="margin:0">What an hour of it is worth</span>
            <span style="display:flex;align-items:center;gap:8px"><span style="font-size:20px">$</span><input id="rate" type="number" min="0" step="1" value="30" style="width:110px"><span>an hour</span></span></label>
        </div>
        <p class="private" style="margin-top:8px">Their pay if staff do it. Yours if you do it, which is usually more than you think.</p>
      </section>
    </div>

    <div style="display:flex;flex-direction:column;gap:16px;position:sticky;top:16px">
      <div class="paper" id="paper" aria-live="polite"></div>
      <div class="noprint" style="display:flex;flex-wrap:wrap;gap:10px">
        <a class="btn hot" id="bring" href="start.html">Bring this receipt to a Blueprint</a>
        <button type="button" class="btn ghost" id="copy">Copy it</button>
        <button type="button" class="btn ghost" id="print">Print it</button>
      </div>
      <p class="private noprint">The "can come back" numbers are a rough rule of thumb for each kind of chore, not a promise. Day 1 of a Blueprint is where the real numbers come from. Nothing you type here leaves this page unless you press the orange button.</p>
    </div>
  </div>
"""

SCRIPT = r"""
(function(){
var V={
 draft:['AI drafts it, you approve',0.6],
 form:['A form or a setting fixes it. No AI needed.',0.75],
 connect:['Connect the apps you already have',0.7],
 tool:['A one-time build',0.7],
 human:['Keep this human. It is the job.',0],
 look:['Worth a look on Day 1',0.3]
};
var PRESETS=[
 ['Answering the same questions',30,'day','draft'],
 ['Booking and rescheduling',20,'day','form'],
 ['Copying info between apps',30,'day','connect'],
 ['Writing social posts',90,'week','draft'],
 ['Editing videos or photos',120,'week','tool'],
 ['Invoices and chasing payments',60,'week','form'],
 ['Staff or volunteer schedules',60,'week','form'],
 ['Inventory counts and reorders',60,'week','connect'],
 ['Meeting notes and follow-ups',45,'week','draft'],
 ['The newsletter',120,'month','draft'],
 ['Grant or donor reports',360,'month','draft'],
 ['Talking with customers and families',60,'day','human']
];
var PER={day:['a workday',250],week:['a week',50],month:['a month',12]};
var lines=[];
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function money(n){return '$'+Math.round(n).toLocaleString('en-US')}
function hrs(n){return (n<10?(Math.round(n*10)/10):Math.round(n)).toLocaleString('en-US')+' hr'}
function addPreset(i){var p=PRESETS[i];lines.push({name:p[0],min:p[1],per:p[2],v:p[3],pi:i});renderLines();renderReceipt()}
function renderPresets(){
  document.getElementById('presets').innerHTML=PRESETS.map(function(p,i){var used=lines.some(function(l){return l.pi===i});
    return '<button type="button" class="chip add'+(used?' used':'')+'" data-p="'+i+'" '+(used?'aria-disabled="true"':'')+'>'+esc(p[0])+'</button>'}).join('');
}
function renderLines(){
  renderPresets();
  var el=document.getElementById('lines');
  if(!lines.length){el.innerHTML='<p class="private" style="padding:12px 0">Tap a chore above to start your receipt.</p>';return}
  el.innerHTML=lines.map(function(l,i){
    return '<div class="line" data-i="'+i+'"><input aria-label="Chore" data-f="name" value="'+esc(l.name)+'">'+
      '<input aria-label="Minutes" type="number" min="0" step="5" data-f="min" value="'+l.min+'">'+
      '<select class="per" aria-label="How often" data-f="per">'+Object.keys(PER).map(function(k){return '<option value="'+k+'"'+(l.per===k?' selected':'')+'>min '+PER[k][0]+'</option>'}).join('')+'</select>'+
      '<button type="button" class="x" data-del="'+i+'" aria-label="Remove '+esc(l.name)+'">×</button>'+
      '<span class="v">'+(l.pi==null?'<label>What fixes it? <select data-f="v" aria-label="What fixes it">'+Object.keys(V).map(function(k){return '<option value="'+k+'"'+(l.v===k?' selected':'')+'>'+V[k][0]+'</option>'}).join('')+'</select></label>':'<span class="tag2 t-'+l.v+'">'+V[l.v][0]+'</span>')+'</span></div>';
  }).join('');
}
function calc(){
  var rate=parseFloat(document.getElementById('rate').value)||0,tot=0,back=0;
  var rows=lines.map(function(l){var h=(parseFloat(l.min)||0)/60*PER[l.per][1];var b=h*V[l.v][1];tot+=h;back+=b;return {l:l,h:h,b:b}});
  return {rows:rows,tot:tot,back:back,rate:rate};
}
function finishDate(h){var d=new Date(new Date().getFullYear()+1,0,1),left=h;while(left>0){var w=d.getDay();if(w>0&&w<6)left-=8;if(left>0)d.setDate(d.getDate()+1)}return d}
function receiptText(c){
  var out=['BUSYWORK RECEIPT','dragomansjourney.com/receipt.html',''];
  c.rows.forEach(function(r){out.push(r.l.name+': '+hrs(r.h)+' a year, '+money(r.h*c.rate)+' ('+V[r.l.v][0]+')')});
  out.push('','Total: '+hrs(c.tot)+' a year, '+money(c.tot*c.rate),'Could come back: about '+hrs(c.back)+' ('+money(c.back*c.rate)+')');
  return out.join('\n');
}
function renderReceipt(){
  var c=calc(),p=document.getElementById('paper'),d=new Date();
  var head='<h2>BUSYWORK RECEIPT</h2><p class="c">'+d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})+' · 1 year of it</p><hr>';
  if(!c.rows.length){p.innerHTML=head+'<p class="c" style="padding:24px 0">Nothing rung up yet.</p>';updateBring(c);return}
  var body=c.rows.map(function(r){return '<div class="rl"><span>'+esc(r.l.name)+'</span><span>'+money(r.h*c.rate)+'</span></div><p class="rs">'+hrs(r.h)+' a year · <span class="t-'+r.l.v+'">'+V[r.l.v][0]+'</span></p>'}).join('');
  var weeks=c.tot/40, fin=finishDate(c.tot);
  var backWeek=c.back*c.rate/50, payback=backWeek>0?Math.ceil(1500/backWeek):0;
  var foot='<hr><div class="rl tot"><span>TOTAL</span><span>'+money(c.tot*c.rate)+'</span></div><div class="rl"><span>Hours</span><span>'+hrs(c.tot)+'</span></div>'+
    '<div class="rl"><span>Full work weeks</span><span>'+(Math.round(weeks*10)/10)+'</span></div><hr>'+
    '<p style="margin:0">Done all at once, starting New Year\'s Day, you\'d finish on</p><p class="big2">'+fin.toLocaleDateString('en-US',{month:'long',day:'numeric'})+'</p><hr>'+
    '<div class="rl tot"><span>COULD COME BACK</span><span>'+money(c.back*c.rate)+'</span></div><div class="rl"><span>Hours</span><span>'+hrs(c.back)+'</span></div>'+
    (payback?'<p style="margin:10px 0 0">At that pace, a $1,500 Blueprint pays for itself in about <b>'+payback+' week'+(payback===1?'':'s')+'</b>.</p>':'')+
    '<hr><p class="c">KEEP THIS RECEIPT<br>THANK YOU FOR COUNTING</p>';
  p.innerHTML=head+body+foot;updateBring(c);
}
function updateBring(c){
  var a=document.getElementById('bring');
  if(!c.rows.length){a.href='start.html';return}
  var top=c.rows.slice().sort(function(x,y){return y.h-x.h}).slice(0,4).map(function(r){return r.l.name.toLowerCase()+' ('+hrs(r.h)+' a year)'});
  var never='From my busywork receipt: '+top.join(', ')+'. About '+hrs(c.tot)+' a year in all.';
  a.href='start.html#pile='+encodeURIComponent('A weekly task that eats hours')+'&never='+encodeURIComponent(never);
}
document.addEventListener('click',function(e){
  var p=e.target.closest('[data-p]');if(p&&!p.hasAttribute('aria-disabled')){addPreset(+p.dataset.p);return}
  var x=e.target.closest('[data-del]');if(x){lines.splice(+x.dataset.del,1);renderLines();renderReceipt();return}
});
document.getElementById('lines').addEventListener('input',function(e){
  var row=e.target.closest('.line');if(!row)return;var l=lines[+row.dataset.i],f=e.target.dataset.f;if(!f)return;
  l[f]=e.target.value;if(f==='v'){renderLines()}renderReceipt();
});
document.getElementById('lines').addEventListener('change',function(e){if(e.target.dataset.f==='per'||e.target.dataset.f==='v')renderReceipt()});
document.getElementById('rate').addEventListener('input',renderReceipt);
document.getElementById('addown').addEventListener('click',function(){lines.push({name:'Something else',min:30,per:'week',v:'look',pi:null});renderLines();renderReceipt();var ins=document.querySelectorAll('#lines .line input[data-f=name]');var last=ins[ins.length-1];if(last){last.focus();last.select()}});
document.getElementById('copy').addEventListener('click',function(){djCopy(receiptText(calc()),'Receipt')});
document.getElementById('print').addEventListener('click',function(){window.print()});
[0,2,3].forEach(function(i){var p=PRESETS[i];lines.push({name:p[0],min:p[1],per:p[2],v:p[3],pi:i})});
renderLines();renderReceipt();
})();
"""

write(sys.argv[1], "receipt.html",
      title="Busywork Receipt",
      description="A free calculator for small businesses and nonprofits: ring up the chores that eat your week and see what they cost in a year, and which ones could honestly come back.",
      kicker="Free tool · runs in your browser",
      h1="Ring up your<br>busywork",
      lede="Tap the chores that eat your week. You get a receipt for a year of them: the hours, the dollars, the day you'd finish if you did them all in a row, and an honest read on which ones could come back. Some of them should stay human.",
      css=CSS, body=BODY, script=SCRIPT,
      cta_h="Want the real numbers?", cta_p="Day 1 of a Blueprint is me watching how the work actually gets done. Two weeks, $1,500, and it comes off the build price.",
      cta_href="start.html", cta_btn="Start a Blueprint →")
