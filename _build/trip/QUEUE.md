# Build queue: dragomansjourney.com

Josef fires one item at a time and checks the result later. Every item below is complete: no question should need asking. If one does, stop and write the question in the item's receipt instead of guessing.

## How to run an item (the same every time)

Start a Claude Code session on the web on repo `stephensjosef-cloud/dragomans-journey-site`, branch `main`, and paste the block in `_build/trip/RUN.md`. That's it. Claude Code picks the next READY item.

## House rules for every item

1. **Never push to `main`.** `main` is the live site (GitHub Pages). Each item commits to its own branch `trip/T-0N`, cut from the `trip/` branch on origin with the most recent commit date (or `main` if there is none), so the branches stack in a line and the newest one holds everything. Going live is Josef saying "push it" to Claude in chat.
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

## T-02 · Make the free tools findable · DONE

**Why:** right now the tools are only reachable from the work page.

**Build:**
1. Header nav on every page gets "Free tools" linking to `work.html#free`, placed before "Free 15-min call". Pipeline pages: in `enhance.py`. Tool pages: in `chrome.py`.
2. On `local.html`, add one short section just before the contact section: heading "Free tools for your pile", then a row of four small cards (title + one line + link), same cards as the work page. Mobile: one column.
3. On each tool page, under the tool and above the dark panel, a quiet line: "More free tools:" then links to the other three by name.
4. Tests: every page's nav has `work.html#free`; local.html has 4 tool links in the new section.

**Done when:** tested and looked at on both widths.

**Receipt:**
- **Branch:** `trip/T-02`, cut from `origin/trip/Q-02` (the only `trip/` branch on origin). Work commit `0a91b98`, receipt in the commit after it. Nothing pushed to `main`.
- **Nav (step 1):** "Free tools" → `work.html#free` on all 13 public pages. Where the header has "Free 15-min call" (`index`, `work`, the four tools) it sits right before it. The other headers have no call link, so it sits before the header's last link: `local` (inside its link group, after "The work"), `mainframe` (before "Request a briefing", outside the jump links that `intent.py` rewrites), `call`, `case-reels`, `start`, `briefing`, `comp3`. Same style as each header's own quiet links. Pipeline pages in `enhance.py` (`add_free_tools()`), tools in `tools/chrome.py`. `404.html` left as it is (logo only, noindex, same as T-01).
- **local.html (step 2):** "Free tools for your pile" section between drop-in hours and contact. The four cards (title, the work page's one-line description, the work page's link text) are read from the work page at build time, so they always match it. No new words. Four in a row at 1440, one column at 390.
- **Tool pages (step 3):** "More free tools:" then the other three by their work-page names (Reel shot list, Caption fitter, Busywork receipt, Recipe scaler), under the tool and above the dark panel.
- **Pipeline:** the unchanged pipeline rebuilt every root file byte for byte first. After the change, `cmp` shows only the 13 pages differ. The diffs are only the added links, the section and the line. `404.html`, `sitemap.xml`, `robots.txt`, `CNAME`, `favicon.svg`, images and `og/` are unchanged.
- **Tests:** `test_new.py` **210/210 passed** (50 new: every page's nav has exactly one "Free tools" link to `work.html#free`, before the call link where there is one; `work.html#free` opens on the free filter; the local section has the heading, sits right before contact, links the 4 tools, and each card matches the work page; one column at 390 and four across at 1440; each tool page links the other three by name above the dark panel; no sideways scroll at 390 on all 13 pages). Against the old build the new checks fail as they should (174/206; some checks only run when the link exists). Run on Windows with Playwright's own Chromium headless shell and real Google Fonts, as a copy, per house rule 3. `test_site.py` times out waiting for `networkidle` on `index.html` here too, the same as T-01 recorded on the untouched build.
- **Looked at:** all 13 headers at 390 and 1440, the new local section at both widths, and the tool line at both widths. Two fixes after looking: the local heading now wraps evenly ("Free tools / for your pile", not "pile" alone), and the tool line has more room between links for thumbs.
- **Worth knowing:** on phones the `local.html` header hides its text links (it already did, under 760px wide), so there the new section is the way in. On `work` and the tool pages at 390, the header now wraps "Free 15-min call" to its own row. Nothing overflows.
- **Josef, by hand:**
  1. Say "push it" to Claude in chat. That merges this into `main` and the site goes live.
- **Decided Nov 10:** Josef said keep "Free tools" in every header, the Mainframe page and `start.html` included.

---

## T-11 · Facts a machine can read · DONE

**Why:** people now ask AI tools who to hire nearby, and those tools read plain facts and structured data off a page. `local.html` and `mainframe.html` carry none. `index.html` has a small block (the site and Josef) that stays as it is.

**Build:**
1. Add a new last build step, `_build/final.py out`, run after `intent.py` (make it step 6b in `_build/README.md`, and say that `tools/og.py` is not affected by it). It reads the finished pages, so its words always match what each page says after the plain and intent passes. Do not put this in `enhance.py`: `intent.py` needs each of its edits to match an exact number of times, and a second copy of a page's words inside a script tag would break that.
2. `local.html` gets one `<script type="application/ld+json">` just before `</head>`, holding an `@graph` with:
   - a `ProfessionalService`: name "Dragoman's Journey", url `https://dragomansjourney.com/local.html`, email `hello@dragomansjourney.com`, founder (a `Person` named Josef Stephens), address with only `addressLocality` Santa Rosa, `addressRegion` CA, `addressCountry` US, `areaServed` "Sonoma County, California", `description` copied from the page's own meta description, and `sameAs` with the same GitHub link `index.html` uses.
   - `makesOffer`: one `Offer` for the Blueprint and one for each of the three things the page sells, each with its name and its price. Read every name and price from the finished page at build time. Never type a price into `final.py`. The price is the first dollar amount inside the card's `<strong>`. A "from" price uses `PriceSpecification` with `minPrice`; if the amount is followed by `/month`, add `unitText` "month". `priceCurrency` is USD. The rest of the card's price line goes in the Offer's `description`, word for word. If a price can't be found on the page, the build fails with a message that names it.
   - a `FAQPage`: every question and answer in the page's FAQ, read from the `data-faq` buttons and their `faq-a-N` paragraphs, as plain text.
3. `mainframe.html` gets one block the same way: a `Service` named "The Mainframe Route", `provider` Dragoman's Journey (with Josef Stephens as founder), `description` from the page's meta description, and, under `offers`, one `Offer` per step that prints a price. Names and prices are read from the page: the price is the first dollar amount in the step's last `<p>`, with the same rules as on `local.html`.
4. Never add a rating, a review, opening hours, a phone number, a street address, or any fact the page itself doesn't state.
5. Tests (add to `test_new.py`): each block parses as JSON; every price inside it appears in that page's text with the tags stripped (FAQ answers are hidden until tapped, so don't use rendered text); the FAQ count equals the number of `data-faq` buttons; `index.html`'s block is unchanged; no long dash.

