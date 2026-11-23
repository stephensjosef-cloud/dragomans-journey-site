#!/usr/bin/env python3
"""T-42's checks for the build log's filter and the voice checker's list rule (Nov 22, 2026).

    python3 tools/test_board.py          (from _build/; needs git and node)

1. tools/board_guard.py on the cases T-42 names: each of the 16 approved catch-up lines
   PASS (on its own date, against shipped.json as it was before T-42 added them), and
   every bad case FAIL. The deny file is written to a temp folder outside the repository;
   its one word is made up.
2. The voice checker's list rule, on its script in _build/voicecheck.html: two plain lists
   not marked, three clauses and three adjectives marked; the sample text marks as it did
   before T-42 except where the list rule changes it; and the headline words W1 to W3.
Prints one line per case and exits 1 if any differs from what T-42 states.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

TOOLS = pathlib.Path(__file__).resolve().parent
HERE = TOOLS.parent
BASE = "273fa0d76862a4685194b9d91e5446b6266eec42"      # origin/main when T-42 was cut
bad = []


def line(ok, text):
    print(("ok    " if ok else "WRONG ") + text)
    if not ok:
        bad.append(text)


def guard(tmp, date, project, text, today, shipped=None):
    args = [sys.executable, str(TOOLS / "board_guard.py"), "--deny", str(tmp / "deny.txt"),
            "--date", date, "--project", project, "--line", text, "--today", today]
    if shipped:
        args += ["--shipped", str(shipped)]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout.strip().replace("\n", " ")


def guard_cases():
    with tempfile.TemporaryDirectory() as t:
        tmp = pathlib.Path(t)
        (tmp / "deny.txt").write_text("Marguerite\n", encoding="utf-8")       # a made-up name
        before = tmp / "shipped-before.json"
        before.write_bytes(subprocess.run(["git", "show", f"{BASE}:_build/shipped.json"], cwd=HERE,
                                          capture_output=True, check=True).stdout)
        now = json.loads((HERE / "shipped.json").read_text(encoding="utf-8"))["entries"]
        old = {(e["date"], e["project"], e["line"]) for e in json.loads(before.read_text(encoding="utf-8"))["entries"]}
        approved = [e for e in now if (e["date"], e["project"], e["line"]) not in old]
        line(len(approved) == 16, f"guard: 16 approved lines found in shipped.json ({len(approved)})")
        for e in reversed(approved):
            code, out = guard(tmp, e["date"], e["project"], e["line"], e["date"], before)
            line(code == 0 and out == "PASS", f'guard PASS expected: {e["date"]} {e["project"]}: {e["line"]}  ->  {out}')
        today = "2026-11-22"
        cases = [
            ("2026-11-22", "birdleague", "Shipped OTA 9b412add to testers."),
            ("2026-11-22", "birdleague", "Bird League build 53 is out."),
            ("2026-11-22", "kids", "Marguerite loved the new fridge finder."),
            ("2026-11-22", "tools", "The checkup now costs $5."),
            ("2026-11-22", "birdleague", "See birdleague.app for more."),
            ("2026-11-22", "tools", "Game-changing new features shipped."),
            ("2026-11-22", "kids", "Every recipe now shows what matters most."),
            ("2026-11-21", "deepcuts", "Deepcuts players can now save a game to play later."),   # 2026-11-21 has three
            ("2026-11-23", "deepcuts", "Deepcuts players can now save a game to play later."),   # tomorrow
        ]
        for date, project, text in cases:
            code, out = guard(tmp, date, project, text, today)
            line(code == 1 and out.startswith("FAIL"), f"guard FAIL expected: {date} {project}: {text}  ->  {out}")
        code, out = guard(tmp, "2026-11-22", "deepcuts", "Deepcuts players can now save a game to play later.", today)
        line(code == 0, f"guard PASS expected (the same line on today's date, control): {out}")
        r = subprocess.run([sys.executable, str(TOOLS / "board_guard.py"), "--deny", str(HERE / "shipped.json"), "--date", today,
                            "--project", "kids", "--line", "The cooking app now prints a week of lunches.", "--today", today],
                           capture_output=True, text=True, encoding="utf-8")
        line(r.returncode == 1 and "inside this repository" in r.stdout, "guard FAIL expected: a --deny file inside the repository")


HARNESS = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const src = scripts.find(s => s.includes('window.voiceCheck'));
const els = {};
const el = id => els[id] || (els[id] = {id, hidden: true, textContent: '', innerHTML: '', value: '', handlers: {},
  addEventListener(e, f) { this.handlers[e] = f; }, focus() {}, scrollIntoView() {}});
global.window = global;
global.document = {getElementById: el, querySelectorAll: () => [], addEventListener() {}};
global.djNw = s => s;
eval(src);
const out = {};
const cases = JSON.parse(process.argv[3]);
for (const [k, text] of Object.entries(cases)) {
  const R = window.voiceCheck(text);
  el('words').value = text;
  el('check').handlers.click();
  out[k] = {marks: R.sentences.map(S => S.marks.map(m => m.rule + ':' + (m.hit || ''))), rhythm: R.rhythm,
            head: el('res-h').textContent, cards: (el('cards').innerHTML.match(/class="vcard"/g) || []).length,
            vend: el('vend').hidden, sample: undefined};
}
const sm = scripts.join('\n').match(/var SAMPLE = ("(?:[^"\\]|\\.)*");/);
out.__sample = sm ? JSON.parse(sm[1]) : null;
console.log(JSON.stringify(out));
"""


