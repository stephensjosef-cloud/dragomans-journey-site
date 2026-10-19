# How this site is built

Jekyll skips folders that start with an underscore, so nothing in `_build/` is served.

1. `canvas/` holds the three design pages (`.dc.html`), the same files as the claude.ai Design canvas.
2. `node dump.js canvas vals.json` evaluates each page's `renderVals()` for every interactive state.
3. `python3 build.py canvas out vals.json` writes `index.html`, `local.html`, `mainframe.html`, `404.html`, `sitemap.xml`, `robots.txt`, `favicon.svg`, `CNAME`.
4. `python3 enhance.py out` adds what the canvas doesn't carry: the packed-decimal decoder (`comp3.html`), tap-a-number sources on the receipts, the raw-to-reel timeline, the intake quiz, drop-in hours, and stand-ins for the photo.
5. Serve `out/` locally and run `test_site.py` and `test_new.py`.

Settings at the top of `enhance.py`: `DROPIN_DATE`, `DROPIN_PLACE`, `LINKEDIN`. Fill them in and rebuild.
