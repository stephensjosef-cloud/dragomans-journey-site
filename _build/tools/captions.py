from chrome import write
import sys

CSS = r"""
.lay{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,380px);grid-template-areas:'in st' 'vd st' 'set st' 'ck st' 'sc st';grid-template-rows:auto auto auto auto 1fr;gap:24px;align-items:start}
.lay>.a-in{grid-area:in}.lay>.a-vd{grid-area:vd}.lay>.a-set{grid-area:set}.lay>.a-ck{grid-area:ck}.lay>.a-sc{grid-area:sc}.lay>.stage{grid-area:st;align-self:stretch}
.stage-in{position:sticky;top:16px;display:flex;flex-direction:column;gap:12px;align-items:center}
@media (max-width:860px){.lay{grid-template-columns:minmax(0,1fr);grid-template-areas:'in' 'st' 'vd' 'set' 'ck' 'sc';grid-template-rows:none}.stage-in{position:static}}
.verdict{display:flex;gap:12px;align-items:flex-start;margin:0;font-size:19px;font-weight:700;line-height:1.4}
.verdict .dot{width:14px;height:14px;margin-top:6px}
.phone{width:min(340px,100%);aspect-ratio:9/16;border:10px solid #16201C;border-radius:34px;overflow:hidden;background:#3B4540;position:relative}
.phone canvas{width:100%;height:100%;display:block}
.row{display:flex;flex-wrap:wrap;gap:22px 32px}
.row>div{min-width:min(240px,100%)}
.verdicts{display:flex;flex-direction:column;gap:8px;margin:0;padding:0;list-style:none}
.verdicts li{display:flex;gap:10px;align-items:flex-start;font-size:16px}
.dot{flex:none;width:12px;height:12px;border-radius:50%;margin-top:7px}
.ok{background:#2E7D4F}.warn{background:#D9A520}.bad{background:#C2461B}
.cards{display:flex;flex-direction:column;gap:10px}
.cardline{display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:center;padding:12px 14px;background:#fff;border:1.5px solid #CFC6B2;border-radius:2px;cursor:pointer;text-align:left;font:inherit;color:#16201C;width:100%}
.cardline[aria-pressed="true"]{border-color:#16201C;box-shadow:inset 4px 0 0 #E8592B}
.cardline .n{font-family:'JetBrains Mono',monospace;font-size:13px;color:#6B716A}
.cardline .t{white-space:pre-line;font-size:15px;line-height:1.35}
.cardline .s{font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700}
.legend{display:flex;flex-wrap:wrap;gap:8px 16px;font-size:13px;color:#5A635D}
.legend i{display:inline-block;width:12px;height:12px;background:rgba(232,89,43,.45);border:1px dashed #E8592B;margin-right:6px;vertical-align:-1px}
input[type=file]{padding:8px;min-height:auto;background:transparent;border-style:dashed}
"""

