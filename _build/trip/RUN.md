# Paste this into Claude Code (on the web, repo dragomans-journey-site, branch main)

```
git fetch --all. Find the newest trip/T-0N branch on origin (highest number); if there is none, use origin/main. Check it out and read _build/trip/QUEUE.md there, top to bottom, including the house rules. That copy holds the latest statuses and receipts.

Do the first item whose status says READY. Skip GATED and DONE items. If an item says READY (build), GATED (deploy), do the build part only.

Cut a branch named trip/<item id> from the branch you just read. Say in one line which item you're doing and which branch you cut from.

Follow the item's steps exactly. Follow every house rule: never push to main, edit the _build sources, rebuild with the pipeline, run the tests, open the screenshots at 390 and 1440 wide.

If anything would need a guess about wording, money, people or what goes live, stop and write the question in the item's Receipt instead of guessing.

When it's done: fill in the Receipt, set the status to DONE, commit with explicit file paths (never git add -A), push the branch, and end with a plain-language summary of 5 lines or fewer: what changed, the test count, and the one thing Josef has to do, if any.
```
