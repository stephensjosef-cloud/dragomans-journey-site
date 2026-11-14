from chrome import write
import sys

CSS = r"""
.ctrl{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(300px,100%),1fr));gap:22px 32px}
.count{display:flex;flex-wrap:wrap;gap:10px 24px;align-items:baseline}
.count .n{font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;font-size:clamp(40px,5vw,60px);line-height:.9;color:#C2461B}
.strip{display:flex;height:44px;border:1.5px solid #16201C;border-radius:2px;overflow:hidden}
.strip span{display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-size:11px;color:#16201C;border-right:1px solid rgba(22,32,28,.35);min-width:0;overflow:hidden;white-space:nowrap}
.strip span:last-child{border-right:0}
.clip{display:grid;grid-template-columns:44px 1fr auto;gap:4px 14px;padding:14px 0;border-top:1px solid #DDD5C3}
.clip:first-of-type{border-top:0}
.clip .no{font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;font-size:30px;line-height:1;color:#16201C}
.clip .role{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:2px;align-self:start;justify-self:start}
.clip .sec{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700;color:#16201C;text-align:right}
.clip p{margin:0;grid-column:2/4;font-size:16px}
.clip .cap{grid-column:2/4;font-size:14px;color:#3B4540;margin:2px 0 0}
.clip .cap b{color:#A93F17;font-weight:700}
.spot{padding:14px 0;border-top:1px solid #DDD5C3}
.spot:first-of-type{border-top:0}
.spot h3{margin:0 0 6px;font-size:18px}
.spot ol{margin:0;padding-left:0;list-style:none;display:flex;flex-direction:column;gap:6px}
.spot li{display:flex;gap:10px;font-size:15px}
.spot li b{font-family:'JetBrains Mono',monospace;font-size:13px;min-width:2.2em;color:#A93F17}
.rules{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:6px;font-size:16px}
.offer{background:#E8592B;color:#0E1B17;border-radius:2px;padding:clamp(18px,2.4vw,28px);display:flex;flex-direction:column;gap:12px}
.offer h2{margin:0;font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;text-transform:uppercase;font-size:clamp(28px,3.4vw,40px);line-height:.95}
.offer p{margin:0;font-size:17px}
.offer .btn{background:#0E1B17;border-color:#0E1B17;color:#F2EDE1}
.r-hook{background:#F6C9B5}.r-place{background:#D9E4D2}.r-hands{background:#F2DEA8}.r-process{background:#F2DEA8}.r-detail{background:#E6DCF0}
.r-people{background:#CFE0EE}.r-customer{background:#CFE0EE}.r-reveal{background:#F6C9B5}.r-sign{background:#D9E4D2}.r-call{background:#16201C;color:#F2EDE1!important}
.stack{display:flex;flex-direction:column;gap:24px}
h1.big{text-wrap:balance}
@media print{.noprint{display:none!important}body{background:#fff}.panel{border:1px solid #999}.panel{break-inside:avoid;margin-bottom:12px}}
"""

