"""The picture viewer (T-44, Nov 23, 2026): tap an app screenshot to see it big, and get back out with zero effort.

One piece, used everywhere an app screenshot shows: tools/studio.py (the Studio gallery, a product card's or a
product page's picture) and enhance.py (the Bird League Then and Now on work.html). tools/board.py rebuilds the
Studio pages through studio.py, so it carries the viewer too.

- link(img, href, group): the picture wrapped in a link to its own file, with the zoom mark (a magnifier, no words)
  on its bottom right corner, mostly outside the picture (T-44: no corner is empty in every screenshot; this one
  reaches about 8px in, under the tab bars' labels). With scripts off a tap opens the file and the browser's back returns. Pictures with the
  same group (one app's gallery block) are stepped through together; a picture with no group stands alone (no
  counter, no arrows).
- CSS: the link, the mark (written in the old palette, so theme.py maps it by role like every light-page color) and
  the viewer. The viewer stays dark on every page, so its colors are written in the new palette and theme.py keeps
  them as they are (VIEWER in theme.py).
- SCRIPT: the viewer. It builds itself on the first tap, so a page without scripts carries none of it. Its only
  words are the screen reader labels "Close", "Previous picture" and "Next picture", the counter "3 of 9", and each
  picture's own alt text and caption, reused as the page writes them.
- page(html): CSS and SCRIPT added to a page that isn't built by chrome.page() (work.html).

Getting out, every way works on the first try: the Close button, a tap on the backdrop, a single tap on the picture
(unless zoomed in: then a tap fits it back), Esc, the phone's back button or back swipe (one history entry is pushed
on open and taken back by every other way of closing, so back never needs two presses and never leaves the page), and
a swipe down (or up). Closing puts the page back at the same scroll with focus on the picture that was tapped. An
impatient second tap is swallowed: for 0.3 s after closing any tap, and for 0.8 s a tap where the closing tap landed,
so it can't open another picture or the menu under the Close button. A tap on the picture closes at once (no double tap
to zoom, so a double tap never leaves it zoomed in).
Inside: pinch to zoom (Ctrl and the wheel with a mouse; the page behind never scrolls or zooms); swipe sideways, the
arrow keys, or the two arrow buttons (mouse only) step through the block and stop at its ends. On a phone the picture
runs edge to edge. Open and close fade in 200 ms; with reduced motion they are instant.
"""

MARK = ('<span class="zm-i" aria-hidden="true"><svg viewBox="0 0 24 24" width="14" height="14" focusable="false">'
        '<circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2.2"/>'
        '<path d="M15.6 15.6L20.5 20.5M10.5 7.6v5.8M7.6 10.5h5.8" fill="none" stroke="currentColor" '
        'stroke-width="2.2" stroke-linecap="round"/></svg></span>')


def link(img, href, group=None):
    """An <img> wrapped in the link that opens it: its own file, or the viewer when scripts are on."""
    g = f' data-zg="{group}"' if group else ""
    return f'<a class="zm" href="{href}"{g}>{img}{MARK}</a>'


