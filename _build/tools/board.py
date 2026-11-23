#!/usr/bin/env python3
"""The build log, one line at a time (T-42, Nov 22, 2026).

    python3 tools/board.py add --date YYYY-MM-DD --project <id> --line '<text>'
    python3 tools/board.py build

Run from _build/. Python 3's standard library only: no Pillow, no Playwright, no Node,
no network. Made for the nightly build log job, which checks a line with
tools/board_guard.py first; a site session can use it too.

add    puts one entry into shipped.json in date order (at the top of its date, so the
       file stays newest first), refuses one whose date, project and line are already
       there, then runs build. If anything fails, every file it wrote is put back.
build  rebuilds studio.html and every studio-<id>.html and writes them into _build/
       (what tools/studio.py writes) and the repo root, byte for byte what the full
       pipeline in _build/README.md would put there. It touches no other file.

How: the full build runs dump.js (Node) and build.py for every page, then the passes.
A Studio page doesn't need the first two: tools/studio.py writes it whole. So this runs
studio.py, then on each Studio page only, the same code the passes run, in their order:
  enhance.py  studio_steps(): the client name, the closing call box (studio.html), the
              phone menu, the orange button contrast, the public email; its checks
  plain.py    apply(): every plain-words edit, in order
  intent.py, voice2.py   nothing (no edit names a Studio page; checked on every run)
  final.py    the visit counter, if CF_BEACON_TOKEN is set, and nobreak_checked()
  theme.py    theme_page()
The sitemap has no lastmod, so it never changes for a new line. A Studio page that
appears or goes (a product's gate or join list changed) needs the full build, its
sitemap line and its share card: build stops and says so.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import tempfile

TOOLS = pathlib.Path(__file__).resolve().parent
HERE = TOOLS.parent                 # _build/
ROOT = HERE.parent                  # the repo root, the public site
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(HERE))

import studio                       # noqa: E402

SHIPPED = HERE / "shipped.json"


def write_shipped(data):
    """shipped.json in its own layout: one entry per line, newest first."""
    body = ('{\n  "_about": ' + json.dumps(data["_about"], ensure_ascii=False) + ',\n  "entries": [\n'
            + ",\n".join("    " + json.dumps(e, ensure_ascii=False) for e in data["entries"]) + "\n  ]\n}\n")
    SHIPPED.write_text(body, encoding="utf-8")


def insert(data, entry):
    """The entry at the top of its date; the entries stay newest first."""
    es = data["entries"]
    key = (entry["date"], entry["project"], entry["line"])
    if any((e["date"], e["project"], e["line"]) == key for e in es):
        raise SystemExit(f"board.py: already in shipped.json: {entry['date']} {entry['project']}: {entry['line']}")
    i = next((k for k, e in enumerate(es) if e["date"] <= entry["date"]), len(es))
    es.insert(i, entry)


def passes_leave_studio_alone():
    """intent.py and voice2.py name every page they edit; none may be a Studio page, or this
    tool would leave out an edit the full build makes."""
    for name in ("intent.py", "voice2.py"):
        src = (HERE / name).read_text(encoding="utf-8")
        code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
        if re.search(r"""\(\s*['"]studio""", code) or re.search(r"\bfor\s+\w+\s+in\s+pages\b", code):
            raise SystemExit(f"board.py: {name} edits a Studio page or every page now; add that step to "
                             "board.py, or run the full build (_build/README.md)")


def studio_files(folder):
    return sorted(p.name for p in pathlib.Path(folder).glob("studio*.html"))


def build():
    import enhance, plain, final, theme      # imported here: enhance.py reads studio.json at import
    passes_leave_studio_alone()
    pages = list(enhance.STUDIO_PAGES)        # from studio.json, as the full build counts them
    if sorted(pages) != studio_files(HERE) or sorted(pages) != studio_files(ROOT):
        raise SystemExit("board.py: the Studio pages changed (now " + ", ".join(pages) + "); a new or closed "
                         "product page needs the full build, its sitemap line and share card (_build/README.md)")
    studio.main(str(HERE))                    # writes _build/studio.html and each studio-<id>.html
    token = final.CF_BEACON_TOKEN
    if token and not re.fullmatch(r"[A-Za-z0-9]+", token):
        raise SystemExit("board.py: CF_BEACON_TOKEN in final.py must be the token only")
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        for f in pages:
            t = (HERE / f).read_text(encoding="utf-8")       # as enhance.py's add_pages() reads it
            t = enhance.studio_steps(f, t)
            t = plain.apply(t)
            if token and f not in final.NO_BEACON:
                if "cloudflareinsights.com" in t or t.count("</body>") != 1:
                    raise SystemExit(f"board.py: {f}: the visit counter has no single place to go")
                t = t.replace("</body>", final.BEACON % token + "</body>")
            t, problem = final.nobreak_checked(f, t)
            if problem:
                raise SystemExit("board.py: " + problem)
            # The page as the passes leave it in out/, then read back the way theme.py reads it.
            p = pathlib.Path(tmp) / f
            p.write_text(t, encoding="utf-8")
            with open(p, encoding="utf-8", newline="") as fh:
                t = fh.read()
            try:
                out[f] = theme.theme_page(t, f)
            except theme.Unknown as e:
                raise SystemExit(f"board.py: theme.py doesn't know a color: {e}")
    for f, t in out.items():
        with open(ROOT / f, "w", encoding="utf-8", newline="") as fh:   # as theme.py writes out-themed/
            fh.write(t)
        print("board.py: wrote", f)


def add(date, project, line):
    try:
        day = datetime.date.fromisoformat(date)
    except ValueError:
        raise SystemExit(f"board.py: --date must be YYYY-MM-DD, not {date!r}")
    if day.isoformat() != date:
        raise SystemExit(f"board.py: --date must be YYYY-MM-DD, not {date!r}")
    st, data = studio.load()
    if project not in studio.labels(st):
        raise SystemExit(f'board.py: no label for project "{project}" (a product in studio.json, or its "labels")')
    line = line.strip()
    if not line or "—" in line:
        raise SystemExit("board.py: the line is empty or has an em dash")
    keep = {p: p.read_bytes() for p in [SHIPPED] + [HERE / f for f in studio_files(HERE)] + [ROOT / f for f in studio_files(ROOT)]}
    insert(data, {"date": date, "project": project, "line": line})
    try:
        write_shipped(data)
        build()
    except BaseException:
        for p, b in keep.items():
            p.write_bytes(b)
        print("board.py: failed; shipped.json and the Studio pages are as they were", file=sys.stderr)
        raise
    print(f"board.py: added {date} {project}: {line}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Add a line to the build log and rebuild the Studio pages.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--date", required=True)
    a.add_argument("--project", required=True)
    a.add_argument("--line", required=True)
    sub.add_parser("build")
    args = ap.parse_args(argv)
    if args.cmd == "add":
        add(args.date, args.project, args.line)
    else:
        build()


if __name__ == "__main__":
    main()
