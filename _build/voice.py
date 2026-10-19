#!/usr/bin/env python3
"""Voice overhaul, Oct 18 2026: the guide who takes it from here.
Fun, warm, informative, clever. Same prices, same approved promises.
Each edit must match exactly once."""
import sys
from pathlib import Path

D = Path(sys.argv[1])

EDITS = {
    "Fork.dc.html": [
        ('>one rule</em></h1>', '>one guide</em></h1>'),
        ("Nothing I make reaches your customers or your production systems until a person has checked the proof. That holds for a kids' cooking app and for a bank's interest routine.",
         "A kids' cooking class and a bank's core systems need the same thing from AI: a guide who knows the ground and won't let anything reach your customers until a person has checked the proof. Pick your route. I'll take it from here."),
        ("Bring the phone videos, the binder of lessons or the task that eats your week. I turn it into reels, apps and workflows that run, and each one comes with the logs to prove it.",
         "Bring the phone videos, the binder of lessons or the chore that eats your Tuesdays. I'll turn it into reels, apps and workflows that run, with the logs to prove it."),
        ('How the two routes <em style="color: #A93F17">line up</em>',
         'Same guide, <em style="color: #A93F17">different terrain</em>'),
        ("What stays the same on either route", "The rules I travel by"),
        ("The first step is paid, fixed and fully credited.", "The first step is small, fixed and fully credited."),
        ("And it's allowed to conclude that you don't need me.", "If the honest answer is that you don't need me, that's the answer you get."),
        ("An interpreter and guide for travelers crossing country where they didn't speak the language. Whether it's a kids' recipe or an interest routine, the job is getting you across without losing the meaning.",
         "For centuries, travelers crossing unfamiliar country hired a dragoman, an interpreter and guide who knew the language and the safe roads. AI is unfamiliar country for most businesses. My job is getting you across with your meaning intact."),
    ],
    "Main.dc.html": [
        ("I'm Josef. You already have the raw material: phone videos nobody has time to edit, lessons living in a binder. I turn it into reels, apps and workflows that run without babysitting. Each one ships with a way to check it, and nothing reaches your customers until a person has signed off.",
         "I'm Josef, and this is the part where you hand it over. The phone videos nobody has time to edit, the lessons living in a binder: I'll take it from here. You get reels, apps and workflows that run without babysitting, each with a way to check it, and nothing reaches your customers until a person has signed off."),
        ("Most AI work for small businesses goes wrong around month two", "Month two is where most AI projects get lost"),
        ("By then it has quietly broken, or it has started sounding like nobody you know, and the person paying for it can't say what it does anymore. That's why everything I build comes with a one-page check each month that you can read in a minute.",
         "The demo dazzles. A few weeks later it has quietly broken, or it sounds like nobody you know, and nobody can say what it does anymore. I plan for month two on day one: everything I build comes with a one-page check each month that you can read in a minute."),
        ("Tap one. I'll point you at the right thing.", "Tap one and I'll show you the way in."),
        ("\"Honestly, I'm not sure yet\"", "\"Not sure yet. Point me somewhere.\""),
        ("\"Then start with the Blueprint. In two weeks you'll know what's worth building.\"",
         "\"Then we start with the Blueprint. Two weeks from now, you'll have a map.\""),
        (">What I build</h2>", ">Three engines, already road-tested</h2>"),
        ("Finished work you can put in front of a customer. It's made on tools I built and test on every job, so you aren't paying me to invent anything from scratch.",
         "Each one is built, tested and running on real work. You get finished pieces you can put in front of a customer, and you don't pay me to invent the machine first."),
        ("No client logos yet, so here are the logs", "Don't take my word for it. Take the logs."),
        ("The business is new, so instead of borrowed credibility, here are real numbers from real runs. I can open the log behind any of them while you watch.",
         "Real numbers from real runs, every one tied to a log. Pick a tab, tap a number, and ask me to open the log on a call."),
        ("How it goes, start to finish", "The route, start to finish"),
        ("Three dates, agreed before we start, so you always know what happens next.",
         "Three stops, agreed before we set out, so you always know where we are and what comes next."),
        ("I sit in on the real work. In person anywhere in Sonoma County.",
         "I come to you and watch the real work happen, anywhere in Sonoma County."),
        ("Where the usual options tend to break", "The other roads, and where they wash out"),
        (">A good fit</h3>", ">This route is for you if</h3>"),
        (">Not a fit</h3>", ">Pick another guide if</h3>"),
        ("Nobody would call it exciting. It's why the reels come out right.",
         "It's the least glamorous thing I've made, and it's why the reels come out right."),
        ("Questions worth asking first", "Fair questions, straight answers"),
        ("Two lines is plenty: what you run, and the part of it that never gets done. I read every message myself, and if I'm full I'll tell you when the next spot opens.",
         "Two lines is plenty: what you run, and the part that never gets done. I read every message myself and write back with the next step."),
    ],
    "Mainframe.dc.html": [
        ("Four stages, each with a fixed scope and a fixed fee", "Four stages to the other side, each with a fixed scope and a fixed fee"),
        ("I haven't spent thirty years on a mainframe. Since March I've been building the proof layer the field keeps saying is missing, in public, with my misses published next to my results.",
         "I'm not a thirty-year mainframe veteran. I'm the one who checks what the veterans and the AIs both assume, and since March I've done it in public, with my misses published next to my results."),
        ("Write with the program family you're least sure about, roughly how large the estate is, and where the migration stands. I reply personally, and if it isn't a fit, I'll tell you who might be.",
         "Write with the program family you're least sure about, roughly how large the estate is and where the migration stands. I'll reply personally with what I'd look at first, and if it isn't a fit, I'll tell you who is."),
    ],
}

for name, edits in EDITS.items():
    p = D / name
    t = p.read_text(encoding="utf-8")
    for old, new in edits:
        n = t.count(old)
        assert n == 1, f"{name}: expected 1 of {old[:70]!r}, found {n}"
        t = t.replace(old, new)
    assert "—" not in t, name + " has an em dash"
    p.write_text(t, encoding="utf-8")
    print(name, len(edits), "edits")