CSS = r"""
a.zm{position:relative;display:block;cursor:zoom-in;color:inherit;-webkit-tap-highlight-color:transparent}
.zm-i{position:absolute;right:-8px;bottom:-8px;z-index:1;width:24px;height:24px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:#FBF8F1;color:#16201C;border:1px solid #CFC6B2;opacity:.9;pointer-events:none}
.zm-i svg{display:block}
a.zm:hover .zm-i{opacity:1}
.dj a.zm:focus-visible{outline:3px solid #E8592B;outline-offset:3px}
html.zv-lock{overflow:hidden}
.zv{position:fixed;inset:0;z-index:9999;font-family:'Instrument Sans','Helvetica Neue',system-ui,sans-serif;-webkit-font-smoothing:antialiased;opacity:0;transition:opacity .2s ease;touch-action:none;overscroll-behavior:contain;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
.zv[hidden]{display:none}
.zv.on{opacity:1}
.zv-bg{position:absolute;inset:0;background:rgba(23,33,43,.98)}
.zv-img{position:absolute;max-width:none;transform-origin:0 0;transition:transform .2s ease,opacity .2s ease;border-radius:2px;-webkit-user-drag:none;cursor:zoom-out}
.zv-cap{position:absolute;left:0;right:0;margin:0 auto;max-width:36em;padding:0 16px;text-align:center;color:#F7F9F3;font-size:15px;line-height:1.45}
.zv-n{position:absolute;left:max(16px,env(safe-area-inset-left));top:max(8px,env(safe-area-inset-top));margin:0;line-height:48px;font-family:'JetBrains Mono',monospace;font-size:14px;letter-spacing:.06em;color:#B9C3CC}
.zv button{position:absolute;display:flex;align-items:center;justify-content:center;width:48px;height:48px;margin:0;padding:0;border:0;border-radius:50%;cursor:pointer;font:inherit}
.zv-x{top:max(8px,env(safe-area-inset-top));right:max(8px,env(safe-area-inset-right));background:#F7F9F3;color:#17212B;box-shadow:0 1px 6px rgba(0,0,0,0.45)}
.zv .zv-p,.zv .zv-nx{display:none;top:50%;margin-top:-24px;background:rgba(247,249,243,.14);color:#F7F9F3}
.zv-p{left:max(12px,env(safe-area-inset-left))}
.zv-nx{right:max(12px,env(safe-area-inset-right))}
@media (hover:hover) and (pointer:fine){.zv .zv-p,.zv .zv-nx{display:flex}.zv .zv-p:hover,.zv .zv-nx:hover{background:rgba(247,249,243,.26)}}
.zv.zv-solo .zv-p,.zv.zv-solo .zv-nx,.zv.zv-solo .zv-n{display:none}
.zv [aria-disabled=true]{opacity:.3;cursor:default}
.zv-cap,.zv-n{transition:opacity .2s ease}
.zv.zv-z .zv-cap,.zv.zv-z .zv-n{opacity:0}
.zv button:focus-visible{outline:3px solid #E8592B;outline-offset:3px}
@media (prefers-reduced-motion:reduce){.zv,.zv-img,.zv-cap,.zv-n{transition:none}}
"""

