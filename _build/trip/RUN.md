# Paste this into Claude Code (on the web, repo dragomans-journey-site, branch main)

```
git fetch --all. List the branches on origin named trip/*. Take the one with the most recent commit date (not the highest number: items are not done in number order). If there is none, use origin/main. Check it out and read _build/trip/QUEUE.md there, top to bottom, including the house rules. That copy holds the latest statuses and receipts.

Do the first item, in file order, whose status says READY. Skip GATED, BLOCKED and DONE items. If an item says READY (build) followed by a GATED part, do the build part only, then set its status to DONE (build), GATED and name the gate.

Cut a branch named trip/<item id> from the branch you just read. Say in one line which item you're doing and which branch you cut from.

Follow the item's steps exactly. Follow every house rule: never push to main, edit the _build sources, rebuild with the pipeline, run the tests, open the screenshots at 390 and 1440 wide.

This repository is public. Write nothing personal into it: no client names, no people's names except Josef Stephens, no travel or schedule details.

If anything would need a guess about wording, money, people or what goes live, stop and write the question in the item's Receipt instead of guessing. Then set that item's status to BLOCKED (question), commit and push, so the next run moves on. Skip BLOCKED items.

When it's done: fill in the Receipt, set the status to DONE, commit with explicit file paths (never git add -A), push the branch, and end with a plain-language summary of 5 lines or fewer: what changed, the test count, and the one thing Josef has to do, if any.
```