BODY = r"""
  <div class="lay">
      <section class="panel a-in" aria-labelledby="w-h">
        <h2 id="w-h" class="label">Your caption</h2>
        <label for="cap" class="label" style="position:absolute;left:-9999px">Caption text</label>
        <textarea id="cap" spellcheck="true">Fresh sourdough comes out of the oven at 7 every morning. Come early, because the first batch is always gone by 9.</textarea>
      </section>

      <p class="verdict a-vd" id="verdict" role="status"><span class="dot" id="v-dot" aria-hidden="true"></span><span id="v-text"></span></p>

      <div class="a-set">
        <button type="button" class="fold" id="f-look" aria-expanded="false" aria-controls="look">Change how it looks</button>
        <section class="panel" id="look" aria-labelledby="f-look" hidden style="margin-top:8px">
          <div class="row">
            <div><p class="label" id="l-size">Text size</p><div class="chips" role="group" aria-labelledby="l-size" id="c-size"></div></div>
            <div><p class="label" id="l-pos">Where on screen</p><div class="chips" role="group" aria-labelledby="l-pos" id="c-pos"></div></div>
            <div><p class="label" id="l-box">Box behind the words</p><div class="chips" role="group" aria-labelledby="l-box" id="c-box"></div></div>
            <div><p class="label" id="l-app">Which app?</p><div class="chips" role="group" aria-labelledby="l-app" id="c-app"></div></div>
            <div style="max-width:220px"><label class="label" for="secs" style="display:block">How long is your clip?</label>
              <div style="display:flex;gap:8px;align-items:center"><input id="secs" type="number" min="1" max="60" step="0.5" value="5" style="width:96px"><span>seconds</span></div></div>
            <div style="max-width:300px"><label class="label" for="bg" style="display:block">Try it on your own video</label>
              <input id="bg" type="file" accept="image/*"><p class="private" style="margin-top:6px">Add a screenshot from your video. It stays on your phone.</p></div>
          </div>
        </section>
      </div>

      <section class="panel a-ck" aria-labelledby="v-h" aria-live="polite">
        <h2 id="v-h" style="margin:0 0 12px;font-size:22px">Why</h2>
        <ul class="verdicts" id="verdicts"></ul>
      </section>

      <section class="panel a-sc" aria-labelledby="k-h">
        <h2 id="k-h" style="margin:0 0 4px;font-size:22px">Your caption, split up</h2>
        <p class="private" id="k-sub" style="margin-bottom:12px"></p>
        <div class="cards" id="cards"></div>
        <div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:16px">
          <button type="button" class="btn" id="png">Save this caption as an image</button>
          <button type="button" class="btn ghost" id="pngall">Save all of them</button>
          <button type="button" class="btn ghost" id="copy">Copy the text</button>
        </div>
        <p class="private" style="margin-top:10px">This picture is see-through except for your words. Lay it over your video in CapCut or the Instagram editor and the words land right where you see them here.</p>
      </section>

    <div class="stage"><div class="stage-in">
      <div class="phone"><canvas id="cv" width="1080" height="1920" role="img" aria-label="Preview of the caption on a phone screen"></canvas></div>
      <div class="legend"><span><i></i>Covered by the app's buttons and text (approximate)</span></div>
      <p class="private" style="text-align:center">Nothing you type or load here leaves this page.</p>
    </div></div>
  </div>
"""