BODY = r"""
  <section class="panel noprint" aria-labelledby="l-type">
    <p class="label" id="l-type">What do you run?</p><div class="chips" role="group" aria-labelledby="l-type" id="c-type"></div>
    <button type="button" class="fold" id="f-details" aria-expanded="false" aria-controls="details" style="margin-top:12px">Change the details</button>
    <div id="details" hidden>
      <div class="ctrl" style="margin-top:12px">
        <div><p class="label" id="l-goal">What should the reel do?</p><div class="chips" role="group" aria-labelledby="l-goal" id="c-goal"></div></div>
        <div><p class="label" id="l-len">How long?</p><div class="chips" role="group" aria-labelledby="l-len" id="c-len"></div></div>
        <div><p class="label" id="l-light">When will you film?</p><div class="chips" role="group" aria-labelledby="l-light" id="c-light"></div></div>
      </div>
    </div>
  </section>

  <section class="panel" aria-labelledby="shoot-h">
    <h2 id="shoot-h" style="margin:0 0 4px;font-size:22px">Your 10 clips. Film them in this order.</h2>
    <p class="private" style="margin-bottom:8px">Start at the top of the list and film as you go. You never walk back.</p>
    <div id="shoot"></div>
  </section>

  <div class="stack">
    <button type="button" class="fold noprint" id="f-cut" aria-expanded="false" aria-controls="cut" style="align-self:flex-start">How it gets cut together</button>
    <div id="cut" class="printopen" hidden>
      <section class="panel" aria-labelledby="edit-h">
        <h2 id="edit-h" style="margin:0 0 4px;font-size:22px">The edit: 10 clips, in the order people see them</h2>
        <p class="private" style="margin-bottom:8px">Film each one for about five seconds. The number beside it is how long it stays in the finished video.</p>
        <div id="edit"></div>
        <p class="label" style="margin-top:18px">The reel, second by second</p>
        <div class="strip" id="strip" aria-hidden="true"></div>
        <p class="private" id="striplabel" style="margin-top:8px"></p>
      </section>
    </div>
  </div>

  <section class="panel count" aria-live="polite" id="when">
    <span class="n" id="days"></span>
    <span id="dayslabel" style="font-size:18px;font-weight:600"></span>
  </section>

  <div id="offer"></div>

  <section class="panel" aria-labelledby="rules-h">
    <h2 id="rules-h" style="margin:0 0 10px;font-size:22px">Five rules for every clip</h2>
    <ul class="rules" id="rules"></ul>
  </section>

  <div class="noprint" style="display:flex;flex-wrap:wrap;gap:12px;align-items:center">
    <button type="button" class="btn" id="copy">Copy the shot list</button>
    <button type="button" class="btn ghost" id="print">Print it</button>
    <p class="private">Nothing you pick here leaves this page.</p>
  </div>
"""