**Done when:** tests pass, and a diff of each rebuilt page against the previous build shows only the added head tag on `local.html` and `mainframe.html`. Every other root file is byte for byte the same. Nothing visible changes, so one screenshot of each page at 390 and 1440 is enough to confirm that.

**Receipt:**
- **Branch:** `trip/T-11`, cut from `origin/trip/T-02` (the `trip/` branch with the newest commit). Work commit `121b33b`, receipt in the commit after it. Nothing pushed to `main`.
- **What's built:** `_build/final.py`, run as step 6b after `intent.py` (in `_build/README.md`, which also says `tools/og.py` is not affected). It reads the finished pages and adds one `<script type="application/ld+json">` just before `</head>`. It refuses to run twice on the same page.
- **local.html:** an `@graph` with a `ProfessionalService` (name, url, email, founder Josef Stephens, Santa Rosa / CA / US, area served, the meta description, and the GitHub link read from `index.html`'s own block) and a `FAQPage` with all 6 questions and answers as plain text. Four offers, all read from the page: The Blueprint (fixed $1,500, from the heading "The Blueprint · $1,500", since its card has no price in a `<strong>`; nothing else on that line, so no description), Reels from your phone videos (from $800/month, "three-month minimum"), Your own app (from $8,000, "then a yearly fee for updates and support"), Busywork, automated (from $3,000, "support from $750/month").
- **mainframe.html:** a `Service` "The Mainframe Route", provider Dragoman's Journey with Josef Stephens as founder, the meta description, the page's own url, and three offers: The Survey (from $8,000, "counts toward step II"), The Checker (from $15,000, "yours to keep and rerun"), The Move (from $5,000/month, "Ongoing checks"). The Audit Report prints no price ("Included with II and III"), so it has no offer.
- **One technical choice:** the two monthly prices use `UnitPriceSpecification`, which is the kind of `PriceSpecification` that schema.org allows `unitText` on. A plain `PriceSpecification` with `unitText` would be flagged by validators. The rest is as written: `minPrice`, `unitText` "month", `priceCurrency` USD.
- **No invented facts:** no rating, review, hours, phone, street address or postal code (a test checks each). A missing price stops the build and names it: tried in a copy with one price removed, it printed `local.html: no price found for "Your own app"` and wrote nothing.
- **Pipeline:** the unchanged pipeline rebuilt every root file byte for byte first. After the change, `cmp` shows only `local.html` and `mainframe.html` differ, and `git diff` on them is additions only (123 and 53 lines, the head tag). The other 32 files, `og/` included, are byte for byte the same.
- **Tests:** `test_new.py` **277/277 passed** (67 new: one block per page, just before `</head>`, parses as JSON; every price and every dollar amount in it is in the page's text with scripts and tags stripped, monthly ones with `/month`; offer names and descriptions word for word on the page; USD; FAQ count equals the 6 `data-faq` buttons and every Q and A is the page's own words; the business facts; one offer per priced Mainframe step; description equals the meta description; `index.html`'s block unchanged; no long dash; none of the forbidden facts). Against the old build, the new checks fail as they should (211/217: no block on either page). Run on Windows with Playwright's Chromium headless shell and real Google Fonts, as a copy with `exe = None`, per house rule 3.
- **Looked at:** `local.html` and `mainframe.html` at 390 and 1440. Nothing visible changed; no sideways scroll at 390 (tested on all 13 pages).
- **Josef, by hand:**
  1. Say "push it" to Claude in chat. That merges this into `main` and the site goes live.
  2. Optional, after it's live: open https://validator.schema.org/, paste `https://dragomansjourney.com/local.html`, press Run test, and check it shows no errors. Do the same for `mainframe.html`.

---

## T-12 · Count visits · DONE (build), GATED (token)

**Why:** the site has no visit counter. Nobody can tell whether a post or a text sent anyone to it, or which free tool gets used.

**Build:**
1. Read Cloudflare's current docs first, not memory: start at `https://developers.cloudflare.com/web-analytics/get-started/`, its "Data origin and collection" page, `https://developers.cloudflare.com/speed/observatory/rum-beacon/` and `https://www.cloudflare.com/web-analytics/` (the last two are where cookies are covered). In the receipt, write what the beacon sends and whether it sets cookies, with the page each fact came from.
2. In `_build/final.py` add `CF_BEACON_TOKEN = ""` at the top. While it is empty, nothing is added anywhere. When it is set, add Cloudflare's Web Analytics snippet, in the exact form the docs give, just before `</body>` on every `.html` page in the output folder except `comp3.html` (see step 3). The visit counter sends nothing a visitor types, so it is allowed under house rule 6.
3. Keep the tools' promise true. The tool pages say "Nothing you type here leaves this page." Cloudflare's docs don't say whether the beacon sends the part of an address after the `#`, so treat it as sent. Three pages carry visitor text there. `receipt.html` hands text to `start.html` (`never=`), and the quiz on `local.html` hands the typed business name to `start.html` (`org=`): make `start.html` read its hash and then clear it from the address bar with `history.replaceState`, before the beacon script runs. Update the existing check in `test_new.py` that expects `start.html#` in the address, and add a test that the hash is gone after load and the form is still prefilled. `comp3.html` keeps pasted bytes in its own hash on purpose (that is its share link), so it gets no beacon at all.
4. Words, only when the token is set and only if the docs confirm no cookies: at the end of the `local.html` FAQ answer to "What do you do with our data?", add exactly: "This site counts page visits with Cloudflare Web Analytics, which uses no cookies." Make that edit in `final.py` before the T-11 block is built, so the `FAQPage` data carries the same sentence. If the docs don't confirm it, add no sentence and write the question in the receipt.
5. Tests: with the token empty, no page has the beacon or the new sentence. In a temp copy with a made-up token, every page except `comp3.html` has exactly one beacon, `comp3.html` has none, and `local.html` has the sentence once.

**Gate for the token:** Josef gets it from the Cloudflare dashboard (Web Analytics, add the site `dragomansjourney.com`, then copy the JS snippet) and pastes the snippet to Claude in chat. Write the exact numbered steps in the receipt from the docs as they read today. The token is public by design (it sits in every page's source), so it can live in this repository. Then Claude sets `CF_BEACON_TOKEN`, rebuilds, and Josef says "push it".

**Receipt:**
- **Branch:** `trip/T-12`, cut from `origin/trip/T-11` (the `trip/` branch with the newest commit). Work and receipt in one commit. Nothing pushed to `main`. Build part only; the token is still gated.
- **What the docs say (read Nov 11, 2026):**
  - *What the beacon sends:* `pageloadId`, `referrer`, `startTime`, `memory`, `timings`, `timingV2`, `firstPaint`, `firstContentfulPaint`, `FCP`, `LCP`, `CLS`, `TTFB`, `INP` and `landingPath` (the landing page URL). It's performance data from the browser's own timing APIs. The IP address arrives with the request; Cloudflare says it discards it at the nearest data center and does not store it in its databases or logs. Source: `developers.cloudflare.com/speed/observatory/rum-beacon/` (field table and "Data processing").
  - *Where it goes:* `cloudflareinsights.com/cdn-cgi/rum` for a manual snippet, or the site's own `/cdn-cgi/rum` when Cloudflare injects it. It sends only timing metrics and doesn't track people across sites. Source: `developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/` and `developers.cloudflare.com/web-analytics/faq/`.
  - *Query strings:* "do not log query strings". Source: the FAQ page. *The part after `#`:* none of the four pages mentions it, and `landingPath` is a full URL, so it's treated as sent (step 3).
  - *Cookies:* none. The beacon "does not store any data in the browser or access any storage data, such as cookies, localStorage, sessionStorage" (`developers.cloudflare.com/speed/observatory/rum-beacon/`), and Web Analytics "does not use any client-side state, such as cookies or localStorage" (`www.cloudflare.com/web-analytics/`). That confirms it, so step 4's sentence is built (it shows only once the token is set).
  - *Snippet form:* the FAQ page gives `<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token": "$SITE_TOKEN"}'></script>`, and says a manual embed must add `type="module"` itself. `final.py` uses exactly that, with the docs' line breaks.
- **What's built:**
  - `final.py`: `CF_BEACON_TOKEN = ""` at the top. Empty means nothing is added: a rebuild matches the old build byte for byte except `start.html`. When it's set, the FAQ sentence goes in first, then the T-11 block is built (so the `FAQPage` data carries the sentence too), then the beacon goes just before `</body>` on every `.html` in the output (`404.html` included) except `comp3.html`. If the token isn't plain letters and digits (for example the whole snippet pasted in), if a page already has a beacon, or if the FAQ answer can't be found, the build stops and says why.
  - `start.html`: after the form reads its `#`, it clears the `#` with `history.replaceState`. The address bar then shows only `start.html`, and the form stays filled. The beacon is a module script, so it runs after this. This covers the quiz on `local.html` (`org=`) and the receipt (`never=`).
  - `_build/README.md`: step 6b and the settings line describe the token.
- **Pipeline:** the unchanged pipeline rebuilt every root file byte for byte first. After the change, `cmp` shows only `start.html` differs (3 added lines in its script). The other 33 files, `og/` included, are unchanged. A temp copy built with a made-up token adds exactly one beacon to each of 13 pages, none to `comp3.html`, and the sentence once in the `local.html` FAQ.
- **Tests:** `test_new.py` **341/341 passed** (64 new: no beacon and no sentence on any of the 14 pages while the token is empty; a full rebuild in a temp copy with a made-up token gives every page except `comp3.html` exactly one beacon, in the docs' form, just before `</body>`; `comp3.html` gets none; the sentence appears once on the page, ends the data answer, and is also in the `FAQPage` data; no other page has it; the quiz and the receipt hand-offs land on `start.html` with no `#`, and the form keeps the business name, the receipt text and the pick). The existing check that expected `start.html#` in the address now expects no `#`. Against the old build, the two hand-off checks fail as they should (339/341). Run on Windows as a copy with `exe = None` and `p.chromium.launch()`, with Playwright 1.65 in a scratch virtual environment, per house rule 3.
- **Looked at:** `start.html` arriving from the receipt link, at 390 and 1440: address cleared, receipt text and pick still in the form, no sideways scroll. The `local.html` FAQ answer with the sentence, from the made-up-token build, at 390 and 1440: it reads as the answer's last sentence and fits.
- **Josef, by hand (the token gate):**
  1. Open the Cloudflare dashboard and go to **Web Analytics**.
  2. Select **Add a site**.
  3. If a box says **Set up hostname**, type `dragomansjourney.com`, select the message box that appears to choose it, and select **Done**. If you get a drop-down of hostnames instead (Cloudflare proxies the site), pick `dragomansjourney.com` and select **Done**. Then open **Manage site** and choose **Enable with JS Snippet installation**, so Cloudflare doesn't add a second beacon of its own.
  4. In **Manage site**, copy the JS snippet.
  5. Paste the snippet to Claude in chat. Claude puts the token into `CF_BEACON_TOKEN` in `_build/final.py`, rebuilds, tests, and commits.
  6. Say "push it" to Claude in chat. That merges this into `main` and the site goes live with the counter.
  7. A day later, open **Web Analytics** in Cloudflare and check that visits show up for `dragomansjourney.com`.
- **Worth knowing:** until the token is set, the only live change is that `start.html` tidies its own address. It's safe to push on its own.

---

## T-14 · One new line on the Mainframe page · GATED (skipped by Josef, Nov 11)

**Why:** in October 2026 OpenAI reported a model passing 97.9% of its own COBOL migration test, and did not publish the test cases. That is this page's argument with a fresh number: translating is no longer the hard part, and a score nobody can inspect is not proof about your programs.

**Build:**
1. Check the source before writing a word. Open OpenAI's own post, "Advancing coding in low-resource programming languages" (`https://openai.com/index/low-resource-programming-languages/`). Confirm three things there: the 97.9% figure and what it measures; that the COBOL test cases are not published; and OpenAI's own statement that production use still needs expert review and testing. A news article is not good enough. If the post can't be opened from this session, set this item's status to BLOCKED (question) and write in the receipt: "Josef: paste the text of OpenAI's post to Claude in chat." If any of the three reads differently, do the same and write what you found.
2. In the first section of `mainframe.html`, right after the sentence "Turning COBOL into Java stopped being the hard part.", add: "In October 2026, OpenAI reported one of its models passing 97.9% of its own COBOL migration test.<sup style="font-size: 11px; color: #A93F17">3</sup> The test cases aren't public, and OpenAI says real use still needs expert review." Change the wording only as far as the source requires, and say in the receipt what you changed and why.
3. Make the edit in `_build/final.py`, after `intent.py` has run. Do not touch `intent.py`: it renumbers the page's notes with exact matches, and a note added earlier in the pipeline breaks it. The finished page has six notes (sup numbers 1, 2, 3, 3, 4, 5, 6 in reading order) and a six-item Notes list. The new note is number 3. Renumber the existing sups in this order so nothing collides: 6 to 7, 5 to 6, 4 to 5, then both 3s to 4. Add the new source as the third item in the Notes list, in the same format as the others, linking OpenAI's post with its date. If T-11 is not built yet, create `final.py` as T-11 step 1 describes.
4. The stats band keeps its three numbers.
5. Tests: the sentence appears once; the sup numbers in reading order are 1, 2, 3, 4, 4, 5, 6, 7; the Notes list has seven items and the third links to `openai.com`; no long dash. Look at the section and the Notes list at 390 and 1440.

**Receipt:**
- Skipped on Josef's word, Nov 11. Nothing was built.

---

## T-08 · The Studio page and the public build log · DONE

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
- **Branch:** `trip/T-08`, cut from `origin/trip/T-12` (the `trip/` branch with the newest commit). Work and receipt in one commit, with T-14 marked skipped. Nothing pushed to `main`.
- **What's built:**
  - `_build/tools/studio.py` writes `_build/studio.html` from `studio.json` and `shipped.json`, with the header and footer from `chrome.py`. `chrome.py` now leaves out the "More free tools" line and the dark panel on a page that has no panel words, so the Studio page carries nothing that isn't in the JSON. The four tool pages change only by the new nav link.
  - Top to bottom: the hero from `studio.json`; the numbers strip ("17 things shipped since Oct 6", "13 in the last 30 days", "4 projects"), counted at build time; "Shipped lately" with the 8 newest lines, each with its date, a small project label and the line, and a "See all 17" button that shows the rest in place and then goes away; then the six open products as cards in the JSON's order (name, status pill, kind, what, proof in bold, image, link and/or join button). Two columns at 1440, one at 390, Bird League across the full width with its image.
  - Join buttons open `mailto:hello@dragomansjourney.com?subject=List: <product name>` with the JSON's button words. Counts show only at 10 or more ("41 people on the list"); all are 0 today, so none shows.
  - Header "Studio" link before "Free tools" on all 14 public pages (pipeline pages in `enhance.py`, tool pages and the Studio page in `chrome.py`). `404.html` left as it is, as in T-01 and T-02.
  - Home page: a slim "Shipped lately" band between the hero and the two routes, with the newest 3 lines and "See everything I'm building →" to `studio.html`, built in `enhance.py` from `shipped.json` by the same rules as the Studio page.
  - `studio.html` is in `enhance.py` (both page lists), the sitemap (`build.py`) and `tools/og.py`, which drew its share card ("Built in the open"). The other 13 cards weren't redrawn.
  - `enhance.py` stops the build if `studio.json` or `shipped.json` changed since `studio.py` last ran, so the page can't go out stale.
- **Choices the item left open (all mechanical, no new words):**
  1. The album is gated, so its card doesn't show, and neither does its log line ("All 15 songs on the album are written..."). The counts leave it out too (17 lines, 4 projects, not 18 and 5). When the gate clears, both appear on the next build. The hero's own words still mention an album, as `studio.json` has them.
  2. Project labels are the product's name from `studio.json`. Project `site` has no product, so its label is the site's own address, `dragomansjourney.com`, which its lines already use.
  3. Lines older than 120 days drop off before anything is counted, so the strip and the "See all" number always agree with the list.
  4. Page title "The studio" (the first part of the kicker); meta description is the lede.
  5. No heading over the product cards, since the JSON has none.
- **Fix, Nov 11 (approved by Josef, done on `trip/T-09`):** the hero names the album only while the album card shows; while it's gated the hero and meta description read "Apps, free tools and shirts, made with AI and a lot of real-phone testing." (`lede_album_gated` in `studio.json`, chosen by `studio.py`; share card words unchanged; both states tested).
- **How a new log line gets added:** Claude adds one line at the top of `shipped.json` (`date`, `project`, `line`: plain words for a stranger, no client names), runs `cd _build/tools && python3 studio.py ..`, rebuilds, tests and commits. Josef never edits it. A new project needs a product in `studio.json` with the same `id`, or the build stops and names it. The counts are as of the day `studio.py` runs, so Claude reruns it before each push. Written in `_build/README.md` step 4d.
- **Pipeline:** the unchanged pipeline rebuilt every root file byte for byte first. After the change, `cmp` shows only the 14 public pages and `sitemap.xml` differ, plus the new `studio.html` and `og/studio.png`. Every page's diff is the added nav link; `index.html` also has the band, `sitemap.xml` one line. `404.html`, `robots.txt`, `CNAME`, `favicon.svg`, images and the other 13 cards are unchanged. `plain.py`, `intent.py` and `final.py` leave `studio.html` exactly as `studio.py` wrote it.
- **Tests:** `test_new.py` **425/425 passed** (84 new: the strip matches `shipped.json` as of the page's build date; all 17 lines, dates and labels in order, 8 showing, "See all 17" reveals the rest in place; every open product renders in order with its JSON words, the gated album doesn't, and nor do its log lines; proof in bold, image and alt, links; each join button mails "List: <name>"; the count rule at 41 and 9; two columns at 1440 with Bird League full width, one column at 390; the home band sits between hero and routes and shows the newest 3; "Studio" before "Free tools" in every header; sitemap; share card; no sideways scroll; a temp copy proves `enhance.py` stops on a stale `studio.html`; the T-12 beacon checks now cover `studio.html` too). Against the old build the run stops at the first `studio.html` fetch (404), as it should. Run on Windows as a copy with `exe = None` and `p.chromium.launch()`, per house rule 3. `test_site.py` not run.
- **Looked at:** `studio.html` at 390 and 1440 (closed and open log), the home band at both widths, every changed header at both widths, and the share card. Two fixes after looking: the Bird League button now sits under its text instead of at the bottom of the card, and the numbers strip stays three across on phones. Worth knowing: on `work.html` at 390 the header now wraps "Free tools" and the call button to a second row; nothing overflows.
- **Josef, by hand:**
  1. Open `studio.html` from this branch (or the screenshots in chat) and read the labels and counts.
  2. Say "push it" to Claude in chat. That merges this into `main` and the site goes live.

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

**Added Nov 9: the checkup also answers "Can AI find you?"** Build this as part of T-04, in the same Worker and the same page.

8. The Worker also fetches `/robots.txt` on the same host, under the same safety rules, and adds to its report:
   a. Whether the site turns AI readers away. Take the current crawler names from OpenAI's, Anthropic's, Perplexity's and Google's own docs, not from memory, and list in the receipt the names you used and where each came from. Those companies run two kinds: crawlers that collect training data, and crawlers that fetch pages to answer a question or a search. Report the two kinds separately, and say a site "turns AI readers away" only when it blocks the answer or search kind. Blocking only the training kind is a choice, not a fault: say so in one plain line. Also report a `User-agent: *` with `Disallow: /`, a `noindex` meta tag, and an `X-Robots-Tag` header whose value contains `noindex` or `none`.
   b. Structured data: whether the page has a JSON-LD block that describes a business or organization, its `@type`, and which of name, address, telephone, opening hours and url it carries.
   c. Facts in the raw page text, with scripts and styles stripped and JavaScript not run: a phone number, opening hours (day names near times), and a street address (an `<address>` tag, a structured-data address, or a US street pattern). Say "found" or "I couldn't find", never "missing", because a pattern can miss.
   d. How much readable text the raw page holds. Under 600 characters, on a page that answered 200 and was not cut off at the 1.5 MB limit, say: "Your page holds almost no text a machine can read without running scripts or reading images."
   e. If the phone number in the structured data and the one in the page text differ (compare digits only), say so.
9. On `checkup.html`, a second report card under the first, headed "Can AI find you?". Its first line, exactly: "This doesn't tell you what ChatGPT says about you. It checks whether a machine can read the facts it would need." Findings use the same shape as the first card: the worst first, what it costs, how hard it is to fix. It ends with a small card, "The facts a machine reads off your page", listing the name, phone, address and hours as found, and the line: "Check these against your Google Business Profile, letter for letter. I can't see your listing from here."
10. A number, only if you can prove it: if you can open BrightLocal's own 2026 Local Consumer Review Survey page and it states the share of people who use AI tools to find local businesses, add one line above the second card with that number, its year, and a tap-to-see-source link, in the source's own meaning. If you can't open it or the meaning is unclear, add no number.
11. Unit tests with small made-up HTML and robots.txt strings for each of 8a to 8e (no network).
12. If T-11 is DONE on the branch you cut from, also run `local.html` from `out/` through the 8b check in a test: it must find the business block.

**Gate for deploy:** Josef deploys it himself. Write exact steps in the receipt: Cloudflare dashboard, Workers and Pages, Create, name `dj-checkup`, paste the file, Deploy, copy the workers.dev address, paste it to Claude in chat. Then Claude sets `CHECKUP_URL`, rebuilds, and he says "push it".

**Receipt:**

---

## T-15 · Host on Cloudflare, with a preview link per branch · READY (build), GATED (switch)

**Why:** GitHub Pages only serves this repository while it is public, and on Nov 9 it left a publish stuck in its queue for five hours. Cloudflare already holds the domain and the intake Worker. Hosting there lets the repository go private, and gives every `trip/` branch its own preview address that Josef can open on his phone before he says "push it".

**Build (this changes nothing live; GitHub Pages keeps serving the site until the switch):**
1. Read Cloudflare's current docs first, not memory. Settings and commands changed during 2026. Start at `https://developers.cloudflare.com/workers/static-assets/` (and its HTML handling and custom 404 pages), `https://developers.cloudflare.com/workers/ci-cd/builds/` (and its configuration and build branches pages), and the Workers previews docs. List in the receipt each page you relied on.
2. `_build/publish.sh` (plain `sh`): makes a folder `dist/` that holds exactly the public site, which is every git-tracked file outside `_build/` except `CNAME`, `wrangler.jsonc`, and any file or folder whose name starts with a dot or an underscore. It also writes one extra file, `dist/_redirects`, holding the single line `/ /index.html 200` (step 3 says why). It fails loudly if `dist/` would be empty or if anything from `_build/` lands in it.
3. `wrangler.jsonc` at the repository root: a Worker that serves static files only (no script), named `dragomans-journey`, serving `./dist`, with `html_handling` set to `none`, `not_found_handling` set to `404-page`, and the `previews` setting the docs describe. Every address that works today must keep working unchanged: `/local.html` must answer 200 at that exact address and must not redirect to `/local` (the default setting redirects it). With `none`, `/` stops finding `index.html`, which is what the `_redirects` line in step 2 fixes. If the docs or the local test in step 5 disagree with any of this, stop and write the options in the receipt.
4. Create `.gitignore` (there isn't one) with `dist/`, `.wrangler/` and `node_modules/`.
5. Prove it locally. Run `publish.sh` and compare the file list in `dist/` with the rule in step 2. Serve `dist/` with wrangler's local server and check: `/` and `/local.html` answer 200 with no redirect; `/og/index.png` is a PNG; `/nope` answers 404 with the body of `404.html`; `/_build/README.md`, `/wrangler.jsonc`, `/CNAME` and `/_redirects` answer 404. Then run `test_new.py` against that server.
6. GitHub Pages must not notice: every existing root file stays byte for byte the same. `wrangler.jsonc` will be reachable on the old host until the switch, so it must hold no secret (it won't: a name and a folder).
7. Add a short "Hosting" section to `_build/README.md`.

**Gate for the switch:** Josef does it at his desk, with Claude in chat, in one sitting. In the receipt, write exact numbered steps, taken from the docs as they read today, for each of these:
   a. Creating the Worker from this GitHub repository: the Worker's name must equal the `name` in `wrangler.jsonc`, the production branch is `main`, the build command is `sh _build/publish.sh`.
   b. Turning on preview builds for other branches, where a branch's preview address shows up, and what the address looks like for a branch named like `trip/T-11`. Say whether preview addresses are public, and whether connecting a private GitHub repository works (if the docs don't say, write that down as a thing to confirm at the desk before step f).
   c. Checking the Worker's own address on a phone before touching the domain.
   d. The switch. First write down every current web record for `dragomansjourney.com` and `www` (that list is the way back). Remove only those web records. Never touch the MX and TXT records: the site's email addresses run on them. Then add both names to the Worker as custom domains, with `www` sending visitors on to `dragomansjourney.com` as it does today (write how).
   e. Checking the live site, the forms, and one share card. Also say whether the Worker's own `workers.dev` address can be switched off after the move without losing branch previews, so a second copy of the site isn't left open to search engines.
   f. On GitHub: unpublish Pages, then make the repository private.
   g. Web Analytics after the move: make sure each page carries one beacon, not two (Cloudflare can add its own on proxied sites).
   h. The way back if anything looks wrong: remove the custom domains and put the written-down records back.
   Also say plainly in the receipt: forms on a preview address or on the Worker's own `workers.dev` address will not send, because the intake Worker only accepts the real site's address. That is expected. Do not add preview addresses or wildcards to the intake Worker.

**Receipt:**

---

## T-13 · The first drop-in date · GATED

**Gate:** Josef gives Claude the date, the hours and the place.

**Build:**
1. `plain.py` rewrites the two no-date lines of the drop-in card ("The list hears first" and "Twenty minutes, your pile...") and fails the build if they're absent, which they are once a date is set. Move those two rewrites out of `plain.py` and into the no-date branch in `enhance.py` as its final wording, so the no-date page comes out word for word as it is live today. Prove that first: with no date set, every rebuilt root file is byte for byte unchanged.
2. Set `DROPIN_DATE` and `DROPIN_PLACE` at the top of `enhance.py` in the format its comments show. Keep the button as "Put me on the list →" in both states: nothing on the site holds a seat, and the message after signing up talks about the list.
3. Add `DROPIN_ENDS` (an ISO date, the day after the drop-in). A build on or after that day, in America/Los_Angeles, uses the no-date wording. A static page can't change itself, so the receipt must tell Josef: "The day after the drop-in, ask Claude to rebuild and push."
4. Rerun `tools/og.py` only if a headline or description changed. Tests: the dated state, and the fallback with the date moved into the past in a temp copy. Look at the drop-in section at 390 and 1440.

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