SCRIPT = r"""
(function(){
var W=1080,H=1920,MARGIN=96,PADX=34,PADY=22,LH=1.2;
var SIZES={s:['Small',46],m:['Medium',54],l:['Large',64]};
var POS={top:['Top',0.30],mid:['Middle',0.50],low:['Bottom',0.66]};
var BOX={dark:['Dark box'],light:['Light box'],none:['No box']};
/* Approximate covered areas at 1080 x 1920. Apps move these now and then. */
var APPS={
 reels:{label:'Instagram Reels',z:[[0,0,1080,210],[0,1500,1080,420],[930,860,150,640]]},
 tiktok:{label:'TikTok',z:[[0,0,1080,190],[0,1460,1080,460],[920,780,160,720]]},
 shorts:{label:'YouTube Shorts',z:[[0,0,1080,180],[0,1540,1080,380],[930,900,150,620]]},
 none:{label:'No app',z:[]}
};
var st={size:'m',pos:'low',box:'dark',app:'reels',card:0};
var cv=document.getElementById('cv'),ctx=cv.getContext('2d'),bgImg=null,cards=[];

function font(){return '700 '+SIZES[st.size][1]+"px 'Instrument Sans', 'Helvetica Neue', Arial, sans-serif"}
function measure(t){ctx.font=font();return ctx.measureText(t).width}
function maxW(){var m=W-2*MARGIN-2*PADX;APPS[st.app].z.forEach(function(z){if(z[0]>W/2&&z[1]>200&&z[1]+z[3]<H-200)m=Math.min(m,2*(z[0]-W/2)-2*PADX-20)});return m}
var MAXW=0;
function wrap(words,width){
  var lines=[],cur='';
  for(var i=0;i<words.length;i++){
    var tryL=cur?cur+' '+words[i]:words[i];
    if(measure(tryL)<=width||!cur){cur=tryL}else{lines.push(cur);cur=words[i]}
  }
  if(cur)lines.push(cur);return lines;
}
/* Same number of lines as a plain wrap, but every line as even as it can be. */
function balanced(text){
  var words=text.trim().split(/\s+/).filter(Boolean);if(!words.length)return [];MAXW=maxW();
  var base=wrap(words,MAXW),n=base.length,lo=0,hi=MAXW;
  if(n===1)return base;
  for(var k=0;k<24;k++){var mid=(lo+hi)/2;if(wrap(words,mid).length<=n)hi=mid;else lo=mid}
  var out=wrap(words,hi);
  return out.length<=n?out:base;
}
var FN=/^(and|but|so|or|because|when|while|then|at|in|on|with|for|to|from|until|before|after|if|which|who|where)$/i;
var GLUE=/^(of|the|a|an|to|my|your|our|their|this|that|at|in|on|for|and|with)$/i;
function breakCost(words,j){
  var prev=words[j-1]||'';
  if(/[.!?]["')]*$/.test(prev))return 0;
  if(/[,;:]["')]*$/.test(prev))return 2;
  if(GLUE.test(prev.replace(/[^A-Za-z]/g,'')))return 30;
  if(FN.test(words[j].replace(/[^A-Za-z]/g,'')))return 5;
  return 12;
}
/* Few screens, natural breaks: sentence ends, then commas, then before joining words. Never after "of" or "the". */
function splitCards(text,maxLines){
  var words=text.replace(/\s+/g,' ').trim().split(' ').filter(Boolean),n=words.length,memo={};
  function fits(i,j){var k=i+':'+j;if(!(k in memo))memo[k]=balanced(words.slice(i,j).join(' ')).length<=maxLines;return memo[k]}
  var best=[{cards:0,cost:0,prev:-1}];
  for(var j=1;j<=n;j++){
    best[j]=null;
    for(var i=Math.max(0,j-40);i<j;i++){
      if(!best[i]||!fits(i,j))continue;
      var len=j-i,bl=balanced(words.slice(i,j).join(' ')),lone=bl.length>1&&bl[bl.length-1].split(' ').length===1;
      var inner=0;for(var q=i;q<j-1;q++)if(/[.!?]["')]*$/.test(words[q]))inner+=10;
      var c=best[i].cost+18+(i>0?breakCost(words,i):0)+(len<3?6:0)+(lone?20:0)+inner;
      var cand={cards:best[i].cards+1,cost:c,prev:i};
      if(!best[j]||cand.cost<best[j].cost)best[j]=cand;
    }
    if(!best[j])best[j]={cards:best[j-1].cards+1,cost:best[j-1].cost+50,prev:j-1};
  }
  var out=[],j2=n;while(j2>0){var i2=best[j2].prev;out.unshift(words.slice(i2,j2).join(' '));j2=i2}
  return out.map(function(t){return {text:t,lines:balanced(t)}});
}
function readSecs(t){var w=t.split(/\s+/).filter(Boolean).length;return Math.max(1.5,Math.round(w/2.8*2)/2)}

function layout(lines){
  var fs=SIZES[st.size][1],lh=fs*LH,wmax=0;
  lines.forEach(function(l){wmax=Math.max(wmax,measure(l))});
  var bw=wmax+2*PADX,bh=lines.length*lh+2*PADY,cx=W/2,cy=H*POS[st.pos][1];
  return {x:cx-bw/2,y:cy-bh/2,w:bw,h:bh,lh:lh,fs:fs};
}
function rr(x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath()}
function drawCaption(c,lines,L){
  if(st.box!=='none'){rr(L.x,L.y,L.w,L.h,30);c.fillStyle=st.box==='dark'?'rgba(14,27,23,0.86)':'rgba(251,248,241,0.94)';c.fill()}
  c.font=font();c.textAlign='center';c.textBaseline='middle';
  lines.forEach(function(l,i){
    var y=L.y+PADY+L.lh*(i+.5);
    if(st.box==='none'){c.lineWidth=10;c.strokeStyle='rgba(14,27,23,0.9)';c.lineJoin='round';c.strokeText(l,W/2,y)}
    c.fillStyle=st.box==='light'?'#16201C':'#FBF8F1';c.fillText(l,W/2,y);
  });
}
function hit(L,z){return !(L.x+L.w<=z[0]||L.x>=z[0]+z[2]||L.y+L.h<=z[1]||L.y>=z[1]+z[3])}
function draw(){
  ctx.clearRect(0,0,W,H);
  if(bgImg){var s=Math.max(W/bgImg.width,H/bgImg.height),iw=bgImg.width*s,ih=bgImg.height*s;ctx.drawImage(bgImg,(W-iw)/2,(H-ih)/2,iw,ih)}
  else{var g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,'#7C8B7A');g.addColorStop(.55,'#4B5A50');g.addColorStop(1,'#2A332E');ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    ctx.fillStyle='rgba(255,255,255,.08)';for(var i=0;i<6;i++){ctx.beginPath();ctx.arc(200+i*150,700+(i%2)*260,120,0,7);ctx.fill()}}
  APPS[st.app].z.forEach(function(z){ctx.fillStyle='rgba(232,89,43,0.30)';ctx.fillRect(z[0],z[1],z[2],z[3]);ctx.setLineDash([16,12]);ctx.strokeStyle='#E8592B';ctx.lineWidth=4;ctx.strokeRect(z[0]+2,z[1]+2,z[2]-4,z[3]-4);ctx.setLineDash([])});
  var c=cards[st.card];if(!c)return null;
  var L=layout(c.lines);drawCaption(ctx,c.lines,L);return L;
}
function chips(id,map,key){document.getElementById(id).innerHTML=Object.keys(map).map(function(k){return '<button type="button" class="chip" data-k="'+key+'" data-v="'+k+'" aria-pressed="'+(st[key]===k)+'">'+(map[k].label||map[k][0])+'</button>'}).join('')}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function render(){
  chips('c-size',SIZES,'size');chips('c-pos',POS,'pos');chips('c-box',BOX,'box');chips('c-app',APPS,'app');
  var text=document.getElementById('cap').value.trim();
  MAXW=maxW();
  cards=text?splitCards(text,2):[];
  if(st.card>=cards.length)st.card=0;
  var secs=parseFloat(document.getElementById('secs').value)||0;
  var need=cards.reduce(function(a,c){return a+readSecs(c.text)},0);
  var sub=document.getElementById('k-sub');sub.hidden=cards.length<2;sub.textContent=cards.length>1?('Two lines fit on a phone, so this caption shows in '+cards.length+' parts. Tap one to see it.'):'';
  document.getElementById('cards').innerHTML=cards.map(function(c,i){return '<button type="button" class="cardline" data-card="'+i+'" aria-pressed="'+(i===st.card)+'"><span class="n">'+(i+1)+'</span><span class="t">'+esc(c.lines.join('\n'))+'</span><span class="s">'+readSecs(c.text)+' s</span></button>'}).join('');
  var L=draw(),v=[],hits=[];
  if(!cards.length){v.push(['warn','Type a caption to check it.'])}
  else{
    var orphan=cards.some(function(c){var l=c.lines;return l.length>1&&l[l.length-1].split(' ').length===1});
    v.push(orphan?['warn','One screen ends on a single word. Add or trim a word in that sentence.']:['ok','No line is stranded on its own. Lines are balanced to even widths and kept clear of the app\'s side buttons.']);
    cards.forEach(function(c,i){var Lc=layout(c.lines);APPS[st.app].z.forEach(function(z){if(hit(Lc,z))hits.push(i+1)})});
    hits=hits.filter(function(x,i,a){return a.indexOf(x)===i});
    if(st.app==='none')v.push(['warn','No app picked. Pick the one you post to and this checks whether its buttons cover your words.']);
    else v.push(hits.length?['bad','On '+APPS[st.app].label+', the app\'s own text or buttons cover screen '+hits.join(', ')+'. Move it to the middle or use a smaller size.']:['ok','Clear of the buttons and caption area on '+APPS[st.app].label+'.']);
    if(secs){v.push(need>secs?['bad','Reading all of it takes about '+need+' seconds and the clip is '+secs+'. Cut words or hold the clip longer, or people scroll before they finish.']:['ok','About '+need+' seconds to read, and the clip runs '+secs+'. Time to spare.'])}
    var big=cards.some(function(c){return c.lines.some(function(l){return measure(l)>MAXW+1})});
    if(big)v.push(['bad','One word is too wide for the screen at this size. Pick a smaller size.']);
    if(st.size==='s')v.push(['warn','Small text reads fine on a big phone and poorly on a small one. Medium is the safer bet.']);
  }
  document.getElementById('verdicts').innerHTML=v.map(function(x){return '<li><span class="dot '+x[0]+'" aria-hidden="true"></span><span>'+x[1]+'</span></li>'}).join('');
  /* The one line under the phone (T-18): covered first, then too long, then good to go. */
  var one=!cards.length?['warn','Type a caption to check it.']:(st.app!=='none'&&hits.length)?['bad','The app\'s buttons cover part of it. Move it up.']:(secs&&need>secs)?['bad','Too long for this clip. People need about '+need+' seconds and your clip is '+secs+'.']:['ok','Good to go. It fits, and people can read it in time.'];
  document.getElementById('v-dot').className='dot '+one[0];
  var vt=document.getElementById('v-text');if(vt.textContent!==one[1])vt.textContent=one[1];
}
function pngFor(i,cb){
  var c=document.createElement('canvas');c.width=W;c.height=H;var x=c.getContext('2d');
  var save=ctx;ctx=x;var L=layout(cards[i].lines);drawCaption(x,cards[i].lines,L);ctx=save;
  c.toBlob(function(b){var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='caption-'+(i+1)+'.png';document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},500);cb&&cb()},'image/png');
}
document.addEventListener('click',function(e){
  var b=e.target.closest('.chip[data-k]');if(b){st[b.dataset.k]=b.dataset.v;render();return}
  var k=e.target.closest('[data-card]');if(k){st.card=+k.dataset.card;render();return}
});
document.getElementById('cap').addEventListener('input',function(){clearTimeout(render.t);render.t=setTimeout(render,120)});
document.getElementById('secs').addEventListener('input',render);
document.getElementById('bg').addEventListener('change',function(e){var f=e.target.files[0];if(!f)return;var img=new Image();img.onload=function(){bgImg=img;render()};img.src=URL.createObjectURL(f)});
document.getElementById('png').addEventListener('click',function(){if(cards.length)pngFor(st.card)});
document.getElementById('pngall').addEventListener('click',function(){var i=0;(function next(){if(i<cards.length)pngFor(i++,function(){setTimeout(next,350)})})()});
document.getElementById('copy').addEventListener('click',function(){djCopy(cards.map(function(c){return c.lines.join('\n')}).join('\n\n'),'Captions')});
render();
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(render);
})();
"""

write(sys.argv[1], "captions.html",
      title="Caption Fitter",
      description="A free check for reel captions: balanced line breaks, no stranded words, clear of each app's buttons, enough time to read, and a see-through PNG to drop on your video.",
      kicker="Free tool",
      h1="Can people read the words on your video?",
      lede="Type the words that go on your video. See them on a phone, and find out if people can read them before they're gone.",
      css=CSS, body=BODY, script=SCRIPT, folds=True,
      cta_h="Rather hand it off?", cta_p="Captions are one step of the reels I make for local businesses and nonprofits. Start with a free 15-minute call.",
      cta_href="call.html", cta_btn="Free 15-minute call")
