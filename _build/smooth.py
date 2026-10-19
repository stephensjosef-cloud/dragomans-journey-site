#!/usr/bin/env python3
"""Anti-AI smoothing pass, Oct 18 2026. Each edit must match exactly once."""
import sys
from pathlib import Path

D = Path(sys.argv[1])

EDITS = {
    "Fork.dc.html": [
        ("Your phone footage or the task that eats your week, turned into reels, program apps and workflows that run, each with its receipts.",
         "Bring the phone videos, the binder of lessons or the task that eats your week. I turn it into reels, apps and workflows that run, and each one comes with the logs to prove it."),
        ("An equivalence harness built for your estate, and a dossier your auditors can reproduce, byte for byte, before anything touches production.",
         "A harness that runs the old and new systems over your own files and compares what they write, plus a dossier your auditors can rerun before anything touches production."),
    ],
    "Main.dc.html": [
        ("I'm Josef. I turn what you already have, like the phone videos nobody has time to edit or the lessons living in a binder, into reels, apps and workflows that run without you babysitting them. Each one ships with its proof, and a person signs off before anything reaches your customers.",
         "I'm Josef. You already have the raw material: phone videos nobody has time to edit, lessons living in a binder. I turn it into reels, apps and workflows that run without babysitting. Each one ships with a way to check it, and nothing reaches your customers until a person has signed off."),
        ("By then it has either broken without anyone noticing or started sounding like nobody you know, and whoever pays for it can't say what it does anymore. So everything here ships with a way to check it, and a person stands between the machine and your customers.",
         "By then it has quietly broken, or it has started sounding like nobody you know, and the person paying for it can't say what it does anymore. That's why everything I build comes with a one-page check each month that you can read in a minute."),
        ("Finished work you can put in front of a customer, made on machinery I built and test on every job, so you aren't paying me to invent it from scratch.",
         "Finished work you can put in front of a customer. It's made on tools I built and test on every job, so you aren't paying me to invent anything from scratch."),
        ("One process that eats your week, rebuilt with AI and a person at the gate.",
         "The one task that eats your week, rebuilt to run on its own."),
        ("I'm new at this as a business, and I'd rather show you real numbers from real runs than borrow anybody's credibility. Every figure here comes from a log I can open in front of you.",
         "The business is new, so instead of borrowed credibility, here are real numbers from real runs. I can open the log behind any of them while you watch."),
        ("A dragoman was the guide who got travelers through country where they didn't speak the language. You won't need to learn the AI part either.",
         "Three dates, agreed before we start, so you always know what happens next."),
        ("One working sample made from your own material, so you judge the craft, not a pitch.",
         "A working sample made from your own material. You see real work before you decide anything."),
        ("The tradeoff is capacity, so I take on a limited number of new projects.",
         "The tradeoff is capacity. I only run a few projects at once."),
        ("What you run, and the one part of it that never gets done. I read every message myself. I take on a small number of Blueprints at a time, so if I'm full I'll tell you when the next one opens.",
         "Two lines is plenty: what you run, and the part of it that never gets done. I read every message myself, and if I'm full I'll tell you when the next spot opens."),
        ("The rule that won't let a kids' recipe publish without naming the grown-up's job is the same rule that won't let a migrated interest routine ship with an unresolved question. For banks, insurers and agencies moving COBOL with AI, that rule becomes a harness that proves the new system behaves like the old one.",
         "The rule that stops a kids' recipe from publishing until it names the grown-up's job also stops a migrated interest routine from shipping with an open question. For banks, insurers and agencies moving COBOL with AI, it takes the form of a harness that checks the new system against the old one."),
        ("'Then the Blueprint is the move. Two weeks, and you will know.'",
         "\"Then start with the Blueprint. In two weeks you'll know what's worth building.\""),
        ("\"That's a Built-to-Prove Workflow, with a person at the gate.\"",
         "\"That's a Built-to-Prove Workflow: one task, rebuilt to run on its own.\""),
        ("'Those \"never\" rows are enforced by the database, not by a promise. A careless edit at midnight gets refused instead of published.'",
         "'The database enforces those \"never\" rows itself. A careless edit at midnight gets refused instead of published.'"),
        ("'This is where the habit comes from. Anything I make for you gets checked the way I checked an AI’s translation of an old-style banking program: against the original, with the misses written down where you can see them.'",
         "'This is where the habit started. I checked an AI’s translation of an old banking program against the original and wrote down every miss. Your work gets checked the same way.'"),
    ],
    "Mainframe.dc.html": [
        ("I build the harness that proves a migrated system behaves exactly like the original, byte for byte, and I hand your auditors the evidence before anything touches production.",
         "I build the harness that runs the original and the migrated system over the same files and compares every byte they write. Your auditors get the evidence before anything touches production."),
        ("Every artifact is testimony. <em style=\"color: #A93F17\">The bytes are the arbiter.</em>",
         "Every source has an opinion. <em style=\"color: #A93F17\">The stored bytes settle it.</em>"),
        ("In a real estate the pieces disagree.",
         "In a real mainframe estate the sources disagree."),
        ("Referenceable behavioral equivalence, finding by finding: a document your model-risk team",
         "Behavioral equivalence written up finding by finding, in a document your model-risk team"),
        ("The harness that guards a bank's interest routine also runs a studio for small businesses and nonprofits in Sonoma County: reels, program apps and workflows, each shipped with its receipts. Small productions keep the method honest. Every week it meets real people who notice when something is off.",
         "The method that guards a bank's interest routine also runs a small studio for businesses and nonprofits in Sonoma County: reels, program apps and workflows, each shipped with its run logs. The small jobs keep it honest. Every week real people use what it makes, and they notice when something is off."),
        ("I don't review somebody's translation by the hour. I build the instrument that proves it, and you keep the instrument.",
         "I don't review translations by the hour. I build the instrument that checks them, and you keep it."),
        ("<a href=\"#s4\">§4 Dossier</a>",
         "<a href=\"#s4\">§4 Dossier</a>\n      <a href=\"#s5\">§5 Limits</a>"),
        ("<section aria-labelledby=\"s6-h\">",
         "<section id=\"s5\" aria-labelledby=\"s6-h\">"),
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
