#!/usr/bin/env python3
"""The build log's filter (T-42, Nov 22, 2026).

    python3 tools/board_guard.py --deny <path> --date YYYY-MM-DD --project <id> --line '<text>'

Run from _build/, before tools/board.py adds a line. A line the nightly build log job
writes goes live with no one reading it first, so this refuses anything that could
embarrass, leak something private, or say more than is true. Exit 0 and "PASS", or
exit 1 and every reason, one per line. Python 3's standard library only.

It refuses:
- a project with no label (a product in studio.json or a name in its "labels");
- a date that isn't YYYY-MM-DD, is in the future, or is more than 3 days old
  (today in America/Los_Angeles);
- a 4th line on one date;
- a line under 25 or over 120 characters, or not one sentence ending in a period;
- an em or en dash;
- anything the voice checker's HARD rules mark (its rules a to e, read from
  voicecheck.py), and its "what matters" phrasing;
- a web address (the site's own, dragomansjourney.com, is allowed), an email address,
  an @ handle, a phone number, a dollar amount or any price;
- a hex string of 7 or more characters, an OTA or a commit id, or a version or build
  number with no "can" after it (what a person can now do);
- any word or phrase in the --deny file (one per line, whole words, any case; blank
  lines and lines starting with # skipped). The file must be outside this repository,
  and nothing from it is ever printed;
- a line whose words repeat an existing line's at 80% or more (Dice overlap of the
  two lines' sets of words).

--today and --shipped are for tests: the day to count from, and the build log to
check against.
"""
import argparse
import datetime
import json
import pathlib
import re
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
HERE = TOOLS.parent
REPO = HERE.parent
sys.path.insert(0, str(TOOLS))
import studio                     # noqa: E402

MIN_LEN, MAX_LEN, PER_DAY, MAX_AGE, OVERLAP = 25, 120, 3, 3, 0.8


def js_rules():
    """The HARD rules (L1, a to e) and the guess rule (L2) from the voice checker's script, as Python regexes."""
    src = (TOOLS / "voicecheck.py").read_text(encoding="utf-8")
    hard = dict(re.findall(r"\['([a-e])', /(.+?)/gi?,\n", src))
    assert sorted(hard) == list("abcde"), "board_guard.py: can't read voicecheck.py's rules a to e"
    guess = re.findall(r"var L2 = \['guess', /(.+?)/gi,\n", src)
    assert len(guess) == 1, "board_guard.py: can't read voicecheck.py's guess rule"
    flags = re.I | re.M
    return {k: re.compile(v, flags) for k, v in hard.items()}, re.compile(guess[0], flags)


WHY = {"a": "a long dash", "b": 'the "not this, it\'s that" shape', "c": "a word AI reaches for",
       "d": "a warm-up opening", "e": "a reveal set-up"}

URL = re.compile(r"https?://|\bwww\.|\b[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|edu|gov|io|co|us|biz|info|shop|app|dev|studio|ai|me|ly|gg|tv|xyz|site|online|store)\b", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
HANDLE = re.compile(r"(?<![\w.])@\w")
PHONE = re.compile(r"(?:\+?\d[\s().-]*){7,}")
MONEY = re.compile(r"[$€£¥]|\b\d+(?:[.,]\d+)?\s*(?:dollars?|usd|eur|euros?|cents?|bucks|pounds?)\b"
                   r"|\b(?:price[sd]?|pricing|costs?|costing|per month|a month|per year|a year|/mo|/yr|discount\w*|\d+% off)\b", re.I)
HEX = re.compile(r"\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,}\b", re.I)
OTA = re.compile(r"\b(?:OTA|commit|sha|hash|changeset)\b", re.I)
VERSION = re.compile(r"\b(?:build|version|release|beta|patch|update)\s*#?\s*\d+|\bv\d+(?:\.\d+)*\b|\b\d+\.\d+(?:\.\d+)+\b", re.I)
CAN = re.compile(r"\bcan\b", re.I)


def words(s):
    return set(re.findall(r"[a-z0-9']+", s.lower().replace("’", "'")))


def dice(a, b):
    a, b = words(a), words(b)
    return 2 * len(a & b) / (len(a) + len(b)) if a and b else 0.0


def deny_rx(path):
    p = pathlib.Path(path).resolve()
    try:
        p.relative_to(REPO)
        inside = True
    except ValueError:
        inside = False
    if inside:
        return None, "the --deny file is inside this repository; it must live outside it"
    if not p.is_file():
        return None, "the --deny file can't be read"
    items = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()]
    items = [i for i in items if i and not i.startswith("#")]
    if not items:
        return None, "the --deny file has no words in it"
    alts = "|".join(r"\s+".join(re.escape(w) for w in i.split()) for i in items)
    return re.compile(r"(?<!\w)(?:" + alts + r")(?!\w)", re.I), None


