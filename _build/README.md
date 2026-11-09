# How this site is built

Jekyll skips folders that start with an underscore, so nothing in `_build/` is served.

1. `canvas/` holds the three design pages (`.dc.html`), the same files as the claude.ai Design canvas.
2. `node dump.js canvas vals.json` evaluates each page's `renderVals()` for every interactive state.
3. `python3 build.py canvas out vals.json` writes `index.html`, `local.html`, `mainframe.html`, `404.html`, `sitemap.xml`, `robots.txt`, `favicon.svg`, `CNAME`.
4. `python3 enhance.py out` adds what the canvas doesn't carry: the packed-decimal decoder (`comp3.html`), tap-a-number sources on the receipts, the raw-to-reel timeline, the intake quiz, drop-in hours, and stand-ins for the photo.
4b. The four free tools (`shotlist.html`, `captions.html`, `receipt.html`, `scaler.html`, added Nov 8, 2026) are written by `tools/`: `cd tools && python3 shotlist.py ..` (same for `captions.py`, `receipt.py`, `scaler.py`) regenerates the template in `_build/`, with the shared header and footer from `tools/chrome.py`. Edit the `.py` file, never the generated page. `enhance.py` copies them into `out/`, along with `assets/bird-league-then-now.jpg` for the Bird League card on `work.html`.
4c. Share cards (Nov 9, 2026): `python3 tools/og.py out` draws a 1200 by 630 PNG per public page into `assets/og/` from each finished page's `<h1>` and meta description, with the fonts in `assets/fonts/` (OFL). It reads the pages after steps 5 and 6, so rerun it after a build whenever a headline or description changes, then rebuild from step 4. `enhance.py` copies the cards to `out/og/` and adds the `og:image` and `twitter:card` tags (the four tools get theirs from `tools/chrome.py`). Copy `out/og/` to `og/` at the repo root along with the pages.
5. `python3 plain.py out` runs the plain-language pass (Oct 26, 2026) over the finished pages. Every edit must hit at least once.
6. `python3 intent.py out` runs the intent pass (Oct 28, 2026): every word on a page is there on purpose for a specific reader. Each edit carries its line ID from the audit in the vault (`Claude outputs/2026-10-28-intent-audit-dragomans-journey.md`) and must match exactly, or nothing is written.
7. Serve `out/` locally and run `test_site.py` and `test_new.py`.

Settings at the top of `enhance.py`: `DROPIN_DATE`, `DROPIN_PLACE`, `LINKEDIN`. Fill them in and rebuild.