SCRIPT = r"""
(function(){
var TYPES = {
 cafe:{label:'Cafe or bakery', thing:'the bake', spots:{k:'The kitchen',c:'The counter',t:'The tables',o:'Out front'}, clips:[
  ['k','Close on motion: dough hitting the bench, or milk steaming. Start on movement, not a wide shot.'],
  ['o','Your front door from the sidewalk, someone walking in.'],
  ['k','Your hands shaping, pouring or frosting. Hands, not faces.'],
  ['k','The oven door opening, or the espresso shot pulling.'],
  ['c','The case or the menu board, one slow pan left to right.'],
  ['c','You or your crew: a quick wave or a nod to camera.'],
  ['t','A regular\'s cup or plate landing on their table (ask first).'],
  ['c','The finished thing on a plate, turned slowly toward the camera.'],
  ['o','Your sign or window, in daylight.'],
  ['c','You holding up the finished thing, saying one line.']]},
 food:{label:'Restaurant or food truck', thing:'the dish', spots:{k:'The line',p:'The pass',d:'The dining room',o:'Outside'}, clips:[
  ['k','Flame, sizzle, or a knife through something crisp. Sound on.'],
  ['o','The building or truck from across the street, the line if there is one.'],
  ['k','Hands prepping one ingredient, tight on the board.'],
  ['k','The dish coming together in the pan or on the flat-top.'],
  ['p','Plating: the last garnish going on.'],
  ['k','The cook, mid-work, glancing up.'],
  ['d','A plate set down in front of a guest (ask first).'],
  ['p','The finished plate from straight above, held for three seconds.'],
  ['o','Your sign or menu board.'],
  ['d','You, one line: the dish and the day to come in.']]},
 shop:{label:'Shop or boutique', thing:'the find', spots:{f:'The floor',c:'The counter',b:'The back room',o:'Outside'}, clips:[
  ['f','Your best seller being picked up off the shelf, close.'],
  ['o','Walking in through your door, camera at chest height.'],
  ['c','Wrapping, tagging or bagging something.'],
  ['b','Unboxing new stock.'],
  ['f','One slow pan across a single shelf or rack.'],
  ['c','You behind the counter, a quick hello.'],
  ['f','A customer\'s hands trying something on or picking something up (ask first).'],
  ['o','Your window display, the whole thing.'],
  ['o','Your storefront with a little of the block around it.'],
  ['c','You, one line: what\'s new and why this Saturday.']]},
 salon:{label:'Salon, barber or studio', thing:'the work', spots:{ch:'The chair',s:'Your station',d:'The front desk',o:'Outside'}, clips:[
  ['ch','The first snip or the first brushstroke, close.'],
  ['o','Your door from the sidewalk.'],
  ['s','Your tools laid out, then your hand picking one up.'],
  ['ch','Mid-service, over your shoulder (ask the client first).'],
  ['s','The product shelf, one slow pan.'],
  ['ch','You, a quick look up from the work.'],
  ['ch','The client seeing the mirror (only if they\'re happy to be seen).'],
  ['ch','The finished result, turned slowly.'],
  ['d','Your name on the wall or the door.'],
  ['d','You, one line: who it\'s for and how to book.']]},
 trades:{label:'Trades or repair', thing:'the fix', spots:{j:'The job',t:'The truck',b:'The bench',o:'Out front'}, clips:[
  ['j','The before: the broken thing, up close.'],
  ['t','Pulling up, or the van doors opening.'],
  ['j','Your hands on the tool, starting the work.'],
  ['j','The middle of the fix, the messy part.'],
  ['b','The part or tool that made the difference, held up.'],
  ['j','You, mid-job, a quick nod.'],
  ['o','The customer at the door or the finished space (ask first, and keep house numbers out of frame).'],
  ['j','The after, from the exact spot you shot the before.'],
  ['t','Your name on the truck or your shirt.'],
  ['t','You, one line: what you fix and how to reach you.']]},
 gym:{label:'Gym or class', thing:'the class', spots:{f:'The floor',w:'The whiteboard wall',d:'The front desk',o:'Outside'}, clips:[
  ['f','One rep, close: the bar leaving the floor, or feet landing.'],
  ['o','The door at class time, people walking in.'],
  ['f','Chalk, tape or gloves going on.'],
  ['f','The class moving together, from a corner.'],
  ['w','The whiteboard with today\'s workout.'],
  ['f','The coach, mid-cue.'],
  ['f','A member finishing something hard (ask first).'],
  ['f','High fives at the end of class.'],
  ['d','Your name or logo on the wall.'],
  ['d','You, one line: who it\'s for and when the next class is.']]},
 nonprofit:{label:'Nonprofit program', thing:'the program', spots:{p:'The program room',x:'The kitchen, garden or floor',d:'The front door',o:'Outside'}, clips:[
  ['x','The moment something happens: a seed going in, a pot stirred, a box sealed. Faces only if they\'re cleared to be shared.'],
  ['o','Your building or sign from the street.'],
  ['x','Volunteer or participant hands at work, faces out of frame.'],
  ['p','The activity in motion, from the side of the room.'],
  ['x','The materials: the food, the supplies, the boxes.'],
  ['p','Staff or volunteers, a quick wave.'],
  ['p','The people you serve, only if they\'re cleared to be in a video.'],
  ['x','The result: the meal, the garden, the packed boxes.'],
  ['d','Your banner or logo.'],
  ['d','You or your director, one line: what a gift does this week.']]}
};
var ROLES=['hook','place','hands','process','detail','people','customer','reveal','sign','call'];
var ROLE_NAME={hook:'Opening',place:'Your place',hands:'Hands',process:'How it\'s made',detail:'Close-up',people:'You',customer:'A customer',reveal:'The best part',sign:'Your sign',call:'The ask'};
var GOALS={
 door:{label:'Bring people in', w:{hook:1.1,place:1,hands:.8,process:.8,detail:1,people:1,customer:1.2,reveal:1.2,sign:.8,call:1.3}},
 how:{label:'Show how it\'s made', w:{hook:1,place:.6,hands:1.4,process:1.6,detail:1.2,people:.8,customer:.7,reveal:1.3,sign:.5,call:.9}},
 people:{label:'Introduce the people', w:{hook:1,place:.7,hands:.9,process:.8,detail:.6,people:1.7,customer:1.3,reveal:1,sign:.6,call:1.1}},
 give:{label:'Ask for support', w:{hook:1.1,place:.7,hands:1,process:1,detail:.8,people:1.1,customer:1.3,reveal:1.3,sign:.7,call:1.4}}
};
var LENS=[15,30,45];
var LIGHT={
 am:{label:'Morning',tip:'Film near a window and face the light. Morning light is soft, so the outside clips look best now too.'},
 mid:{label:'Midday',tip:'Hard sun makes harsh shadows. Shoot the outside clips in shade and the inside ones away from skylights.'},
 pm:{label:'Evening',tip:'Turn on every light you have. Keep windows behind the camera, never behind the person.'}
};
var st={type:'shop',goal:'door',len:30,light:'am'};

function thanksgiving(y){var d=new Date(y,10,1);var first=(4-d.getDay()+7)%7;return new Date(y,10,1+first+21)}
function addDays(d,n){var x=new Date(d);x.setDate(x.getDate()+n);return x}
var SOON=42;   // days out when the countdown starts to show (T-16)
function daysUntil(d){var t=new Date();t.setHours(0,0,0,0);return Math.round((d-t)/864e5)}
function fmt(d){return d.toLocaleDateString('en-US',{month:'short',day:'numeric'})}

function captions(role){
  var T=TYPES[st.type], g=st.goal, thing=T.thing;
  var M={
   door:{hook:'This is why it\'s worth the trip',reveal:'This is '+thing+'.',call:'Come see us this Saturday'},
   how:{hook:'How '+thing+' really gets made',process:'No shortcuts here',reveal:'Start to finish',call:'Come try it fresh'},
   people:{hook:'Meet the people behind '+thing,people:'This is who you\'ll see',reveal:'Made by people who care',call:'Come say hi'},
   give:{hook:'Here\'s what your support did this week',customer:'This is who it\'s for',reveal:'This is what a gift becomes',call:'Give on Giving Tuesday, Dec 1'}
  };
  return (M[g]||{})[role]||'';
}
function chips(id,opts,key){
  var el=document.getElementById(id);
  el.innerHTML=opts.map(function(o){return '<button type="button" class="chip" data-k="'+key+'" data-v="'+o[0]+'" aria-pressed="'+(String(st[key])===String(o[0]))+'">'+o[1]+'</button>'}).join('');
}
function plan(){
  var T=TYPES[st.type], w=GOALS[st.goal].w, sum=0;
  ROLES.forEach(function(r){sum+=w[r]});
  var clips=T.clips.map(function(c,i){
    var r=ROLES[i];
    var s=Math.max(1,Math.round(st.len*w[r]/sum*2)/2);
    return {no:i+1,role:r,spot:c[0],text:c[1],sec:s,cap:captions(r)};
  });
  var tot=clips.reduce(function(a,c){return a+c.sec},0), diff=st.len-tot, i=0;
  var order=clips.slice().sort(function(a,b){return w[b.role]-w[a.role]});
  while(Math.abs(diff)>=.5&&i<40){var c=order[i%order.length];if(diff>0){c.sec+=.5;diff-=.5}else if(c.sec>1){c.sec-=.5;diff+=.5}i++}
  return clips;
}
function render(){
  chips('c-type',Object.keys(TYPES).map(function(k){return [k,TYPES[k].label]}),'type');
  chips('c-goal',Object.keys(GOALS).map(function(k){return [k,GOALS[k].label]}),'goal');
  chips('c-len',LENS.map(function(n){return [n,n+' seconds']}),'len');
  chips('c-light',Object.keys(LIGHT).map(function(k){return [k,LIGHT[k].label]}),'light');
  var T=TYPES[st.type], clips=plan(), y=new Date().getFullYear();
  var tg=thanksgiving(y); if(daysUntil(addDays(tg,5))<0) tg=thanksgiving(y+1);
  var sbs=addDays(tg,2), gt=addDays(tg,5);
  var np=st.type==='nonprofit'||st.goal==='give';
  var target=np?gt:sbs, name=np?'Giving Tuesday':'Small Business Saturday';
  var d=daysUntil(target);
  // The countdown shows only from 42 days out to the day itself (T-16); farther out, nothing.
  document.getElementById('when').hidden=!(d>=0&&d<=SOON);
  document.getElementById('days').textContent=d===0?'Today':d+(d===1?' day':' days');
  document.getElementById('dayslabel').textContent=d===0?(name+' is today. Post it this morning.'):('until '+name+', '+fmt(target)+'. Film this week, post the week before.');
  document.getElementById('strip').innerHTML=clips.map(function(c){return '<span class="r-'+c.role+'" style="flex:'+c.sec+'">'+c.no+'</span>'}).join('');
  document.getElementById('striplabel').textContent=st.len+' seconds, 10 clips. Hook first, the ask last.';
  document.getElementById('edit').innerHTML=clips.map(function(c){
    return '<div class="clip"><span class="no">'+c.no+'</span><span class="role r-'+c.role+'">'+ROLE_NAME[c.role]+'</span><span class="sec">'+c.sec+' s</span><p>'+c.text+'</p>'+
      (c.cap?'<p class="cap">On-screen text: <b>'+c.cap+'</b></p>':'')+'</div>';
  }).join('');
  var groups={};clips.forEach(function(c){(groups[c.spot]=groups[c.spot]||[]).push(c)});
  var spotOrder=Object.keys(T.spots).filter(function(s){return groups[s]});
  document.getElementById('shoot').innerHTML=spotOrder.map(function(s,i){
    return '<div class="spot"><h3>Stop '+(i+1)+': '+T.spots[s]+'</h3><ol>'+groups[s].map(function(c){return '<li><b>#'+c.no+'</b><span>'+c.text+'</span></li>'}).join('')+'</ol></div>';
  }).join('');
  var rules=['Hold the phone upright, the way people watch.','Count to five on every clip, then stop. Short clips are easy to trim and impossible to stretch.','Don\'t zoom. Walk closer.','Wipe the lens on your shirt first. It\'s the cheapest upgrade there is.',LIGHT[st.light].tip];
  document.getElementById('rules').innerHTML=rules.map(function(r){return '<li>'+r+'</li>'}).join('');
  var off=document.getElementById('offer'), today=new Date(), cut=new Date(2026,10,20,23,59);
  if(today<=cut){
    off.innerHTML='<div class="offer noprint"><h2>Want it edited for free?</h2><p>This month I\'m editing three reels for Santa Rosa shops and three for nonprofits, free. Film these 10 clips, send them by November 20, and you get a finished, captioned reel back by November 25. You approve it before anyone sees it.</p><div style="display:flex;flex-wrap:wrap;gap:10px"><a class="btn" href="mailto:hello@dragomansjourney.com?subject='+encodeURIComponent('Free reel: '+T.label)+'&body='+encodeURIComponent('Hi Josef, I\'d like one of the free reels. I run: \n\nI\'ll send the clips by Nov 20.\n')+'">Claim a free reel</a><a class="btn" href="call.html" style="background:transparent;color:#0E1B17;border-color:#0E1B17">Ask on a 15-minute call</a></div></div>';
  }else off.innerHTML='';
  window._dj=clips;
}
document.addEventListener('click',function(e){
  var b=e.target.closest('.chip[data-k]');
  if(b){var k=b.dataset.k,v=b.dataset.v;st[k]=k==='len'?+v:v;if(k==='type'&&v==='nonprofit')st.goal='give';render();return}
});
document.getElementById('copy').addEventListener('click',function(){
  var T=TYPES[st.type];
  var txt='Reel shot list: '+T.label+', '+st.len+' seconds ('+GOALS[st.goal].label.toLowerCase()+')\n\nTHE EDIT\n'+window._dj.map(function(c){return c.no+'. '+ROLE_NAME[c.role]+' ('+c.sec+' s): '+c.text+(c.cap?'  On-screen: "'+c.cap+'"':'')}).join('\n');
  var g={};window._dj.forEach(function(c){(g[c.spot]=g[c.spot]||[]).push('#'+c.no)});
  txt+='\n\nTHE SHOOT (one lap)\n'+Object.keys(T.spots).filter(function(s){return g[s]}).map(function(s){return T.spots[s]+': '+g[s].join(', ')}).join('\n');
  txt+='\n\nFrom dragomansjourney.com/shotlist.html';
  djCopy(txt,'Shot list');
});
document.getElementById('print').addEventListener('click',function(){window.print()});
render();
})();
"""

write(sys.argv[1], "shotlist.html",
      title="Reel Shot List",
      description="A free planner for small businesses and nonprofits: pick what you run and get the 10 phone clips to film, in edit order and in one-lap shooting order.",
      kicker="Free tool",
      h1="What to film for your reel",
      lede="Tell me what you run. You get 10 clips to film, in the order you walk your shop.",
      css=CSS, body=BODY, script=SCRIPT, folds=True,
      cta_h="Rather hand it off?", cta_p="Send me the clips and I'll cut the reel. Or start with a free 15-minute call.",
      cta_href="call.html", cta_btn="Free 15-minute call")