def check(date, project, line, deny, today=None, shipped=None):
    """Every reason the line can't go in; an empty list means PASS."""
    why = []
    st, log = studio.load()
    if shipped is not None:
        log = json.loads(pathlib.Path(shipped).read_text(encoding="utf-8"))
    today = today or studio.la_today()
    if project not in studio.labels(st):
        why.append(f'project "{project}" has no label (a product in studio.json, or its "labels")')
    day = None
    try:
        day = datetime.date.fromisoformat(date)
        if day.isoformat() != date:
            day = None
    except ValueError:
        pass
    if day is None:
        why.append("the date isn't YYYY-MM-DD")
    elif day > today:
        why.append(f"the date {date} is in the future (today is {today.isoformat()} in Los Angeles)")
    elif (today - day).days > MAX_AGE:
        why.append(f"the date {date} is more than {MAX_AGE} days old (today is {today.isoformat()} in Los Angeles)")
    if day is not None and sum(1 for e in log["entries"] if e["date"] == date) >= PER_DAY:
        why.append(f"{date} already has {PER_DAY} lines")
    if not MIN_LEN <= len(line) <= MAX_LEN:
        why.append(f"the line is {len(line)} characters; it must be {MIN_LEN} to {MAX_LEN}")
    if not line.endswith(".") or re.search(r"[.!?][\"')”’]*\s", line) or re.search(r"[!?]", line):
        why.append("the line must be one sentence ending in a period")
    if re.search("[–—]", line):
        why.append("an em or en dash")
    plain = line.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    hard, guess = js_rules()
    for k, rx in hard.items():
        if k != "a" and rx.search(plain):
            why.append(f"the voice checker's HARD rule {k}: {WHY[k]} ({rx.search(plain).group(0)!r})")
    for m in guess.finditer(plain):
        if "matter" in m.group(0).lower():
            why.append(f'"what matters" phrasing ({m.group(0)!r})')
    for m in URL.finditer(line):
        if m.group(0).lower() != studio.SITE_LABEL:
            why.append(f"a web address ({m.group(0)!r})")
    if EMAIL.search(line):
        why.append("an email address")
    elif HANDLE.search(line):
        why.append("an @ handle")
    if PHONE.search(line):
        why.append("a phone number")
    if MONEY.search(line):
        why.append(f"a dollar amount or a price ({MONEY.search(line).group(0)!r})")
    if HEX.search(line):
        why.append(f"a hex string of 7 or more characters ({HEX.search(line).group(0)!r})")
    if OTA.search(line):
        why.append(f"an OTA or commit id ({OTA.search(line).group(0)!r})")
    v = VERSION.search(line)
    if v and not CAN.search(line[v.end():]):
        why.append(f"a version or build number ({v.group(0)!r}) with no \"can\" after it saying what a person can now do")
    rx, problem = deny_rx(deny)
    if problem:
        why.append(problem)
    elif rx.search(line):
        why.append("a word or phrase from the --deny file")
    for e in log["entries"]:
        if dice(line, e["line"]) >= OVERLAP:
            why.append(f'it repeats an existing line ({e["date"]}: "{e["line"]}")')
            break
    return why


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check one build log line before it goes in.")
    ap.add_argument("--deny", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--line", required=True)
    ap.add_argument("--today", help="for tests: the day to count from, YYYY-MM-DD")
    ap.add_argument("--shipped", help="for tests: the build log to check against")
    args = ap.parse_args(argv)
    today = datetime.date.fromisoformat(args.today) if args.today else None
    why = check(args.date, args.project, args.line.strip(), args.deny, today, args.shipped)
    if why:
        print("FAIL")
        for w in why:
            print("- " + w)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