SCRIPT = r"""
(function(){
var D=document,R=D.documentElement;
if(!D.querySelector('a.zm')||!window.history||!history.pushState)return;
var RM=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
var SVG='<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false"><path fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" d="';
var box,bg,img,cap,cnt,bP,bN,bX,list=[],i=0,opener=null,sx=0,sy=0,open=false,backWait=0,openedAt=0,closedAt=0,inerted=[];
var nw=1,nh=1,FX=0,FY=0,W=0,H=0,z={s:1,x:0,y:0},ptrs={},g=null,tapT=0;
function el(t,c,a){var e=D.createElement(t);if(c)e.className=c;for(var k in a)e.setAttribute(k,a[k]);return e}
function btn(c,label,d,fn){var b=el('button',c,{type:'button','aria-label':label});b.innerHTML=SVG+d+'"/></svg>';b.addEventListener('click',function(e){e.stopPropagation();fn(e)});return b}
var shield={t:0,x:-99,y:-99};
function shieldAt(x,y){shield={t:Date.now(),x:x,y:y}}
D.addEventListener('click',function(e){var dt=Date.now()-shield.t;if(open||dt>800)return;
  if(dt<300||(Math.abs(e.clientX-shield.x)<64&&Math.abs(e.clientY-shield.y)<64)){e.preventDefault();e.stopPropagation()}},true);
function build(){
  box=el('div','zv',{role:'dialog','aria-modal':'true','aria-labelledby':'zv-img'});box.hidden=true;
  bg=el('div','zv-bg');img=el('img','zv-img',{id:'zv-img',alt:'',draggable:'false'});cap=el('p','zv-cap');cnt=el('p','zv-n');
  bP=btn('zv-p','Previous picture','M15 5l-7 7 7 7',function(){go(-1)});
  bN=btn('zv-nx','Next picture','M9 5l7 7-7 7',function(){go(1)});
  bX=btn('zv-x','Close','M6 6l12 12M18 6L6 18',function(){var r=bX.getBoundingClientRect();shieldAt(r.left+r.width/2,r.top+r.height/2);hide()});
  [bg,img,cap,cnt,bP,bN,bX].forEach(function(e){box.appendChild(e)});
  D.body.appendChild(box);
  box.addEventListener('pointerdown',down);box.addEventListener('pointermove',move);
  box.addEventListener('pointerup',up);box.addEventListener('pointercancel',up);
  box.addEventListener('click',tap);
  box.addEventListener('wheel',wheel,{passive:false});
  box.addEventListener('touchmove',function(e){e.preventDefault()},{passive:false});
  ['gesturestart','gesturechange'].forEach(function(n){box.addEventListener(n,function(e){e.preventDefault()})});
  addEventListener('resize',function(){if(open){reset(true);fit()}});
}
function group(a){var k=a.getAttribute('data-zg');return k?[].filter.call(D.querySelectorAll('a.zm'),function(x){return x.getAttribute('data-zg')===k}):[a]}
function show(a){
  if(open||backWait)return;
  if(!box)build();
  list=group(a);i=list.indexOf(a);opener=a;sx=scrollX;sy=scrollY;open=true;openedAt=Date.now();
  history.pushState({zv:1},'');
  R.classList.add('zv-lock');
  [].forEach.call(D.body.children,function(c){if(c!==box&&c.tagName!=='SCRIPT'&&!c.hasAttribute('inert')){c.setAttribute('inert','');inerted.push(c)}});
  box.classList.toggle('zv-solo',list.length<2);box.classList.remove('on');box.hidden=false;
  load(0);void box.offsetWidth;box.classList.add('on');
  bX.focus({preventScroll:true});
}
function hide(pop){
  if(!open)return;
  open=false;closedAt=Date.now();clearTimeout(tapT);tapT=0;ptrs={};
  inerted.forEach(function(c){c.removeAttribute('inert')});inerted=[];
  box.classList.remove('on');
  R.classList.remove('zv-lock');
  if(scrollX!==sx||scrollY!==sy)scrollTo(sx,sy);
  if(opener)opener.focus({preventScroll:true});
  var done=function(){if(!open){box.hidden=true;img.removeAttribute('src');reset(true)}};
  if(RM)done();else setTimeout(done,200);
  if(!pop){backWait=1;history.back();setTimeout(function(){backWait=0},1000)}
}
addEventListener('popstate',function(){
  if(backWait){backWait=0;if(scrollX!==sx||scrollY!==sy)scrollTo(sx,sy);return}
  if(open){hide(true);if(scrollX!==sx||scrollY!==sy)scrollTo(sx,sy)}
});
D.addEventListener('click',function(e){
  var a=e.target.closest&&e.target.closest('a.zm');
  if(!a||e.defaultPrevented||e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
  e.preventDefault();show(a);
});
function load(d){
  var a=list[i],t=a.querySelector('img'),f=a.closest('figure'),fc=f&&f.querySelector('figcaption');
  reset(true);
  nw=+t.getAttribute('width')||t.naturalWidth||1;nh=+t.getAttribute('height')||t.naturalHeight||1;
  img.src=a.getAttribute('href');img.alt=t.alt;
  cap.innerHTML=fc?fc.innerHTML:'';cap.hidden=!fc;
  cnt.textContent=list.length>1?(i+1)+' of '+list.length:'';
  bP.setAttribute('aria-disabled',String(i===0));bN.setAttribute('aria-disabled',String(i===list.length-1));
  fit();
  if(d&&!RM){img.style.transition='none';img.style.opacity='0';img.style.transform='translate('+(d*48)+'px,0)';void img.offsetWidth;img.style.transition='';img.style.opacity='';img.style.transform=''}
  [i-1,i+1].forEach(function(k){if(list[k])(new Image()).src=list[k].getAttribute('href')});
}
function fit(){
  var vw=box.clientWidth,vh=box.clientHeight,side=bP.getClientRects().length?72:vw<600?0:12;
  var top=bX.offsetTop+bX.offsetHeight+8,bot=16;
  cap.style.top='0px';var ch=cap.hidden?0:cap.offsetHeight+12;
  var s=Math.min((vw-2*side)/nw,(vh-top-bot-ch)/nh,1);
  W=Math.round(nw*s);H=Math.round(nh*s);
  FX=Math.round((vw-W)/2);FY=Math.round(top+Math.max(0,(vh-top-bot-ch-H)/2));
  img.style.width=W+'px';img.style.height=H+'px';img.style.left=FX+'px';img.style.top=FY+'px';
  cap.style.top=(FY+H+12)+'px';
}
function apply(){box.classList.toggle('zv-z',z.s>1);img.style.transform=z.s===1&&!z.x&&!z.y?'':'translate('+z.x+'px,'+z.y+'px) scale('+z.s+')'}
function reset(now){z={s:1,x:0,y:0};if(now)img.style.transition='none';apply();bg.style.opacity='';if(now){void img.offsetWidth;img.style.transition=''}}
function clamp(){
  var vw=box.clientWidth,vh=box.clientHeight,sw=W*z.s,sh=H*z.s;
  z.x=sw<=vw?(vw-sw)/2-FX:Math.min(-FX,Math.max(vw-sw-FX,z.x));
  z.y=sh<=vh?(vh-sh)/2-FY:Math.min(-FY,Math.max(vh-sh-FY,z.y));
}
function zoomAt(cx,cy,s){
  var qx=(cx-FX-z.x)/z.s,qy=(cy-FY-z.y)/z.s;
  z.s=Math.max(1,Math.min(4,s));z.x=cx-FX-qx*z.s;z.y=cy-FY-qy*z.s;
  if(z.s<=1.02)z={s:1,x:0,y:0};else clamp();
  apply();
}
function go(d){var k=i+d;if(!open||k<0||k>=list.length)return;i=k;load(d)}
function onImg(x,y){var r=img.getBoundingClientRect();return x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom}
function tap(e){
  if(e.target.closest('button'))return;
  if((g&&g.moved)||!open||Date.now()-openedAt<400)return;
  if(z.s>1&&onImg(e.clientX,e.clientY)){zoomAt(e.clientX,e.clientY,1);return}
  shieldAt(e.clientX,e.clientY);hide();
}
function pts(){var k=Object.keys(ptrs);return k.map(function(id){return ptrs[id]})}
function pinch(){var p=pts();return {d:Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y)||1,x:(p[0].x+p[1].x)/2,y:(p[0].y+p[1].y)/2}}
function down(e){
  if(e.button>0||e.target.closest('button'))return;
  if(e.pointerType==='mouse')e.preventDefault();
  try{box.setPointerCapture(e.pointerId)}catch(_){}
  ptrs[e.pointerId]={x:e.clientX,y:e.clientY};
  var n=pts().length;
  if(n===1)g={mode:'',x0:e.clientX,y0:e.clientY,t0:Date.now(),moved:false,zx:z.x,zy:z.y,dx:0,dy:0};
  else if(n===2&&g){var p=pinch();g.mode='pinch';g.moved=true;g.p=p;g.s0=z.s;g.zx=z.x;g.zy=z.y;img.style.transition='none'}
}
function move(e){
  if(!ptrs[e.pointerId]||!g)return;
  ptrs[e.pointerId]={x:e.clientX,y:e.clientY};
  if(g.mode==='pinch'){
    if(pts().length<2)return;
    var p=pinch(),s=Math.max(.8,Math.min(5,g.s0*p.d/g.p.d)),qx=(g.p.x-FX-g.zx)/g.s0,qy=(g.p.y-FY-g.zy)/g.s0;
    z.s=s;z.x=p.x-FX-qx*s;z.y=p.y-FY-qy*s;apply();return;
  }
  var dx=e.clientX-g.x0,dy=e.clientY-g.y0;
  if(!g.mode){
    if(Math.abs(dx)<8&&Math.abs(dy)<8)return;
    g.moved=true;clearTimeout(tapT);tapT=0;
    g.mode=z.s>1?'pan':Math.abs(dy)>Math.abs(dx)?'down':'side';img.style.transition='none';
  }
  if(g.mode==='pan'){z.x=g.zx+dx;z.y=g.zy+dy;apply()}
  else if(g.mode==='down'){g.dy=dy;img.style.transform='translate(0,'+dy+'px)';bg.style.opacity=String(1-Math.min(.6,Math.abs(dy)/360))}
  else{g.edge=list.length<2||(dx>0&&i===0)||(dx<0&&i===list.length-1);g.dx=g.edge?dx/3:dx;img.style.transform='translate('+g.dx+'px,0)'}
}
function up(e){
  if(!ptrs[e.pointerId])return;
  delete ptrs[e.pointerId];
  var left=pts();
  if(!g)return;
  if(g.mode==='pinch'){
    if(left.length===1){g.mode='pan';g.x0=left[0].x;g.y0=left[0].y;g.zx=z.x;g.zy=z.y;return}
    if(left.length)return;
    img.style.transition='';settle();return;
  }
  if(left.length)return;
  img.style.transition='';
  var dt=Math.max(1,Date.now()-g.t0);
  if(g.mode==='down'){
    if(Math.abs(g.dy)>64||(Math.abs(g.dy)>24&&Math.abs(g.dy)/dt>.3)){hide();return}
    img.style.transform='';bg.style.opacity='';
  }else if(g.mode==='side'){
    if(!g.edge&&(Math.abs(g.dx)>60||(Math.abs(g.dx)>25&&Math.abs(g.dx)/dt>.5)))go(g.dx<0?1:-1);else img.style.transform='';
  }else if(g.mode==='pan'){settle()}
}
function settle(){if(z.s<=1.02)z={s:1,x:0,y:0};else{if(z.s>4)zoomAt(box.clientWidth/2,box.clientHeight/2,4);clamp()}apply()}
function wheel(e){
  e.preventDefault();
  if(e.ctrlKey){img.style.transition='none';zoomAt(e.clientX,e.clientY,z.s*Math.exp(-e.deltaY*.01));void img.offsetWidth;img.style.transition=''}
}
D.addEventListener('keydown',function(e){
  if(!open)return;
  var k=e.key;
  if(k==='Escape'||k==='Esc'){e.preventDefault();hide()}
  else if(e.altKey||e.ctrlKey||e.metaKey)return;
  else if(k==='ArrowRight'){e.preventDefault();go(1)}
  else if(k==='ArrowLeft'){e.preventDefault();go(-1)}
  else if(k==='Tab'){
    var f=[bP,bN,bX].filter(function(b){return b.getClientRects().length}),a=D.activeElement,first=f[0],last=f[f.length-1];
    if(e.shiftKey&&(a===first||!box.contains(a))){e.preventDefault();last.focus()}
    else if(!e.shiftKey&&(a===last||!box.contains(a))){e.preventDefault();first.focus()}
  }
  else if(/^(ArrowUp|ArrowDown|PageUp|PageDown|Home|End)$/.test(k)||(k===' '&&!(e.target.closest&&e.target.closest('button')))){e.preventDefault()}
});
})();
"""


def page(html):
    """The viewer's CSS and script added to a finished page that holds at least one link(), once."""
    assert html.count('class="zm"') >= 1, "zoom.page(): no picture to zoom"
    assert html.count("</head>") == 1 and html.count("</body>") == 1, "zoom.page(): needs one </head> and one </body>"
    assert "data-zoom" not in html, "zoom.page(): already added"
    html = html.replace("</head>", f"<style data-zoom>{CSS}</style>\n</head>", 1)
    return html.replace("</body>", f"<script data-zoom>{SCRIPT}</script>\n</body>", 1)
