"""Voice checker (T-35, Nov 21, 2026): a visitor pastes words written with AI; the page marks the
sentences that read as machine-made, says why in plain words, and says what to put there instead.
The checks come from Josef's voice harness (tells.py's rules, the read-back runs, version 2's swap
test), ported to JavaScript. Everything runs in the browser: no fetch, no Worker, no storage, and the
text never goes into the address. No AI call.
Not voice.py: _build/voice.py is a different thing (a build pass)."""
from chrome import write
import sys

CSS = r"""
.vbox textarea{min-height:220px;font-size:17px}
.vacts{display:flex;flex-wrap:wrap;gap:12px;margin-top:14px}
.vmsg{margin:12px 0 0;font-weight:600}
.vmsg:empty{display:none}
.vns{margin:0;font-weight:600}
#res{display:flex;flex-direction:column;gap:16px}
#res-h{margin:0;font-size:24px;line-height:1.3;outline:none}
.vnote{margin:0;border-left:4px solid #D9A520;background:#F9EEDA;padding:12px 14px;font-size:16px}
.vcards{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:14px}
.vcard{background:#FBF8F1;border:1.5px solid #CFC6B2;border-left:4px solid #C2461B;border-radius:2px;padding:14px 16px}
.vcard .s{margin:0;font-size:18px;line-height:1.55;overflow-wrap:anywhere}
.vcard mark{background:#F8E3DA;color:#16201C;font-weight:700;padding:0 2px;border-radius:2px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.vmarks{list-style:none;margin:12px 0 0;padding:0;display:flex;flex-direction:column;gap:10px}
.vmarks li{border-top:1px solid #CFC6B2;padding-top:10px}
.vmarks p{margin:0;font-size:16px;line-height:1.5}
.vmarks .try{margin-top:2px;color:#3B4540;font-weight:600}
.vend{margin:8px 0 0;font-size:17px}
.fixit{display:inline-flex;align-items:center;min-height:48px;font-weight:700;color:#16201C;font-size:18px}
"""

BODY = r"""
  <div class="panel vbox">
    <label for="words" class="label">Your words</label>
    <textarea id="words" autocomplete="off"></textarea>
    <div class="vacts">
      <button type="button" class="btn hot" id="check">Check it</button>
      <button type="button" class="btn ghost" id="sample">Try a sample</button>
    </div>
    <p class="vmsg" id="msg" role="status" aria-live="polite"></p>
  </div>
  <noscript><p class="vns">The checker runs in your browser, so it needs JavaScript turned on.</p></noscript>

  <section id="res" aria-labelledby="res-h" hidden>
    <h2 id="res-h" tabindex="-1"></h2>
    <p class="vnote" id="note" hidden>Most of your sentences are about the same length, which reads flat. Mix in a short one.</p>
    <ol class="vcards" id="cards"></ol>
    <p class="vend" id="vend">This finds the marks. It can't make it sound like you. That takes your own words, and getting them out of you is the part I do.</p>
    <a class="fixit" id="fixit" href="call.html">Want me to fix it?</a>
  </section>
"""

