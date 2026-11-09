# Build queue: dragomansjourney.com

Josef fires one item at a time and checks the result later. Every item below is complete: no question should need asking. If one does, stop and write the question in the item's receipt instead of guessing.

## How to run an item (the same every time)

Start a Claude Code session on the web on repo `stephensjosef-cloud/dragomans-journey-site`, branch `main`, and paste the block in `_build/trip/RUN.md`. That's it. Claude Code picks the next READY item.

## House rules for every item

1. **Never push to `main`.** `main` is the live site (GitHub Pages). Each item commits to its own branch `trip/T-0N`, cut from the newest DONE `trip/` branch (or `main` if there is none), so the branches stack in a line and the newest one holds everything. Going live is Josef saying "push it" to Claude in chat.
2. **Use the pipeline.** Edit `_build/` sources (templates, `enhance.py`, `build.py`, `_build/tools/*.py`), never only the root files. Rebuild with the 6 steps in `_build/README.md`, copy `out/*` to the repo root, and confirm with `cmp` that pages you didn't mean to touch are byte-for-byte unchanged.
3. **Test.** Serve `out/` on port 8765 and run `python3 _build/test_new.py http://localhost:8765/ /tmp/shots`. If Chromium isn't at `/opt/pw-browsers`, run a copy with `exe = None` and `p.chromium.launch()`; never edit the test's expectations to make a failure pass, only to describe a change the item asked for. Add checks for anything new.
4. **Look.** Screenshot every page you changed at 390 and 1440 wide and open the screenshots. No sideways scroll at 390.
5. **Words.** No em dashes. Plain words, short sentences. Every word on a page is there for a specific reader (the intent rule, `Claude outputs/2026-10-28-intent-audit-dragomans-journey.md` in the vault). The nonprofit client is never named: say "a Sonoma County children's nonprofit".
6. **Nothing leaves the visitor's device** in any tool unless the visitor presses a button that says so.
7. **Receipt.** When done, fill in the item's Receipt section in this file (commit, branch, test count, screenshots looked at, anything Josef must do by hand, in numbered exact steps), change its status to DONE, and commit that too.

---

## T-01 · Share cards for every page · DONE

**Why:** this week's LinkedIn posts and texts link to the site. Right now a shared link shows no picture. A good card doubles the taps.

**Build:**
1. New script `_build/tools/og.py` (Python + Pillow) that writes a 1200 by 630 PNG for each page into `_build/assets/og/`: index, local, mainframe, work, comp3, shotlist, captions, receipt, scaler, start, call, case-reels.
2. Look: background `#0E1B17`, the mountain mark and "Dragoman's Journey" top left in `#E9EEE9`, the page's own headline big in Big Shoulders Display 800 uppercase (download the font files once from Google Fonts into `_build/assets/fonts/`, they're OFL), a one-line subhead in Instrument Sans, and a `#E8592B` bar along the bottom. Free tools get a small "FREE TOOL" tag in JetBrains Mono. Text must fit with 64px margins; shrink the headline until it does.
3. Headlines: use each page's `<h1>` (strip `<br>`). Subheads: each page's meta description, cut at a sentence end under 110 characters.
4. Add to every page's head: `og:image` (absolute URL `https://dragomansjourney.com/og/<page>.png`), `og:image:width` 1200, `og:image:height` 630, `twitter:card` summary_large_image. For tool pages, add it in `_build/tools/chrome.py`. For pipeline pages, add it in `enhance.py` (one function, run last). `enhance.py` copies `_build/assets/og/*.png` to `out/og/`.
5. Test: every page has exactly one `og:image`, and the file it names exists in `out/og/`.

**Done when:** all 12 cards exist, each looked at, tests pass.