def voice(page, cases):
    with tempfile.TemporaryDirectory() as t:
        h = pathlib.Path(t) / "h.js"
        h.write_text(HARNESS, encoding="utf-8")
        r = subprocess.run(["node", str(h), str(page), json.dumps(cases)], capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            raise SystemExit(r.stderr)
        return json.loads(r.stdout)


def list_rule():
    page = HERE / "voicecheck.html"
    plain = {"bread": "Bread, coffee and the odd pie.",
             "apps": "Plus two apps, a birding game and a public COBOL check.",
             "clauses": "We listen, we build, we deliver.",
             "adjectives": "We offer fast, friendly and reliable service.",
             "adjectives2": "fast, friendly and reliable service"}
    R = voice(page, plain)
    f = lambda k: [m for s in R[k]["marks"] for m in s if m.startswith("f:")]
    line(not f("bread"), f'list rule: "{plain["bread"]}" not marked  ->  {f("bread")}')
    line(not f("apps"), f'list rule: "two apps, a birding game and a public COBOL check" not marked  ->  {f("apps")}')
    line(bool(f("clauses")), f'list rule: "{plain["clauses"]}" marked  ->  {f("clauses")}')
    line(bool(f("adjectives2")), f'list rule: "{plain["adjectives2"]}" marked  ->  {f("adjectives2")}')
    line(bool(f("adjectives")), f'list rule: "{plain["adjectives"]}" marked  ->  {f("adjectives")}')
    # The approved sample, old checker (origin/main when T-42 was cut) against new.
    with tempfile.TemporaryDirectory() as t:
        oldp = pathlib.Path(t) / "voicecheck.html"
        oldp.write_bytes(subprocess.run(["git", "show", f"{BASE}:_build/voicecheck.html"], cwd=HERE, capture_output=True, check=True).stdout)
        sample = R["__sample"]
        old = voice(oldp, {"s": sample})["s"]["marks"]
    new = voice(page, {"s": sample})["s"]["marks"]
    same = [o for o in old] == [n for n in new]
    nof = lambda ms: [[m for m in s if not m.startswith("f:")] for s in ms]
    line(nof(old) == nof(new), f"list rule: the sample's marks other than three-in-a-row are the same as before ({sum(map(len, nof(new)))} marks)")
    print(f"      sample three-in-a-row marks before: {[m for s in old for m in s if m.startswith('f:')]}, after: {[m for s in new for m in s if m.startswith('f:')]}"
          f"{' (identical)' if same else ''}")
    # W1 to W3, the headline.
    w = voice(page, {
        "one": "Our team leverages cutting-edge tools to elevate your brand.",
        "two": "We leverage tools. We bake bread at six. Our seamless service is robust.",
        "none": "We bake 60 loaves before 6 every morning, and the rye sells out by noon.",
        "flat": " ".join(["We bake fresh bread here every single morning at six."] * 9),
        "es": "Hacemos pan cada mañana y el centeno se agota al mediodía. Abrimos de martes a domingo, y los sábados hay pan dulce para todos.",
    })
    line(w["one"]["head"] == "1 of 1 sentence has a mark", f'W1: one sentence  ->  "{w["one"]["head"]}"')
    line(w["two"]["head"] == "2 of 3 sentences have marks", f'W1: more  ->  "{w["two"]["head"]}"')
    line(w["none"]["head"].startswith("Nothing jumped out."), f'W3 not shown without the rhythm note  ->  "{w["none"]["head"]}"')
    line(w["flat"]["head"] == "No sentence has a mark, but the rhythm reads flat." and w["flat"]["rhythm"],
         f'W3: no mark, flat rhythm  ->  "{w["flat"]["head"]}"')
    line(w["es"]["head"] == "This reads English only, so I can't check these words." and w["es"]["cards"] == 0 and w["es"]["vend"],
         f'W2: Spanish  ->  "{w["es"]["head"]}", {w["es"]["cards"]} cards, end line hidden {w["es"]["vend"]}')


if __name__ == "__main__":
    os.chdir(HERE)
    guard_cases()
    list_rule()
    print(f"{'ALL AS STATED' if not bad else str(len(bad)) + ' DIFFER'}")
    sys.exit(1 if bad else 0)