SCRIPT = r"""
(function () {
  // The rules, in the order they are checked. tells.py's regexes, ported (long dashes written as \u escapes); T-41's
  // play pass narrowed a and b and widened f's last item, each noted where it changed.
  var L1 = [
    // T-41 play pass: a typed " -- " is not marked (people type it; AI tools write the long dash), and "not X, but" is
    // marked only as "not just/only/about X, but", so a plain "I'm not a morning person, but ..." isn't.
    ['a', /\u2014|\u2013(?=\s)/g,
      'Long dashes are the mark people spot first now.', 'Use a period or a comma.'],
    ['b', /\b(?:isn't|is not|aren't|not) (?:(?:just |only |about )?[^.?!]{3,60}?(?:[,;.] ?(?:it's|it is|they're)\b|\u2014)|(?:just |only |about )[^.?!]{3,60}?[,;] ?but\b)/gi,
      '"It\'s not this, it\'s that" is the most copied shape in AI writing.', 'Say the second half on its own.'],
    ['c', /\b(?:leverag\w*|seamless\w*|unlock\w*|elevat\w*|robust|streamlin\w*|effortless\w*|game.chang\w*|delve\w*|tapestry|cutting.edge|empower\w*|harness the|supercharg\w*|revolutioni\w*|transformative|next.level|world.class|bespoke|curated|holistic|synerg\w*|journey to|in today's|landscape of|at the end of the day|when it comes to|it's worth noting|rest assured)\b/gi,
      '"{hit}" is one of the words AI reaches for.', 'Say what actually happens.'],
    ['d', /^(?:Whether you're|Whether you are|Imagine |Picture this|In a world|Let's face it|Here's the thing|The truth is|Simply put|Look,)/gi,
      '"{hit}" warms up instead of starting.', 'Start with the point.'],
    ['e', /\b(?:The (?:result|answer|secret|catch|best part|bottom line)|Here's (?:why|how|what))\s*[:?]/gi,
      '"{hit}" sets up a reveal.', 'Just say it.']
  ];
  var L2 = ['guess', /\b(?:something|things|stuff|content|solutions|your needs|unique needs|everything you need|(?:what|the (?:\w+ )?(?:that|which))(?: (?:really|actually|truly))? matters?(?: most)?|quality|value)\b/gi,
    '"{hit}" makes the reader guess.', 'Name the real thing: which one, how many, or what it was last time.'];
  var L3 = ['swap', 'Any business could paste this on their own site without changing a word.', 'Add one thing only you have: a number, a name or a place.'];
  var L4 = {
    // T-42: three items with "and" or "or" before the last, or three with commas only. Each find is marked only when
    // it's a rhythm (triad() below): three clauses, or three adjectives. A plain list of things isn't.
    f: [/\b([\w'\u2019-]+(?: [\w'\u2019-]+){0,3}), ([\w'\u2019-]+(?: [\w'\u2019-]+){0,3})(?:,? (?:and|or) ([\w'\u2019-]+(?: [\w'\u2019-]+){0,2})|, ([\w'\u2019-]+(?: [\w'\u2019-]+){0,2}))/g,
      'Three in a row is a rhythm AI loves.', 'Keep the one you\'d miss.'],
    g: ['Asking a question and answering it yourself is a stage move.', 'On a page, just answer.'],
    h: ['Three short sentences in a row reads like a slogan.', 'Join two of them.']
  };
  var MAX_WORDS = 3000;
  var SAMPLE = "Whether you're a small business or a growing nonprofit, we deliver seamless solutions tailored to your unique needs. It's not just about marketing, it's about building real connections. Our team leverages cutting-edge tools to elevate your brand. Here's the secret: consistency. We handle everything so you can focus on what matters most. We bake 60 loaves before 6 every morning, and the rye sells out by noon. Ready to take your business to the next level?";

  function words(s) { var w = String(s).trim().split(/\s+/); return w[0] ? w : []; }

  // Sentences end at . ! ? followed by a space or the end (the punctuation stays), and at a line break.
  function split(text) {
    var out = [];
    String(text).split(/\r\n|\r|\n/).forEach(function (line) {
      var start = 0;
      for (var i = 0; i < line.length; i++) {
        if ('.!?'.indexOf(line[i]) > -1 && (i + 1 === line.length || /\s/.test(line[i + 1]))) {
          out.push(line.slice(start, i + 1)); start = i + 1;
        }
      }
      out.push(line.slice(start));
    });
    return out.map(function (s) { return s.trim(); }).filter(Boolean);
  }

  // T-42 (Nov 22, 2026), the list rule: "Bread, coffee and the odd pie." is a list of things and isn't marked;
  // "We listen, we build, we deliver." (three clauses) and "fast, friendly and reliable service" (three adjectives) are.
  // Clauses: the second and third items start with a person (we, you, I, they...) and the first holds one too, or all
  // three start with the same word. Adjectives: the second item is one word, and at least two of the first item's
  // last word, the second item and the third item's first word read as adjectives (ADJ, or an adjective's ending).
  var WHO = /^(?:we|you|i|they|he|she|it|we'll|we're|you'll|you're|i'll|i'm|they'll|they're)$/i;
  var ADJ = /^(?:fast|quick|friendly|reliable|simple|easy|affordable|modern|clean|smart|fresh|honest|warm|bold|safe|secure|professional|personal|creative|innovative|efficient|effective|flexible|trusted|proven|powerful|beautiful|stunning|unique|custom|premium|expert|dedicated|passionate|experienced|skilled|caring|welcoming|cozy|delicious|authentic|sustainable|transparent|responsive|scalable|intuitive|elegant|timeless|vibrant|dynamic|seamless|robust|smooth|clear|calm|kind|fun|bright|better|faster|smarter|stronger|cheaper|best|great|good|new|local|real|hassle-free|stress-free|on-time)$/i;
  var NOT_LY = /^(?:family|supply|assembly|jelly|belly|rally|ally|fly|july|reply|lily|holly|bully|italy|apply|comply|multiply|only)$/i;
  function adj(w) {
    w = String(w || '').toLowerCase();
    return ADJ.test(w) || /(?:ful|ous|ive|able|ible|less)$/.test(w) || (/ly$/.test(w) && w.length > 4 && !NOT_LY.test(w));
  }
  function triad(m) {
    var A = m[1].split(' '), B = m[2].split(' '), C = (m[3] || m[4]).split(' ');
    var lo = function (w) { return w.toLowerCase(); };
    if (WHO.test(B[0]) && WHO.test(C[0]) && A.some(function (w) { return WHO.test(w); })) return true;
    if (A.length > 1 && B.length > 1 && C.length > 1 && lo(A[0]) === lo(B[0]) && lo(B[0]) === lo(C[0])) return true;
    return B.length === 1 && [A[A.length - 1], B[0], C[0]].filter(adj).length >= 2;
  }

  function finds(re, s) {
    var hits = [], m;
    re.lastIndex = 0;
    while ((m = re.exec(s))) {
      hits.push({hit: m[0], at: m.index});
      if (!m[0]) re.lastIndex++;
      if (!re.global) break;
    }
    return hits;
  }

  // Level 3, the swap test: only a sentence that makes a claim about the business.
  var CLAIM = /\b(?:we|our|us|your business|your brand)\b/i;
  var OK_CAPS = ['I', "I'm", "I'll", "I've", "I'd", 'I\u2019m', 'I\u2019ll', 'I\u2019ve', 'I\u2019d'];
  // T-41 play pass: a sentence holding a web or email address is the business's own, so it never fails the swap test.
  var ADDR = /https?:\/\/|\bwww\.|\b[\w-]+\.(?:com|org|net|edu|gov|io|co|us|biz|info|shop|app|dev|studio)\b|[\w.+-]+@[\w-]+\./i;
  function swap(s) {
    var w = words(s);
    if (w.length < 8 || !CLAIM.test(s) || /[0-9$%]/.test(s) || ADDR.test(s)) return false;
    return !w.slice(1).some(function (x) {
      var core = x.replace(/^[^\p{L}\p{N}]+/u, '').replace(/[^\p{L}\p{N}'\u2019]+$/u, '');
      return /^\p{Lu}/u.test(core) && OK_CAPS.indexOf(core) < 0;
    });
  }

  // T-41 play pass: the rules read a copy with curly quotes made straight (phones and word processors type them) and a
  // list line's bullet or number blanked out; the copy keeps every position, so the marks land on the words as typed.
  var LIST = /^(?:[-*\u2022\u2023\u25E6\u2013\u2014]|\d{1,2}[.)])\s+/;
  function plainCopy(s) {
    var c = s.replace(/[\u2018\u2019]/g, "'").replace(/[\u201C\u201D]/g, '"');
    var m = LIST.exec(c);
    return m ? new Array(m[0].length + 1).join(' ') + c.slice(m[0].length) : c;
  }

  function check(text) {
    var sents = split(text).map(function (s) {
      var list = LIST.test(s);
      return {text: s, words: words(list ? s.replace(LIST, '') : s).length, marks: [], list: list};
    });
    sents.forEach(function (S) {
      var s = plainCopy(S.text);
      var at = function (h) { return S.text.substr(h.at, h.hit.length); };
      L1.forEach(function (r) {
        finds(r[1], s).forEach(function (h) { S.marks.push({level: 1, rule: r[0], hit: at(h), at: h.at}); });
      });
      finds(L2[1], s).forEach(function (h) { S.marks.push({level: 2, rule: L2[0], hit: at(h), at: h.at}); });
      // T-41 play pass: the swap test speaks only where the sentence already reaches for generic words (a level 1 or 2
      // mark); on its own it marked plain, specific talk like "We do cakes but we need a week."
      if (S.marks.length && swap(s)) S.marks.push({level: 3, rule: L3[0], hit: null, at: null});
      var fm, fre = L4.f[0];
      fre.lastIndex = 0;
      while ((fm = fre.exec(s))) { if (triad(fm)) S.marks.push({level: 4, rule: 'f', hit: at({hit: fm[0], at: fm.index}), at: fm.index}); }
    });
    // g: a question answered by the very next sentence, short, starting with It, That, This, You, We, I or The.
    sents.forEach(function (S, i) {
      var nx = sents[i + 1];
      if (/\?$/.test(S.text) && nx && nx.text.length <= 80 && /^(?:It|That|This|You|We|I|The)\b/.test(nx.text))
        S.marks.push({level: 4, rule: 'g', hit: null, at: null});
    });
    // h: three sentences in a row of 2 to 6 words each; the first of the three is marked, and the next run starts after them.
    // T-41 play pass: list lines are not sentences here, and the card shows all three sentences it means.
    var short = function (S) { return S && !S.list && S.words >= 2 && S.words <= 6; };
    for (var i = 0; i + 2 < sents.length; i++) {
      if (short(sents[i]) && short(sents[i + 1]) && short(sents[i + 2])) {
        sents[i].marks.push({level: 4, rule: 'h', hit: null, at: null});
        sents[i].run = [sents[i + 1].text, sents[i + 2].text];
        i += 2;
      }
    }
    sents.forEach(function (S) {   // worst first; the same level keeps the order the rules run in
      S.marks = S.marks.map(function (m, k) { m.k = k; return m; }).sort(function (a, b) { return a.level - b.level || a.k - b.k; });
      S.marks.forEach(function (m) { delete m.k; });
    });
    // The whole text: 8 or more sentences of 3 words or more, all about the same length (tells.py's rhythm rule).
    var n = sents.filter(function (S) { return S.words >= 3 && !S.list; }).map(function (S) { return S.words; }), flat = false;   // T-41: list lines don't count
    if (n.length >= 8) {
      var mean = n.reduce(function (a, b) { return a + b; }, 0) / n.length;
      var sd = Math.sqrt(n.reduce(function (a, b) { return a + (b - mean) * (b - mean); }, 0) / n.length);
      flat = sd / mean < 0.45;
    }
    return {sentences: sents, rhythm: flat, words: words(text).length};
  }
  window.voiceCheck = check;

  // T-42 W2: the rules only know English. Text of 12 words or more where under 1 word in 12 is a common English
  // word (or written mostly outside the Latin alphabet) gets one line and no marks.
  var EN = /^(?:the|and|to|of|in|is|you|we|it|for|on|with|our|your|that|this|are|be|my|at|as|can|will|have|from|or|by|an|not|but|all|so|if|they|was|what|when|who|how|do|get|just|more|about|us|me|their|there|here|one|out|up|any|every)$/;
  function english(text) {
    var w = words(text.toLowerCase().replace(/[\u2018\u2019]/g, "'")).map(function (x) { return x.replace(/^[^\p{L}]+|[^\p{L}']+$/gu, ''); }).filter(Boolean);
    if (w.length < 12) return true;
    var letters = (text.match(/\p{L}/gu) || []).length, latin = (text.match(/[A-Za-z\u00C0-\u024F]/g) || []).length;
    if (letters && latin / letters < 0.5) return false;
    return w.filter(function (x) { return EN.test(x); }).length / w.length >= 1 / 12;
  }
  window.voiceEnglish = english;

  // ---- The page.
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); };
  var txt = function (s) { return djNw(esc(s)); };
  function reason(m) {
    var r = m.level === 1 ? L1.filter(function (x) { return x[0] === m.rule; })[0].slice(2)
      : m.level === 2 ? L2.slice(2) : m.level === 3 ? L3.slice(1) : (m.rule === 'f' ? L4.f.slice(1) : L4[m.rule]);
    return r.map(function (x) { return x.replace('{hit}', m.hit == null ? '' : m.hit); });
  }
  function marked(S) {   // the sentence, every matched stretch in a <mark> (joined where they touch)
    var spans = S.marks.filter(function (m) { return m.hit; }).map(function (m) { return [m.at, m.at + m.hit.length]; })
      .sort(function (a, b) { return a[0] - b[0]; }), merged = [];
    spans.forEach(function (p) { var l = merged[merged.length - 1]; if (l && p[0] <= l[1]) l[1] = Math.max(l[1], p[1]); else merged.push(p.slice()); });
    var out = '', at = 0;
    merged.forEach(function (p) { out += txt(S.text.slice(at, p[0])) + '<mark>' + txt(S.text.slice(p[0], p[1])) + '</mark>'; at = p[1]; });
    return out + txt(S.text.slice(at));
  }
  function say(t) { $('msg').textContent = t; }
  function run() {
    var text = $('words').value;
    $('res').hidden = true;
    if (!text.trim()) { say('Paste some words first.'); $('words').focus(); return; }
    var R = check(text);
    if (R.words > MAX_WORDS) { say("That's a lot at once. Paste one page at a time, about 3,000 words."); return; }
    say('');
    var en = english(text);
    $('vend').hidden = $('fixit').hidden = !en;
    if (!en) {
      $('res-h').textContent = "This reads English only, so I can't check these words.";
      $('note').hidden = true;
      $('cards').innerHTML = '';
      $('res').hidden = false;
      $('res-h').focus({preventScroll: true});
      $('res').scrollIntoView({block: 'start'});
      return;
    }
    var hit = R.sentences.map(function (S, i) { S.i = i; return S; }).filter(function (S) { return S.marks.length; });
    hit.sort(function (a, b) { return a.marks[0].level - b.marks[0].level || a.i - b.i; });
    var m = R.sentences.length, n = hit.length;
    // T-42 W1: the noun agrees with the count; W3: no mark but a flat rhythm says so.
    $('res-h').textContent = !n ? (R.rhythm ? 'No sentence has a mark, but the rhythm reads flat.'
        : "Nothing jumped out. Read it out loud once anyway. If you wouldn't say it, cut it.")
      : n === 1 ? '1 of ' + m + (m === 1 ? ' sentence has a mark' : ' sentences has a mark') : n + ' of ' + m + ' sentences have marks';
    $('note').hidden = !R.rhythm;
    $('cards').innerHTML = hit.map(function (S) {
      var said = {};   // T-41 play pass: the same advice once per sentence (two long dashes gave it twice)
      return '<li class="vcard"><p class="s">' + marked(S) + (S.run ? ' ' + S.run.map(txt).join(' ') : '') + '</p><ul class="vmarks">' + S.marks.map(function (k) {
        var r = reason(k), key = r[0] + '\n' + r[1];
        if (said[key]) return '';
        said[key] = 1;
        return '<li><p>' + txt(r[0]) + '</p><p class="try">' + txt(r[1]) + '</p></li>';
      }).join('') + '</ul></li>';
    }).join('');
    $('res').hidden = false;
    $('res-h').focus({preventScroll: true});
    $('res').scrollIntoView({block: 'start'});
  }
  $('check').addEventListener('click', run);
  $('sample').addEventListener('click', function () { $('words').value = SAMPLE; run(); });
})();
"""

write(sys.argv[1], "voicecheck.html",
      title="Voice checker",
      description="Paste words written with AI and see which sentences give it away, and what to put there instead.",
      h1="Does it sound like AI?",
      lede="Paste words you wrote with AI. I'll mark the sentences that give it away and tell you what to put there instead.",
      css=CSS, body=BODY, script=SCRIPT, more_line=True)