**Receipt:**
- **Branch:** `trip/T-01`, cut from `origin/free-tools` (no `trip/` branch existed yet). Work commit `3b25267`, receipt in the commit after it. Nothing pushed to `main`.
- **What's built:** `_build/tools/og.py` draws the cards into `_build/assets/og/` (fonts from Google Fonts in `_build/assets/fonts/`, with their OFL files). `enhance.py` (`add_og()`, run last) copies them to `out/og/` and tags the 9 pipeline pages. `tools/chrome.py` tags the 4 tools. Each page gets `og:image` (absolute `https://dragomansjourney.com/og/<page>.png`), `og:image:width` 1200, `og:image:height` 630, and `twitter:card` summary_large_image. Step 4c added to `_build/README.md`.
- **13 cards, not 12:** `briefing.html` is a public page too, and the item says every page gets an `og:image`, so it has its own card made by the same rule. `404.html` has none (it's noindex).
- **Subheads, where the rule needed help (no new words, all the page's own):** five descriptions have no sentence end under 110 characters. `work` and `case-reels` use the first sentence of their own `og:description`. `local`, `shotlist`, `captions`, `scaler` and `receipt` are cut at the last comma or colon under 110 and end with a period. On `index` the first sentence ("AI, made easy.") repeats the headline, so the card uses the next one. Headlines are balanced so no line is a single word; where the page's own `<br>` gives the same number of lines, that break is used ("COOK FOR 4. / FEED 24.").
- **Pipeline:** the unchanged pipeline rebuilt every root file byte for byte first. After the change, `cmp` shows only the 13 pages differ from that baseline, by exactly the 4 head lines each; `404.html`, `sitemap.xml`, `robots.txt`, `CNAME`, `favicon.svg` and the images are unchanged. Root `og/` holds the 13 PNGs, identical to `out/og/`.
- **Tests:** `test_new.py` **160/160 passed** (53 new: one `og:image` per page, it names the page's own card, the size tags and `twitter:card` are there, the PNG is served from `og/` at 1200x630, and 404 has none). Against the old build, the new checks fail as they should (13 failures). Chromium isn't at the test's `/opt/pw-browsers/chromium-*/chrome-linux/chrome` path in this container, so it ran as a copy with `exe = None` and `p.chromium.launch()`, as house rule 3 says. `test_site.py` times out waiting for `networkidle` on `index.html` in this container, the same on the untouched baseline build, so it's this environment and not this change.
- **Looked at:** all 13 cards at full size and as a sheet. Every card measures inside the 64px margins (checked by pixel). All 13 changed pages screenshotted at 390 and 1440: no sideways scroll at either width, and nothing visible changed (the change is head-only).
- **Josef, by hand:**
  1. Read the 13 cards in `_build/assets/og/` (or look at the sheet in this chat). If a subhead should say something else, change that page's meta description and ask Claude to rebuild.
  2. When happy, say "push it" to Claude in chat. That merges this into `main` and the site goes live.
  3. After it's live, open https://www.linkedin.com/post-inspector/, paste `https://dragomansjourney.com/local.html`, press Inspect, and check that the card shows. Do the same for any link you already shared this week, because LinkedIn keeps the old preview until you inspect it.

---

## T-02 · Make the free tools findable · READY

**Why:** right now the tools are only reachable from the work page.

**Build:**
1. Header nav on every page gets "Free tools" linking to `work.html#free`, placed before "Free 15-min call". Pipeline pages: in `enhance.py`. Tool pages: in `chrome.py`.
2. On `local.html`, add one short section just before the contact section: heading "Free tools for your pile", then a row of four small cards (title + one line + link), same cards as the work page. Mobile: one column.
3. On each tool page, under the tool and above the dark panel, a quiet line: "More free tools:" then links to the other three by name.
4. Tests: every page's nav has `work.html#free`; local.html has 4 tool links in the new section.

**Done when:** tested and looked at on both widths.

**Receipt:**

---

## T-08 · The Studio page and the public build log · READY

**Why:** Josef wants everything he's building on the site, packaged so people feel they're missing out if they aren't involved. The honest way: show real, dated momentum. He ruled Nov 9: a new Studio section; Dragoman's Journey stays the front door for clients.

**The content is already written.** `_build/studio.json` (every product, its status, what it is, its proof line, its link or join list, and a gate) and `_build/shipped.json` (the dated build log, newest first). Use their words exactly. Don't invent products, numbers or dates. A product with a non-null `gate` does not render at all.

**Build:**
1. `_build/tools/studio.py` (uses `chrome.py`) writes `_build/studio.html` from the two JSON files. Add `studio.html` to `enhance.py` (both page lists) and `build.py` (sitemap). Add `og.py` support so it gets a share card.
2. Top: the hero from `studio.json`. Right under it, a numbers strip computed at build time from `shipped.json` only: "<N> things shipped since <oldest date>", "<M> in the last 30 days", and "<K> projects". Real counts, nothing typed by hand.
3. Then "Shipped lately": the 8 newest log lines, each with its date (Nov 8), a small project label, and the line. A "See all <N>" toggle reveals the rest in place (no new page). Entries older than 120 days drop off at build time.
4. Then the products, as big cards in the order given: name, a status pill, the kind, "what", the proof line in bold if present, the image if present (Bird League uses `bird-league-then-now.jpg`, already in the repo), then the link and/or the join-list button. Two columns at desktop, one on phones. Bird League spans the full width like on the work page.
5. Join-list buttons: until T-10 is live, each opens `mailto:hello@dragomansjourney.com?subject=List: <product name>`. A list count shows only when it's 10 or more ("41 people on the list"); below 10, nothing.
6. Header nav on every page gets "Studio" (before "Free tools" if T-02 is done). The home page (`index.html`) gets a slim band under its hero: the newest 3 log lines and "See everything I'm building →" to `studio.html`. Do it in `enhance.py`, reading `shipped.json`.
7. Words: no em dashes; plain; the nonprofit client never named; every line is from the JSON.
8. Tests: studio.html renders every non-gated product and no gated one; the numbers strip matches `shipped.json`; the home band shows the newest 3; the nav link is on every page; no overflow at 390.

**Done when:** tested, screenshots looked at, and the receipt says how a new log line gets added (Claude appends to `shipped.json` and rebuilds; Josef never edits it).

**Receipt:**

---

## T-09 · Product pages that make people want in · READY

**Why:** a card says what a thing is. A page per product shows it's real and moving, and gives one obvious way in.

**Build:**
1. `studio.py` also writes one page per non-gated product that has a join list: `studio-birdleague.html`, `studio-deepcuts.html` (and later `studio-album.html` once its gate clears).
2. Each page: the product's name big; status pill; "what"; the proof line; the image if any; "Shipped lately" filtered to that project (all its log lines, newest first, with dates); and one join box: email field + the list's button, with one line under it: "One email when it's out. No newsletter." Until T-10 is live, the box is a mailto button with the same subject as T-08.
3. Each studio card links to its page ("See it move →").
4. Share cards for each new page through `og.py`.
5. Tests: one page per eligible product; each page's log matches `shipped.json` for that project.

**Receipt:**

---

## T-10 · Real join lists · READY (build), GATED (deploy)

**Why:** the lists have to work without Josef touching them.

**Build:**
1. Add a `list` form to `_build/worker/intake.js` (keep everything else byte-for-byte): fields `email` (required), `name` (optional), `list` (required, one of `birdleague`, `deepcuts`, `album`, `spots-feb`). Subject `List: <list> · <email>`. Same honeypot and 2.5-second minimum as the other forms. Write the deployable single file next to it as `intake.deployed.js` (same format as now).
2. The join boxes from T-08 and T-09 post to the Worker the same way `start.html` does (copy its fetch, honeypot and timing code), show "You're on the list" on success, and fall back to the mailto if the send fails.
3. Counting needs no database: Claude in chat counts the `List:` emails in Josef's Gmail when it next updates the site, writes the numbers into `studio.json`, and rebuilds. Note that in the receipt.
4. Tests: the form posts the right fields (intercept the request in Playwright, don't send); success and failure states both render.

**Gate for deploy:** Josef pastes the new `intake.deployed.js` over the old one in the Cloudflare dashboard (Workers and Pages, `dj-intake`, Edit code, paste, Deploy). Exact numbered steps go in the receipt. Until then the mailto fallback works, so nothing is broken in the meantime.

**Receipt:**

---

## T-03 · Five Santa Rosa spots counter · GATED

**Gate:** Josef has said in chat that Monday's emails went out (the contact rule). Claude marks this READY when he does. Do not start it while it says GATED.

**Why:** the push ruled Nov 3: five Blueprint spots for Santa Rosa businesses and nonprofits, Nov 9 to Jan 31. The count is real and each filled spot is a post.

**Build:**
1. `_build/spots.json`: `{"total": 5, "taken": 0, "ends": "2026-01-31", "city": "Santa Rosa"}`. This is the only thing Josef ever edits to change the count.
2. `enhance.py` reads it and adds a slim band under the header on `index.html`, `local.html`, `work.html` and `start.html`: "5 Blueprint spots for Santa Rosa, through January. 5 open." with "Start a Blueprint →" (on start.html, no link). Five small squares, filled for taken. When `taken` equals `total`: "All 5 Santa Rosa spots are taken. Join the list for February." linking to `call.html`.
3. After Jan 31 the band doesn't render (build-time date check, America/Los_Angeles).
4. Tests: band present on the 4 pages with the right numbers; set taken to 5 in a temp copy and check the full message; set the date past and check it's gone.
5. Receipt includes exact steps for changing the count later (edit one number, ask Claude to rebuild and push).

**Receipt:**

---

## T-04 · Website checkup tool · READY (build), GATED (deploy)

**Why:** the "broken button" idea from the Nov 2 push, as a free tool. An owner pastes their site's address and gets a plain report of what's broken. A browser page can't fetch another site, so this needs a small Cloudflare Worker.

**Build:**
1. New Worker `_build/worker/checkup.js` (separate from `intake.js`; do not touch intake). `GET /?url=<https://...>`, CORS for the same origins as intake.
2. Safety first: only `http` and `https`; only ports 80 and 443; refuse IP-address hosts, `localhost`, `.local`, `.internal` and any private range; follow at most 3 redirects, re-checking each hop; 8-second timeout per request; read at most 1.5 MB of the page; check at most 25 links; one check per IP every 20 seconds (Cache API key). Never send cookies. User-Agent: `dragomansjourney-checkup/1.0 (+https://dragomansjourney.com/checkup.html)`.
3. It fetches the page and reports: HTTPS yes or no; does it redirect from http to https; the mobile viewport tag; title and description present; page size; a clickable phone number (`tel:`); an email or contact form; and every link or button whose text or URL looks like booking, ordering, contact, donate, menu, schedule, appointment or reserve. Each of those gets a HEAD (falling back to GET) and is reported working, broken (4xx/5xx, timeout) or goes-nowhere (`#`, empty, `javascript:`).
4. New page `checkup.html` via `_build/tools/checkup.py` and `chrome.py`: one address box, a "Check it" button, then a report card. The worst finding first, in plain words ("Your Book Now button leads to an error page"). Each finding says what it costs ("people who tap it can't book") and how hard it is to fix ("a five-minute fix in your site builder"). End with "Want me to fix it?" linking to `call.html`. A line under the box: "This checks your public page the way a visitor's phone would. Nothing is stored."
5. Add `checkup.html` everywhere the other four tools are listed: `enhance.py` (both page lists), `build.py` (sitemap), the work page (a fifth tool card, `data-k="free"`, num "25 links", h2 "Website checkup"), and the T-02 tool links if T-02 is DONE.
6. Until the Worker is live, the page must say "Coming this week" and not show the box. Make that one constant at the top of the script: `CHECKUP_URL = ''`.
7. Tests: unit-test the safety checks and the link classifier with Node (no network). The page test checks the "coming this week" state.

**Gate for deploy:** Josef deploys it himself. Write exact steps in the receipt: Cloudflare dashboard, Workers and Pages, Create, name `dj-checkup`, paste the file, Deploy, copy the workers.dev address, paste it to Claude in chat. Then Claude sets `CHECKUP_URL`, rebuilds, and he says "push it".

**Receipt:**

---

## T-05 · Deepcuts card · GATED

**Gate:** Josef gives one number he can show (testers, games matched, quizzes taken) and the link people should open.

**Build:** a card on `work.html`, `data-k="own"`, tags "My own build", "App", "In testing", the number as `num`, h2 "Deepcuts", one or two sentences: indie games matched by how they actually play, not by what's trending. Rebuild, test (card counts change: update the test to match), look.

**Receipt:**

---

## T-06 · Name the nonprofit client on the site · GATED

**Gate:** the client's written yes to being named as a case study, with the wording they approved. Josef passes it to Claude in chat.

**Build:** set `CLIENT_LONG` and `CLIENT_SHORT` in `enhance.py` to the approved wording, rebuild, check every page that says "a Sonoma County children's nonprofit" now reads right, and update the Kids Kitchen card on `work.html` with what Josef says is public. Test, look.

**Receipt:**

---

## T-07 · Fix what Josef finds using the tools · GATED

**Gate:** Josef sends his list after trying the four tools on his phone (the recipe scaler at dinner counts).

**Build:** each item on his list, smallest change that fixes it, in the tool's `.py` source. Retest and look at both widths.

**Receipt:**
