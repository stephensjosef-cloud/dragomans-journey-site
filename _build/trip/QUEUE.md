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

## T-09 · Product pages that make people want in · DONE

**Why:** a card says what a thing is. A page per product shows it's real and moving, and gives one obvious way in.

**Build:**
1. `studio.py` also writes one page per non-gated product that has a join list: `studio-birdleague.html`, `studio-deepcuts.html` (and later `studio-album.html` once its gate clears).
2. Each page: the product's name big; status pill; "what"; the proof line; the image if any; "Shipped lately" filtered to that project (all its log lines, newest first, with dates); and one join box: email field + the list's button, with one line under it: "One email when it's out. No newsletter." Until T-10 is live, the box is a mailto button with the same subject as T-08.
3. Each studio card links to its page ("See it move →").
4. Share cards for each new page through `og.py`.
5. Tests: one page per eligible product; each page's log matches `shipped.json` for that project.

**Receipt:**
- **Branch:** `trip/T-09`, cut from `origin/trip/T-08` (the `trip/` branch with the newest commit). First commit `fcc4e97` is the approved Studio hero fix (noted in T-08's receipt); the T-09 work and this receipt are in the commit after it. Nothing pushed to `main`.
- **What's built:**
  - `tools/studio.py` also writes `studio-birdleague.html` and `studio-deepcuts.html`: one per product with no gate and a join list. Top to bottom: "The studio · <kind>" (with "The studio" linking back), the product's name big, its status pill, "what"; then the proof line in bold and the image when the JSON has them (Bird League: both; Deepcuts: neither); then "Shipped lately" with every line of that project, newest first, with dates; then one join box: the list's own button (mailto, subject "List: <name>", same as T-08) and under it "One email when it's out. No newsletter." The count rule is the same as on the cards (10 or more).
  - Each of those two Studio cards now has "See it move →" to its page, before the join button. The other four cards have no page and no link.
  - The page list comes from one place, `product_pages()` in `studio.py`; `enhance.py` (copy, freshness stamp, share-card tags, dash check), `build.py` (sitemap) and `tools/og.py` (cards) all read it. When the album's gate clears, `studio-album.html` appears on the next build with no other code change. A page whose product loses its list or gets a gate is deleted by `studio.py`.
  - `tools/chrome.py` has an empty slot under the `<h1>` for the status pill; the four tool pages are byte for byte unchanged.
  - Share cards drawn by `og.py`: "BIRD LEAGUE / Fantasy sports for birders." and "DEEPCUTS / Indie games matched by how they actually play, not by what's trending." The other 14 cards weren't redrawn.
  - `_build/README.md` step 4d says how the pages come and go.
- **Choices the item left open (mechanical, no new words):**
  1. "All its log lines" uses the same rules as the Studio page: lines older than 120 days drop off. Today that drops nothing (6 Bird League lines, 4 Deepcuts lines).
  2. No project label on each line, since the whole page is one project.
  3. Kicker is the Studio kicker's first part plus the product's kind, both from `studio.json`. Page title is the product name; meta description is "what".
  4. Until T-10 there's no email field, only the button, as step 2 says.
- **Pipeline:** the unchanged pipeline rebuilt every root file byte for byte first. After the change, `cmp` shows only `studio.html` (the two card links) and `sitemap.xml` (two lines) differ, plus the new two pages and two cards. `plain.py`, `intent.py` and `final.py` leave the new pages exactly as `studio.py` wrote them.
- **Tests:** `test_new.py` **511/511 passed**: 9 for the hero fix (both album states, built from `studio.py` in a temp copy) and 77 for T-09 (one page per eligible product and none for the others or the gated album; sitemap; card links; name, pill under it, what, kicker link, proof, image; each page's log matches `shipped.json` for its project, newest first, with dates, all showing, no other project's lines; one join box with the right subject, button words and line, after the log; count rule; no sideways scroll at 390 and 1440; the product pages also run through the share-card, nav, Studio-link, beacon and no-sideways-scroll checks every page gets; a product gets a page once its gate clears). Run on Windows as a copy with `exe = None` and `p.chromium.launch()`, Playwright 1.65, per house rule 3. `test_site.py` not run.
- **Looked at:** both product pages at 390 and 1440, the Studio cards at both widths, the Studio hero at both widths, and both new share cards. Two fixes after looking: the log dates now sit in one even column on phones, and at 1440 the proof line sits at the top beside the Bird League image and the join box is narrower.
- **Word fixes, Nov 11 (approved by Josef, done on `trip/T-10`):** the Nov 2 log line now says "went up to TestFlight, Apple's testing app" (Studio and Deepcuts pages), and the line under each join box is a per-list `line` in `studio.json`, so Deepcuts reads "One email when a tester spot opens. No newsletter." and Bird League keeps its line; no share card changed, 511/511 tests pass.
- **Josef, by hand:**
  1. Open `studio-birdleague.html` and `studio-deepcuts.html` from this branch (or the screenshots in chat) and read them.
  2. Say "push it" to Claude in chat. That merges this into `main` and the site goes live.

---

## T-10 · Real join lists · DONE (build), GATED (deploy)

**Why:** the lists have to work without Josef touching them.

**Build:**
1. Add a `list` form to `_build/worker/intake.js` (keep everything else byte-for-byte): fields `email` (required), `name` (optional), `list` (required, one of `birdleague`, `deepcuts`, `album`, `spots-feb`). Subject `List: <list> · <email>`. Same honeypot and 2.5-second minimum as the other forms. Write the deployable single file next to it as `intake.deployed.js` (same format as now).
2. The join boxes from T-08 and T-09 post to the Worker the same way `start.html` does (copy its fetch, honeypot and timing code), show "You're on the list" on success, and fall back to the mailto if the send fails.
3. Counting needs no database: Claude in chat counts the `List:` emails in Josef's Gmail when it next updates the site, writes the numbers into `studio.json`, and rebuilds. Note that in the receipt.
4. Tests: the form posts the right fields (intercept the request in Playwright, don't send); success and failure states both render.

**Gate for deploy:** Josef pastes the new `intake.deployed.js` over the old one in the Cloudflare dashboard (Workers and Pages, `dj-intake`, Edit code, paste, Deploy). Exact numbered steps go in the receipt. Until then the mailto fallback works, so nothing is broken in the meantime.

**Receipt:**
- **Branch:** `trip/T-10`, cut from `origin/trip/T-09` (the `trip/` branch with the newest commit). First commit `79f9d59` is the two word fixes approved Nov 11 (noted in T-09's receipt); the T-10 work and this receipt are in the commit after it. Nothing pushed to `main`. Build part only; the Worker deploy is still gated.
- **The Worker (step 1):** `worker/intake.js` gets a `list` form: `email` and `list` required, `name` optional, `list` must be one of `birdleague`, `deepcuts`, `album`, `spots-feb` (anything else gets a 400). Subject `List: <list> · <email>`, for example "List: deepcuts · fan@example.com". Same origins, honeypot and 2.5-second minimum as the other forms; the email body lists List, Email and Name, and Reply-To is the visitor. The rest of the file is unchanged except the subject line, which now picks the list subject for this one form. `worker/intake.deployed.js` has the same three changes in its one-line format; everything else in it is byte for byte the same.
- **Worker check:** new `worker/test_intake.mjs` (`node test_intake.mjs`, no network, no Cloudflare) runs both files side by side with a stand-in email binding: 34/34 pass. Both files give the same answer and the same email for every case, the four old forms (blueprint, briefing, call, drop-in) send exactly what they sent before, and against the old Worker the list cases fail as they should (20/34).
- **The join boxes (step 2):** every join button on `studio.html` (Bird League and Deepcuts cards) and on both product pages is now a small form, written by `tools/studio.py`: an "Email" field (the word `start.html` uses), the list's own button, and the same off-screen "Website" honeypot as `start.html`. Pressing the button posts `{form: "list", fields: {email, list}, website, ms}` to the same Worker address as `start.html`, with its fetch and timing code. When the Worker says ok, the field and button give way to "You're on the list". When it says no or can't be reached, the box opens the same mailto as before (`List: <product name>`) and stays ready to try again. That mailto is also the form's own action, so it works with scripts off. An empty or broken email is stopped by the browser's own check, so no new words. Today the live Worker doesn't know the `list` form, so every press ends in the mailto, as before, until the deploy below.
- **Choices the item left open (no new words):** the boxes ask for email only, no name, as T-09 step 2 describes the box ("email field + the list's button"); the Worker still takes a name if a later form sends one. The button shows "Sending…" while it waits, as on `start.html`.
- **Counting (step 3):** no database. When Claude next updates the site, it counts the `List:` emails in Josef's Gmail and writes the numbers into each list's `count` in `studio.json`, then rebuilds (counts show at 10 or more). Count both kinds of subject: "List: <list> · <email>" from the Worker, and "List: <product name>" from the mailto (before the deploy, or when a send fails). Count each email address once per list.
- **Pipeline:** the pipeline rebuilt every root file byte for byte first (after the word fixes). After the change, `cmp` shows only `studio.html`, `studio-birdleague.html` and `studio-deepcuts.html` differ: the join box markup, its CSS and the join script. Every other root file, `og/` included, is unchanged. No headline or description changed, so no share card was redrawn.
- **Tests:** `test_new.py` **568/568 passed** (57 new, plus the T-08 and T-09 join checks rewritten to describe the form instead of the old link). New: `node test_intake.mjs` passes from inside the run; the Worker's four lists are the item's four and every Studio list is one of them; the join boxes post to the same Worker address as `start.html`; on the Studio cards and both product pages, with the Worker intercepted in Playwright (nothing sent): the field is required, type email, labeled; the honeypot is off screen; an empty email sends nothing; a real one posts `form=list` with the trimmed email, the right list, an empty honeypot and at least 2.5 seconds; success says "You're on the list" in a status line, hides the field and button and opens no mailto; an error answer and a dropped connection each open the box's mailto once and leave the box ready; no sideways scroll at 390 and 1440. Against the pages from before this item, the run stops at the first join box (there's no form to press), as it should. Run on Windows as a copy with `exe = None` and `p.chromium.launch()`, Playwright 1.65, per house rule 3. `test_site.py` not run.
- **Looked at:** both product pages at 390 and 1440, the Studio cards at 390 and 1440, the success state at both widths, and the failure state at 390. Nothing overflows.
- **Josef, by hand (the deploy gate):**
  1. On this branch, open `_build/worker/intake.deployed.js` and copy all of it (it's one line).
  2. Open the Cloudflare dashboard and go to **Workers & Pages**.
  3. Select the Worker **dj-intake**.
  4. Select **Edit code**.
  5. Select all the code in the editor, delete it, and paste the copied file in its place.
  6. Select **Deploy**, and confirm if it asks.
  7. Say "push it" to Claude in chat. That merges this into `main` and the site goes live with the new join boxes. (The order doesn't matter: before the deploy the boxes fall back to the mailto, as today.)
  8. Once both are done, open https://dragomansjourney.com/studio-deepcuts.html on your phone, type your own email, and press **Join the beta**. It should say "You're on the list", and Gmail should get "List: deepcuts · <your email>". If it opened your mail app instead, the deploy didn't take: tell Claude.

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

## T-04 · Website checkup tool · DONE (build), GATED (deploy)

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
- **Branch:** `trip/T-04`, cut from `origin/trip/T-10` (the `trip/` branch with the newest commit). Work and receipt in one commit. Nothing pushed to `main`. Build part only; the Worker deploy is still gated.
- **The Worker (steps 1 to 3, 8):** new `worker/checkup.js`, separate from `intake.js` (which is untouched). `GET /?url=<address>` answers JSON facts; the page turns them into words. CORS for the same origins as intake, and it refuses any other origin (403), so other sites can't use it as a free fetcher. Safety: `http` and `https` only, ports 80 and 443 only, no name or password in the address; refuses IP-address hosts (any form, IPv4 or IPv6), `localhost`, `.local`, `.internal` (also `.localhost`, `.home.arpa`, `.lan` and one-word names). A Worker can't see DNS, so it asks Cloudflare's own resolver (`cloudflare-dns.com`) where a name points and refuses it if any address is in a private range; this runs again on every redirect hop, at most 3 hops. 8 seconds per request, covering the answer and reading it; at most 1.5 MB of the page; at most 25 links checked, each address once; one check per IP every 20 seconds (Cache API, with a per-instance backup). Never sends cookies; User-Agent exactly as the item gives it. It reports HTTPS, whether `http://` sends people on to `https://`, the phone viewport tag, title, description, page size, a `tel:` link, an email or contact form, and every link or button whose words or address look like booking, ordering, contact, donate, menu, schedule, appointment or reserve: `#`, empty and `javascript:` are "goes nowhere"; the rest get a HEAD, then a GET if the server won't answer HEAD, and are "working" or "broken" (4xx/5xx, timeout).
- **AI crawler names (step 8a), read Nov 12, 2026:**
  - OpenAI (`developers.openai.com/api/docs/bots`): `OAI-SearchBot` (ChatGPT search) and `ChatGPT-User` (a person asked ChatGPT to look) are the answer kind; `GPTBot` (training) is the training kind. `OAI-AdsBot` only checks ad landing pages, so it's left out.
  - Anthropic (`support.claude.com`, "Does Anthropic crawl data from the web..."): `Claude-SearchBot` and `Claude-User` answer; `ClaudeBot` trains.
  - Perplexity (`docs.perplexity.ai/guides/bots`): `PerplexityBot` and `Perplexity-User` answer. Perplexity says neither collects training data, so it has no training crawler.
  - Google (`developers.google.com/search/docs/crawling-indexing/google-common-crawlers` and `.../appearance/ai-features`): `Googlebot` is the answer kind, because Google says robots.txt rules for Googlebot are the control for AI Overviews and AI Mode. `Google-Extended` is the training kind: Google says it controls training of Gemini models and doesn't affect Search. Google also says it covers grounding in Gemini apps, so blocking it isn't only about training; the report still calls it a choice, as the item says.
  - `ChatGPT-User` and `Perplexity-User` may not obey robots.txt (their docs say so), so the report says what robots.txt *asks*, not what they do.
- **The rest of step 8:** `User-agent: *` with `Disallow: /`, a `noindex` or `none` meta tag, and an `X-Robots-Tag` header with either, are reported separately. 8b finds a business or organization block (in `@graph` too), its `@type`, and which of name, address, telephone, opening hours and url it carries. 8c reads phone, hours (day names near times) and street address (`<address>`, structured data, or a US street pattern) from the raw text with scripts and styles stripped, and the page says "found" or "I couldn't find", never "missing" (a test checks the word never appears). 8d uses the item's sentence exactly, only on a 200 page not cut at 1.5 MB. 8e compares digits only.
- **The number (step 10):** BrightLocal's own page `brightlocal.com/research/local-consumer-review-survey/` opened: "Local Consumer Review Survey 2026", published Feb 11, 2026, 1,002 US adults. It says use of ChatGPT and other generative AI tools for local recommendations rose from 6% last year to 45%. The line above the second card: "45% of people now use ChatGPT and other AI tools for local recommendations, up from 6% a year before (BrightLocal, 2026). See the source" (link to that page). It shows only after a check.
- **The page (steps 4, 6, 9):** `tools/checkup.py` writes `checkup.html` with `chrome.py`. `var CHECKUP_URL = '';` is the first line of its own script. While it's empty the page says "Coming this week" and shows no box, and sends nothing. When set: one address box, "Check it", the item's line under it, then the first card (worst finding first, each with what it costs and how hard it is to fix, then a short list of what works, ending with "Want me to fix it? →" to `call.html`), the BrightLocal line, and "Can AI find you?" with the item's first line, its findings worst first, and "The facts a machine reads off your page" (name, phone, address, hours as found) with the item's closing line. A refused address gets one plain sentence and no report.
- **Listed everywhere (step 5):** `enhance.py` (both page lists, and `FREE_TOOLS`, so the `local.html` "Free tools for your pile" section has five cards; its grid now fits five across at 1440), `build.py` (sitemap), `tools/og.py` (share card "WEBSITE CHECKUP / A free check for small businesses and nonprofits."; the other cards are unchanged), the work page's fifth tool card (`data-k="free"`, num "25 links", h2 "Website checkup"), and `chrome.py`'s tool list, so every tool's "More free tools" line now names the other four. `_build/README.md` step 4e.
- **Words I wrote (the item gave the shape, not the text; read them before "push it"):** the page title "Website Checkup", kicker "Free tool · checks your public page", h1 "Website checkup", lede, meta description, the dark panel ("Rather hand it off?" / "Start with a free 15-minute call.", both already used on the shot list page), the work card's tag "Websites", line "Paste your site's address and get a plain report of what's broken, worst first, and whether a machine can read the facts AI tools need." and link "Check your site →", and every finding and error sentence in `tools/checkup.py` (`siteCard`, `aiCard`, `ERR`). All plain, no long dashes. None of the findings show until the Worker is live.
- **Pipeline:** the unchanged pipeline rebuilt every root file byte for byte first (0 of 40 differed). After the change, `cmp` shows only `work.html` (the card), `local.html` (the fifth card and the grid width), the four tool pages (the "More free tools" line), `sitemap.xml` (one line), plus the new `checkup.html` and `og/checkup.png`. Every other root file, the other 18 share cards included, is unchanged.
- **Tests:** `test_new.py` **630/630 passed** (62 new, plus the T-02 checks and work-page counts updated to describe the fifth tool: 10 cards, 6 free, five local cards in one row at 1440). New: `node worker/test_checkup.mjs` passes from inside the run, **147/147**, with no network: every safety rule (schemes, ports, IP forms, private names, private DNS answers, each redirect hop re-checked, the 4th hop refused, the 1.5 MB cap, our User-Agent and no cookies, the 25-link cap, the 50-request budget), the link classifier, the Worker's door (other origins refused, CORS, the 20-second limit), 8a to 8e on made-up HTML and robots.txt, and `local.html` from the build through 8b (finds its ProfessionalService block, step 12). With two safety rules loosened in a temp copy, those tests fail as they should (142/147). In the browser: "Coming this week", no box and nothing sent while `CHECKUP_URL` is empty; with an address set in the browser only and the Worker's own answer for a made-up bakery: one GET only after the button, worst finding first and levels in order, the item's exact lines, the BrightLocal line with its source between the cards, the facts card, never "missing", the 8d sentence on a thin page and not on a cut one, a refused address, no sideways scroll at 390 and 1440. `node worker/test_intake.mjs` still 34/34. Run on Windows as a copy with `exe = None` and `p.chromium.launch()`, Playwright 1.65, per house rule 3. `test_site.py` not run.
- **Looked at:** `checkup.html` coming soon at 390 and 1440, the full report at 390 and 1440, the refused-address state at 390, the `local.html` tools section at 390 and 1440, the work page cards, the four tool pages' "More free tools" line, and the share card. One fix after looking: the two phone numbers in the 8e finding sat inside brackets twice ("((707) 555-0199)"); they now read with commas.
- **Worth knowing:**
  1. A link that answers 4xx or 5xx is called broken, as the item says. Some sites refuse automated checks with a 403, so now and then a working button may show as "leads to an error page".
  2. Cloudflare's docs promise working Cache API calls on custom domains and don't say so for `workers.dev`, and the cache is per data center. On the `workers.dev` address the 20-second limit may only hold per running instance (the backup).
  3. On the Workers Free plan a Worker gets 50 outside requests and 10 ms of CPU per request (`developers.cloudflare.com/workers/platform/limits/`). The check stays under 50 (links past that are marked "couldn't test"), but a very large page may hit the CPU limit and fail on the Free plan.
- **Josef, by hand (the deploy gate):**
  1. On this branch, open `_build/worker/checkup.js` and copy all of it.
  2. Open the Cloudflare dashboard and go to **Workers & Pages**.
  3. Select **Create application**, and start from the Hello World template.
  4. Name it `dj-checkup` and select **Deploy**.
  5. Select **Edit code**, select all the code in the editor, delete it, and paste the copied file in its place. Select **Deploy**. It needs no bindings or settings.
  6. Copy the Worker's `workers.dev` address from its page (it looks like `https://dj-checkup.<your-subdomain>.workers.dev`). Open it in a browser: it should say "dj-checkup is running".
  7. Paste the address to Claude in chat. Claude sets `CHECKUP_URL` in `tools/checkup.py`, rebuilds, tests, and commits.
  8. Say "push it" to Claude in chat. That merges this into `main` and the tool goes live. (Pushing before step 7 is safe: the page says "Coming this week".)
  9. Once live, open https://dragomansjourney.com/checkup.html on your phone, check `dragomansjourney.com`, and read both cards.

---

## T-15 · Host on Cloudflare, with a preview link per branch · DONE (build), GATED (switch)

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
- **Status: DONE (build), GATED (switch), Nov 12, 2026.** Branch `trip/T-15`, cut from `origin/trip/T-04` (the `trip/` branch with the newest commit). Nothing pushed to `main`. Both questions are answered. Work commit `72d51da`; the second answer is recorded in the commit after it. Steps 1 to 7 are done; the switch steps a to h are written below, with step d as the docs describe it (the answer to the second question). The switch is Josef's, at the desk.
- **The question, for Josef:** today GitHub Pages answers an address without `.html` too: `https://dragomansjourney.com/local` and `/work` both answer 200 (checked Nov 12), and `www` sends people on to the same address without www (301). With the settings the item gives (`html_handling: "none"` and the one `/ /index.html 200` line), `/local.html` stays exactly as it is, but `/local`, `/work` and the like answer 404 after the switch. No page, link or sitemap line on the site uses those short addresses; someone could still have typed or shared one. Which do you want?
  1. **Keep the short addresses working (my pick).** `publish.sh` writes one more line per page into `dist/_redirects` (`/local /local.html 200`, 16 pages, made from the file list, nothing typed by hand). Tested on wrangler's local server: `/local` and `/local.html` both answer 200 with the same page and no redirect, `/local/` stays 404 as it is today. 17 of the 18 pages already name their `.html` address as canonical, so search engines keep the `.html` one.
  2. **Let them answer 404**, exactly as the item is written. Simplest; anyone with a short address gets the site's 404 page.
  3. **Cloudflare's default** (`auto-trailing-slash`): `/local` works, but `/local.html` answers with a redirect to `/local`, which the item rules out.
  Answer in chat with 1, 2 or 3. Then set this item back to READY (build), GATED (switch).
  Answer (Josef, Nov 12, 2026): 1. Keep the short addresses working.
- **Built and proven in the first run (before the answer):**
  - `_build/publish.sh` (plain `sh`) makes `dist/`: every git-tracked file outside `_build/` except `CNAME`, `wrangler.jsonc` and dot or underscore names, plus `dist/_redirects` with `/ /index.html 200`. Today that's 41 files plus `_redirects`; compared with the rule worked out separately from `git ls-files`, the lists match, and every file is byte for byte its root file. It fails loudly (exit 1, a message) when `dist/` would be empty, and when anything from `_build/` lands in it (both tried).
  - `wrangler.jsonc`: `name` "dragomans-journey", `assets.directory` "./dist", `html_handling` "none", `not_found_handling` "404-page", `"previews": {}` (the Previews docs say the block is required and can be empty), `compatibility_date` 2026-11-12. No script, no secret.
  - `.gitignore`: `dist/`, `.wrangler/`, `node_modules/`.
  - Step 5 on wrangler 4.161.0's local server (`wrangler dev`, port 8765): `/` and `/local.html` answer 200 with no redirect; `/og/index.png` is a PNG; `/nope` answers 404 with the body of `404.html`; `/_build/README.md`, `/wrangler.jsonc`, `/CNAME` and `/_redirects` answer 404. `test_new.py` against that server: **630/630 passed** (run as a copy with `exe = None` and `p.chromium.launch()`, per house rule 3).
  - Step 6: every existing root file is unchanged; this item adds only `wrangler.jsonc` and `.gitignore` at the root.
- **Docs read so far (Nov 12, 2026), for the switch steps:** `developers.cloudflare.com/workers/static-assets/routing/advanced/html-handling/` (the default redirects `/file.html` to `/file`; `none` turns that off), `.../static-assets/redirects/` (`_redirects` is supported, a 200 line is a supported proxy for addresses on the same site, the file itself is never served), `.../static-assets/routing/static-site-generation/` (`404-page` serves the nearest `404.html` with status 404), `.../ci-cd/builds/` (Create application, GitHub, pick the repo, Save and Deploy; the Worker's name must match `name` in the config or the build fails), `.../ci-cd/builds/configuration/` (Build command, Deploy command `npx wrangler deploy`, Preview command `npx wrangler preview`, production branch), `.../ci-cd/builds/build-branches/` ("Enable Preview Builds" under Settings, Build, Branch control; pull request comments for other branches), `.../workers/previews/` and its configuration, get-started and custom-domains pages (Preview address `<preview-name>-dragomans-journey.<subdomain>.workers.dev`, public by default unless Cloudflare Access is added, can also live on a custom domain so `workers.dev` isn't required), `.../configuration/routing/custom-domains/` (the zone must be on Cloudflare; an existing CNAME on the name must be deleted first; `www` to the bare domain is a Redirect Rule). Not in the docs, to confirm at the desk: how a branch name with a slash and capitals (`trip/T-11`) becomes the preview name, and whether a private GitHub repository works.
- **Second run, Nov 12, 2026: the answer applied.** Same branch, `trip/T-15`, checked out from `origin/trip/T-15` at `2631137`; this run's work and receipt are in the commit after it. Nothing pushed to `main`.
  - **`publish.sh` (option 1):** after `/ /index.html 200`, it writes one line per page into `dist/_redirects`, like `/local /local.html 200`. The lines come from `git ls-files` (the `.html` files at the root that land in `dist/`), nothing typed by hand, so a page added later gets its line on its own. `index.html` and `404.html` get none. Today that's 16 lines, 17 with `/`. It still fails loudly when `dist/` would be empty and when anything from `_build/` lands in it (both tried again in throwaway clones: exit 1 and the message each time). `dist/` is still 41 files plus `_redirects`, the list matches the step 2 rule worked out separately from `git ls-files`, and every file is byte for byte its root file.
  - **Step 5, rerun in full on wrangler 4.161.0's local server** (`wrangler dev`, port 8765). These checks were only ever run by hand, from a small script in a scratch folder; no file in the repository keeps them. **41/41 passed:**
    1. `/` answers 200, no redirect, with the body of `index.html`.
    2. `/local.html` answers 200, no redirect.
    3. `/og/index.png` is a PNG (`image/png`, PNG signature).
    4. `/nope` answers 404 with the body of `404.html`.
    5. to 8. `/_build/README.md`, `/wrangler.jsonc`, `/CNAME` and `/_redirects` each answer 404.
    9. to 40. For each of the 16 pages with a line (briefing, call, captions, case-reels, checkup, comp3, local, mainframe, receipt, scaler, shotlist, start, studio-birdleague, studio-deepcuts, studio, work): the short address (like `/local`) and the `.html` address (like `/local.html`) both answer 200, no redirect, with the same body, which is the file in `dist/` (16 passed); and the short address with a slash (like `/local/`) answers 404 with the body of `404.html` (16 passed).
    41. `/404` answers 404.
    For the record, not a check: `/404.html` answers 200 (it's a file, as on GitHub Pages today) and `/index` answers 404 (no line, as the answer asked).
  - **`test_new.py` against that server: 630/630 passed** (house rule 3: run as a copy with `exe = None`, `p.chromium.launch()` and real Google Fonts, Playwright 1.65, on Windows). No test changed.
  - **Step 7:** a short "Hosting" section at the end of `_build/README.md`: what `publish.sh` makes, the `_redirects` lines and why the short-address lines are there, what `wrangler.jsonc` sets, how to check it locally, and that forms don't send from preview or `workers.dev` addresses.
  - **Step 6:** every existing root file is byte for byte the same as the branch as I found it: `cmp` of each of the 44 git-tracked files outside `_build/` (the 41 public files plus `CNAME`, `wrangler.jsonc` and `.gitignore`), as stored in this run's commit, against the same file in `2631137`, 0 differ. This run changed only `_build/publish.sh`, `_build/README.md` and this file. Nothing a visitor sees changed.
- **Second question, for Josef (Nov 12, 2026): how `www` reaches the site after the switch.** The gate's step d says to add both names to the Worker as custom domains, with `www` sending visitors on. Cloudflare's docs show a different way. A custom domain only matches its exact name, and for `www` they say to add a proxied placeholder record (`A`, `www`, `192.0.2.0`) plus a redirect rule, not a second custom domain. The docs never say whether a redirect rule runs before a Worker, so "`www` as a custom domain plus a rule" isn't shown to work; if the Worker answered first, `www` would show a second copy of the site instead of sending people on. Visitors end up in the same place either way. Which do you want?
  1. **The docs' way (my pick).** Only `dragomansjourney.com` is a custom domain on the Worker. `www` gets the placeholder record and the redirect rule. The switch steps below are written this way.
  2. **The item's way.** `www` is a second custom domain on the Worker, plus the same redirect rule. At the desk, open `https://www.dragomansjourney.com/local.html`: if it lands on `https://dragomansjourney.com/local.html`, keep it; if it shows the page at `www`, remove the `www` custom domain and do option 1.
  Answer in chat with 1 or 2. The next run records the answer here, changes step d if it's 2, and sets this item to DONE (build), GATED (switch).
  Answer (Josef, Nov 12, 2026): 1. The docs' way. Step d below already follows it, so nothing else changed.
- **What a visitor's address does today** (checked Nov 12 from here, for the checks in step e): `https://dragomansjourney.com/local` answers 200; `/local/` answers 404; `http://dragomansjourney.com/local.html`, `http://www...` and `https://www.dragomansjourney.com/local.html` each send people to `https://dragomansjourney.com/local.html` in one step (301). Public DNS shows `dragomansjourney.com` as four GitHub Pages A records and `www` as a CNAME to the GitHub Pages host. That isn't the full record list; step d1 writes that down from the dashboard.
- **Forms, said plainly:** forms on a preview address or on the Worker's own `workers.dev` address will not send, because the intake Worker only accepts the real site's address. That is expected. Do not add preview addresses or wildcards to the intake Worker.
- **Still to confirm at the desk** (the docs read today don't answer these):
  1. How a branch name like `trip/T-11` (a slash and a capital letter) becomes a preview name. The docs say only that the name "defaults to the current git branch". Read the real address off the Worker's Previews section after the first `trip/` branch builds (step b3).
  2. Whether a private GitHub repository works with Workers Builds. The docs say only that you see the repositories you can access on GitHub. Checked at step f3, with a way back.
  3. Which Wrangler version Workers Builds uses. The repository has no `package.json`, and the docs say only that Builds uses the version in `package.json`. Previews need Wrangler 4.135.0 or later. Read it in the first build log (step a8).
- **Switch steps for Josef** (at the desk, with Claude in chat, in one sitting; taken from the docs listed at the end, read Nov 12, 2026; step d follows the answer to the second question, the docs' way):
  - **Before you start:** the Worker builds from `main`, so `wrangler.jsonc` and `_build/publish.sh` must be on `main` first. They get there when you say "push it" for this branch. The `trip/` branches stack, so that also puts every earlier `trip/` item that isn't live yet on the live site. GitHub Pages keeps serving the site the whole time until step d; `wrangler.jsonc` is a name and a folder, no secret. If `main` doesn't have them, the first build in step a fails; that's harmless, but wait until they're there.
  - **a. Create the Worker from GitHub**
    1. Open the Cloudflare dashboard and go to **Workers & Pages**.
    2. Select **Create application**.
    3. Select **GitHub**.
    4. If asked, sign in to GitHub and install the Cloudflare Workers and Pages app. Under repository access, pick **Only select repositories** and choose `dragomans-journey-site`.
    5. Pick the repository `stephensjosef-cloud/dragomans-journey-site` from the list.
    6. Set the project up: name `dragomans-journey` (it must equal the `name` in `wrangler.jsonc`, or the build fails); **Build command** `sh _build/publish.sh`; **Deploy command** left as `npx wrangler deploy`; **Root directory** left empty (the repository root); **Git branch** (the production branch) `main`.
    7. Select **Save and Deploy**.
    8. Open the build log. It should print `publish.sh: 41 files in dist/, plus dist/_redirects (16 short addresses)` (the numbers grow as pages are added), then a successful deploy. Find the Wrangler version in the log and read it to Claude: it must be 4.135.0 or later for previews.
  - **b. Preview builds for other branches**
    1. In **Workers & Pages**, select **dragomans-journey**, then **Settings** > **Build** > **Branch control**, and tick **Enable Preview Builds**. Leave the **Preview command** as `npx wrangler preview` (the build command runs first).
    2. Ask Claude to push any `trip/` branch, as it does for every item.
    3. The preview address shows in the Worker's **Previews** section. When the branch has an open pull request on GitHub, Cloudflare also posts the address as a comment on it, and later pushes to the same branch update the same address. It looks like `<preview-name>-dragomans-journey.<your-subdomain>.workers.dev`. The preview name comes from the branch name; how `trip/T-11` turns into one isn't in the docs, so read the real address here and tell Claude, who writes it into `_build/README.md`.
    4. Preview addresses are public by default: anyone with the address can open one. Cloudflare Access can put a sign-in in front of them; that isn't part of this item.
    5. Forms on a preview address won't send (see above). That's expected.
  - **c. Check the Worker's own address on your phone, before touching the domain**
    1. On the Worker's page, copy its address, `https://dragomans-journey.<your-subdomain>.workers.dev`.
    2. On your phone, open it and check: the home page shows; `/local.html` shows the local page and the address stays `/local.html`; `/local` shows the same page; `/nope` shows the site's 404 page; `/og/local.png` opens as a picture.
    3. Don't try the forms here; they won't send.
  - **d. The switch**
    1. Open the Cloudflare dashboard, select the zone `dragomansjourney.com`, and go to **DNS** > **Records**. Write down every A, AAAA and CNAME record named `dragomansjourney.com` (shown as `@` or the bare name) or `www`: type, name, content, proxy status and TTL. Paste the list to Claude in chat and take a screenshot. This list is the way back.
    2. Never touch the MX and TXT records. The site's email addresses run on them.
    3. Delete only the records you wrote down in step 1, nothing else.
    4. Go to **Workers & Pages**, select **dragomans-journey**, then **Settings** > **Domains & Routes** > **Add** > **Custom Domain**. Type `dragomansjourney.com` and select **Add Custom Domain**. Cloudflare makes the DNS record for it.
    5. For `www`: go back to **DNS** > **Records** and add a record: type **A**, name `www`, IPv4 address `192.0.2.0`, proxy status **Proxied**. Save. (A placeholder: because it's proxied, no visitor ever reaches that address; Cloudflare answers with the redirect below.)
    6. Go to **Rules** > **Overview**, select **Create rule** > **Redirect Rule**. Rule name: `www to the bare name`. Under **When incoming requests match**, choose **Wildcard pattern** and set **Request URL** to `https://www.*`. Set **Target URL** to `https://${1}`, **Status code** to **301**, and turn on **Preserve query string**. Select **Deploy**.
    7. Go to **SSL/TLS** > **Overview** and check the encryption mode isn't **Off**. Then go to **SSL/TLS** > **Edge Certificates** and turn on **Always Use HTTPS**, so `http://` addresses still go to `https://` as they do today. (An `http://www` address may now take two steps instead of one; it still lands on the same page.)
  - **e. Check the live site**
    1. On your phone: `https://dragomansjourney.com/` shows the home page; `/local.html` shows and stays `/local.html`; `/local` shows the same page; `/nope` shows the 404 page.
    2. `https://www.dragomansjourney.com/local.html` and `http://dragomansjourney.com/local.html` both land on `https://dragomansjourney.com/local.html`.
    3. One form: on `https://dragomansjourney.com/start.html`, send a request with your own email. The page should confirm it was sent, and Gmail should get the email.
    4. One share card: open https://www.linkedin.com/post-inspector/, paste `https://dragomansjourney.com/local.html`, press **Inspect**, and check the card shows.
    5. Claude checks the same addresses from its side in chat and reads you the status codes.
    6. The Worker's own `workers.dev` address can be switched off now without losing branch previews: the docs say turning it off "does not disable Version URLs, Preview URLs, or Deployment URLs". In **Workers & Pages** > **dragomans-journey** > **Settings** > **Domains & Routes**, select **Disable** on `workers.dev` and confirm. Leave the **Preview** toggle under **Worker URL** on; that's the one previews use. Then Claude adds `"workers_dev": false` to `wrangler.jsonc` on a branch and you say "push it"; without it, the next deploy turns the address back on. Check that `https://dragomans-journey.<your-subdomain>.workers.dev` no longer shows the site and that a preview address still does.
  - **f. On GitHub** (only after step e looks right, and after `www` and the bare name no longer point at GitHub, which step d did; GitHub's docs say to change the domain's records first so nobody else can claim it)
    1. In the repository on GitHub, open **Settings** > **Pages**. Next to "Your site is live at", open the **...** menu and select **Unpublish site**.
    2. In **Settings**, in the **Danger Zone**, next to "Change repository visibility", select **Change visibility**, then **Private**. Confirm the repository name, select **I have read and understand these effects**, then **Make this repository private**. GitHub's docs say stars and watchers are erased and any public forks stay public, detached.
    3. Ask Claude to push a small branch. Check that a new build starts in Cloudflare and a preview address appears (step b3). If no build starts within a few minutes, the private repository isn't reaching Cloudflare: go back to **Change visibility**, choose **Public**, and tell Claude. The live site isn't affected either way; it's already served by the Worker.
  - **g. Web Analytics after the move**
    1. If `dragomansjourney.com` is already in **Web Analytics** (from T-12), open it, select **Manage site**, and choose **Enable with JS Snippet installation**. That stops Cloudflare adding a beacon of its own now that the site runs through Cloudflare (the docs say the automatic setup is on by default for such sites); the site carries its own from T-12. If it isn't there yet, nothing to do now: T-12's steps add it this way.
    2. Claude fetches every page of the live site in chat and counts the beacon: one per page and none on `comp3.html` once the T-12 token is set, none anywhere before that. Never two.
  - **h. The way back, if anything looks wrong**
    1. In **Workers & Pages** > **dragomans-journey** > **Settings** > **Domains & Routes**, remove the custom domain `dragomansjourney.com`.
    2. In **DNS** > **Records**, delete the `www` placeholder record from step d5, and in **Rules** > **Overview**, delete or turn off the `www` redirect rule.
    3. Add back every record from the list in step d1, exactly as written (type, name, content, proxy status, TTL).
    4. If step f was done: make the repository public again and publish Pages again from `main` with the custom domain `dragomansjourney.com`; Claude walks through it in chat.
    5. Optional tidy-up: the docs say the certificate made for the custom domain isn't deleted with it; it can be removed in **SSL/TLS** > **Edge Certificates**.
- **Cloudflare and GitHub docs read for this run (Nov 12, 2026):**
  - `developers.cloudflare.com/workers/ci-cd/builds/` (Create application, GitHub, pick the repository, Save and Deploy; the name must match `name` in the config; preview builds create or update a Preview, shown in the **Previews** section)
  - `.../workers/ci-cd/builds/configuration/` (Build command, Deploy command `npx wrangler deploy`, Preview command `npx wrangler preview`, Root directory, Git branch defaulting to `main`; Builds uses the Wrangler version in `package.json`)
  - `.../workers/ci-cd/builds/build-branches/` (**Settings** > **Build** > **Branch control** > **Enable Preview Builds**)
  - `.../workers/ci-cd/builds/build-image/` (Ubuntu 24.04 with git; Node 24 by default)
  - `.../workers/ci-cd/builds/git-integration/github-integration/` (repository access, pull request comments with the Preview URL; private repositories not mentioned)
  - `.../workers/previews/`, `.../previews/get-started/`, `.../previews/configuration/`, `.../previews/custom-domains/`, `.../previews/resources/`, `.../previews/test-and-debug/`, `.../previews/examples/` (address shape, public by default, Access, `"previews": {}` is valid, Wrangler 4.135.0 or later, name defaults to the git branch with no stated rules)
  - `.../workers/wrangler/commands/workers/` (`wrangler preview --name` "Defaults to the current git branch")
  - `.../workers/configuration/routing/workers-dev/` (turning off `workers.dev`, and `"workers_dev": false` or it comes back on the next deploy; Preview URLs keep working)
  - `.../workers/configuration/routing/custom-domains/` (adding a custom domain, removing CNAME records first, `www` by a proxied `192.0.2.0` record and a redirect rule, the certificate left behind)
  - `.../rules/url-forwarding/examples/redirect-www-to-root/`, `.../rules/url-forwarding/single-redirects/create-dashboard/`, `.../rules/url-forwarding/` and `.../ruleset-engine/reference/phases-list/` (the `www` rule; neither order list mentions Workers)
  - `.../ssl/edge-certificates/additional-options/always-use-https/`
  - `.../workers/static-assets/routing/advanced/html-handling/`, `.../workers/static-assets/redirects/` (200 lines serve a page on the same site, the file is never served, 2,000 static lines allowed), `.../workers/static-assets/routing/static-site-generation/` (`404-page`)
  - `.../web-analytics/get-started/` (automatic setup on by default for proxied sites; **Manage site** > **Enable with JS Snippet installation**)
  - `docs.github.com`: "Unpublishing a GitHub Pages site" and "Setting repository visibility"

---

## T-16 · Intent pass 2 · DONE

**Why:** Josef, Nov 12, 2026: the pages added since Oct 28 were never checked against the intent rule; this applies his audit.

**Build:**
- **N1.** Home: remove the "Shipped lately" strip between the intro and the two route cards (heading, three log lines, "See everything I'm building →"). The header's Studio link stays.
- **N2.** Studio: remove "The studio · updated as things ship" above the title.
- **N3.** Studio: the intro keeps only "Everything I'm building right now, and the date each piece shipped." The meta description stays as it is.
- **N4.** Studio: the counts strip keeps only "<n> things shipped since Oct 6", still computed from the log, and doesn't sit in a three-column box.
- **N5.** `shipped.json`: remove four entries, shorten the Deepcuts new-look line to "Deepcuts got its new look.", and add the stranger rule to `_about` and to the "To log a ship" line in `_build/README.md`.
- **N6.** Studio cards: stop printing the kind label; the status pill stays.
- **N7.** Studio cards: "See it move →" becomes "More on Bird League →" and "More on Deepcuts →".
- **N8.** Product pages: the line above the title becomes one link, "← The Studio", to `studio.html`.
- **N9.** Product pages: their logs follow N5 on their own (confirm).
- **N10.** Work page: remove the big figure from seven cards; keep "~4 min", "535 tests", "2 AI translations"; cards still line up.
- **N11.** Work page, Bird League card: "More about how I work →" becomes "See Bird League →" to `studio-birdleague.html`.
- **N12.** Work page, cooking app card: "iPhone, iPad, Android and the web."
- **N13.** All five tool pages: the line above the title is just "Free tool".
- **N14.** All five tool pages: remove the "More free tools" button from the dark panel; the line above it and the panel's other button stay.
- **N15.** Recipe scaler intro: remove "Kids count as half a portion." (the line under the boxes stays).
- **N16.** Shot list: show the countdown only at 42 days away or fewer, today included; farther out, nothing and no empty box. Test both sides.
- **N17.** `local.html`: remove "Recently finished" (heading and four lines) and the `plain.py` rewrite that existed only for its heading.
- **N18.** `local.html` drop-in box, no date: three lines become "No date set yet. Leave your email and you'll get it first."; form and button stay. Update T-13 step 1 to match.
- **N22.** Checkup: the line above the second card becomes "45% of US adults surveyed now use ChatGPT and other AI tools for local recommendations, up from 6% a year before (BrightLocal, 2026)." with the same "See the source" link.
- **N24.** `mainframe.html`: remove the lone "05" and "06"; the audit report's 01 to 07 stay.
- **N25.** Remove "Studio" and "Free tools" from the header of `mainframe.html`, `briefing.html` and `comp3.html` only; T-02's rule now reads "every header except the three Mainframe pages".

**Receipt:**
- **Branch:** `trip/T-16`, cut from `origin/trip/T-15` (the `trip/` branch with the newest commit, `6bb5770`). Work commit `c0340b4`; this receipt is in the commit after it. Nothing pushed to `main`.
- **Pipeline:** the unchanged pipeline rebuilt every root file byte for byte first. After the change, `cmp` of every file in `out/` (and `out/og/`) against the root shows exactly the 14 named pages differ: `index`, `studio`, `studio-birdleague`, `studio-deepcuts`, `work`, `shotlist`, `captions`, `receipt`, `scaler`, `checkup`, `local`, `mainframe`, `briefing`, `comp3`. Every other root file, the 17 share cards and `sitemap.xml` included, is unchanged. No title, meta description or share card changed, so `tools/og.py` wasn't run.
- **Each change, where it was made:**
  - **N1** `index.html`: the "Shipped lately" strip (heading, 3 log lines, "See everything I'm building →") is gone; `add_studio_band()` removed from `enhance.py` with its inline styles. The hero now runs straight into the two routes. The header's Studio link stays.
  - **N2** `studio.html`: "The studio · updated as things ship" no longer prints. `tools/chrome.py` now writes no kicker span at all when a page has none, so no empty line is left. The page title still comes from the kicker's first part ("The studio"), so the `kicker` field stays in `studio.json`.
  - **N3** `studio.html`: the hero shows only "Everything I'm building right now, and the date each piece shipped." (new `intro` field in `studio.json`, the sentence word for word). The meta description is unchanged and still drops the album while it's gated.
  - **N4** `studio.html`: one count, "13 things shipped since Oct 6", still counted from the log by `studio.py`. "in the last 30 days" and "projects" are gone, and so is the three-column grid: the count is one full-width block between the two rules. The CSS for the columns and the code that counted the other two numbers are removed.
  - **N5** `shipped.json`: the four entries removed, the Deepcuts line now "Deepcuts got its new look.", and the stranger sentence added to the end of `_about` and to the "To log a ship" line in `_build/README.md`. The log now has 14 entries; 13 show (the album's is gated). The Studio log, its "See all 13" button and both product pages follow on their own.
  - **N6** `studio.html`: no kind label on any card. `kind` stays in `studio.json`; its span and its `.kind` CSS are gone. The status pill stays.
  - **N7** `studio.html`: "More on Bird League →" and "More on Deepcuts →".
  - **N8** `studio-birdleague.html`, `studio-deepcuts.html`: the line above the title is one link, "← The Studio", to `studio.html`.
  - **N9** confirmed: Bird League's page lost "Bird League build 50 runs on Apple's newest tools." (5 lines now); Deepcuts' lost "Deepcuts build 4 works end to end on iPhone." and shows "Deepcuts got its new look." (3 lines). No code change was needed.
  - **N10** `work.html` (source `_build/work.html`): the seven figures are gone; "~4 min", "535 tests" and "2 AI translations" stay. The `.num` CSS stays, since those three still use it. Cards still line up: at 1440 the three with a figure share the first row, and in the Nonprofits and Banking filters, where cards with and without a figure share a row, each row's cards have the same top, height and link line (tested). Only the heading starts higher on a card without a figure.
  - **N11** `work.html`: the Bird League card's link is "See Bird League →" to `studio-birdleague.html`.
  - **N12** `work.html`: "iPhone, iPad, Android and the web." The sentence is written by `intent.py`'s F2 edit, so the change is there.
  - **N13** all five tool pages: the kicker is "Free tool" (`tools/*.py`).
  - **N14** all five tool pages: the "More free tools" button is gone from the dark panel (`tools/chrome.py`). The "More free tools: ..." line above it and each panel's own button stay.
  - **N15** `scaler.html`: "Kids count as half a portion." removed from the intro; "A kid counts as half a portion." under the boxes stays.
  - **N16** `shotlist.html`: the countdown shows only from 42 days before the date to the day itself (`SOON = 42`). Farther out, its row is hidden and the panel starts at "The reel, second by second" with no gap (the 18 px space moved from the label onto the countdown row, so it goes with it). A date already past also shows nothing; before, that could show a negative count for the three days between Small Business Saturday and Giving Tuesday. Tested at 42 and 43 days for both Small Business Saturday (Oct 17, Oct 16) and Giving Tuesday (Oct 20, Oct 19), on the day itself ("Today"), and today (16 days).
  - **N17** `local.html`: "Recently finished" and its four dated lines are gone, removed in `enhance.py` (the canvas file is left matching the claude.ai Design canvas). In `plain.py` five rewrites existed only for that section and are removed so the build can't fail on a missing match: the heading's, as asked, and the four line labels' (`Program app engine.`, the 324-tests line, `Reels Engine.`, `Proof method, in public.`), which would have failed the build the same way.
  - **N18** `local.html`: with no date set, the drop-in box shows one line, "No date set yet. Leave your email and you'll get it first." (`enhance.py`, no-date branch). The form and "Put me on the list →" stay. The dated branch still prints "NEXT DROP-IN", the date and the place as before. The two `plain.py` rewrites and `intent.py` L28, which only rewrote the old no-date lines, are removed. **T-13 step 1** now says the no-date box shows that one line, written as final wording in `enhance.py`, that `plain.py` and `intent.py` no longer touch the drop-in card, and still asks to prove the no-date page unchanged first.
  - **N22** `checkup.html`: "45% of US adults surveyed now use ChatGPT and other AI tools for local recommendations, up from 6% a year before (BrightLocal, 2026)." with the same "See the source" link. No finding or error sentence changed.
  - **N24** `mainframe.html`: the lone "05" and "06" are gone (`enhance.py`, and the two `plain.py` renumberings for them removed). "05" was the only thing in its column, so the column went too: at 1440 "What this does not prove." now starts at the page's left margin instead of behind an empty 260 px column, while sections 1, 3 and 4 keep their empty columns from Oct 28 (not named, not touched). The section about Josef keeps its photo column. The audit report's 01 to 07 are unchanged.
  - **N25** `mainframe.html`, `briefing.html`, `comp3.html`: no "Studio" or "Free tools" in the header, which is back to its own links ("Request a briefing", "← The Mainframe Route", "The Mainframe Route →"). Every other page keeps both. `_build/README.md` step 4d says so.
- **Intent report.** Lines added, each with its reader and job: (1) "No date set yet. Leave your email and you'll get it first.", `local.html` drop-in box: a local owner who wants to come, so they know there's no date yet and that the form gets them one. (2) "← The Studio", over each product page's title: someone who landed on a product page from a link, so they have one way to everything else. (3) "More on Bird League →" / "More on Deepcuts →", Studio cards: a reader of the card, so the link names where it goes. (4) "See Bird League →", work page: a visitor reading the Bird League card, so they reach its page. (5) "iPhone, iPad, Android and the web.", work page: a teacher or program lead, so they know it runs on what they have. (6) "45% of US adults surveyed now use...", checkup: an owner deciding whether AI findability matters, so the number says who was asked. (7) "Free tool", tool kickers, and (8) "Deepcuts got its new look.", the log: shorter forms of lines already there. Off screen only: the stranger sentence (README and `_about`), the `_about` notes in `studio.json`, code comments.
  Lines removed, where and why: home "Shipped lately" strip, 3 lines and its link (N1, a feed on the front door that the Studio already holds); Studio "The studio · updated as things ship" (N2, restates the title), the intro's second and third sentences (N3, restate the page), "in the last 30 days" and "projects" (N4, numbers nobody acts on), the four log lines and the Deepcuts tail (N5, a stranger can't picture what changed), the five kind labels (N6, the pill already says it), "See it move →" (N7); "The studio · My own app" on both product pages (N8); seven work-card figures (N10, slogans in a figure's place) and "More about how I work →" (N11); "· runs in your browser" and "· checks your public page" (N13, the intros already say it); five "More free tools" buttons (N14, the line above already links the tools); "Kids count as half a portion." in the scaler intro (N15, said where it applies); the shot list countdown more than 42 days out (N16); "Recently finished" and 4 lines (N17); "NEXT DROP-IN", "Get the next date", "Sign up and you'll hear the date first." (N18, three lines for one fact); "05" and "06" (N24, numbers with no list); "Studio" and "Free tools" in three Mainframe headers (N25, a bank reader isn't there for either).
- **Tests updated to describe this item** (no expectation changed to make a failure pass): T-02's nav check now expects "Free tools" in every header except `mainframe`, `briefing` and `comp3`, and checks those three have none; T-08's strip check (one count, not three), hero check (no kicker), hero text check (first sentence), meta description check (unchanged, album rule kept), the two album-state checks from the temp copy (hero is the first sentence, meta reads as approved), card check (name, status and what; kind no longer printed), the four home band checks (now: no strip, hero straight into routes, Studio link kept, screenshot of the top instead of the band), and the Studio-in-every-header check (except the three Mainframe pages); T-09's "See it move →" check (now "More on <name> →") and kicker check (now one link, "← The Studio"); T-04's work card check (no "25 links" figure). New: every N line above, including the N16 dates either side of 42 days, the N10 line-up in three views, and no sideways scroll at 320 and 390 on all 14 pages.
- **Tests:** `test_new.py` **711/711 passed** (630 before this item). Run on Windows as a copy with `exe = None`, `p.chromium.launch()` and real Google Fonts, Playwright 1.65 in a scratch virtual environment, against `out/` served on port 8765, per house rule 3. `node _build/worker/test_intake.mjs` **34/34**, `node _build/worker/test_checkup.mjs` **147/147**. `test_site.py` not run.
- **Looked at** (screenshots in the session's scratch folder, `t16-<page>-<width>.png` full pages and region shots of each change), every changed page at 320, 390 and 1440:
  - `index`: reads as the hero, then the two route cards. Nothing floating; Studio, Free tools and the call button in the header.
  - `studio`: reads as "Built in the open", one sentence, the big count "13 / things shipped since Oct 6" on its own between two rules, then the log and the cards. Each card is name, pill, what, link. Nothing cut off at 320.
  - `studio-birdleague`, `studio-deepcuts`: "← THE STUDIO" (the kicker style is capitals) sits alone over the name and is the link back, 44 px tall; the log shows 5 and 3 lines.
  - `work`: three cards with figures in the first row at 1440, the Bird League card with "See Bird League →" sitting on its text, then six tool cards with no figures. In the Nonprofits filter the scaler card sits beside two figure cards with the same box and link line. One column at 320 and 390.
  - Tool pages: "FREE TOOL" over each title; the dark panel holds its heading, line and one button, with no hole where the second was. Shot list today shows "16 days until Small Business Saturday, Nov 28."; at 43 days the panel opens on "The reel, second by second" with no empty row. Checkup's line wraps cleanly at 320 with "See the source" on the link.
  - `local`: the section about Josef runs into "Questions people ask"; the dark band is gone with no seam left. The drop-in box reads as one bold line, then Email, Name and the button.
  - `mainframe`: header is the name and "Request a briefing"; "What this does not prove." box has no number over it and starts at the left margin at 1440 (see N24); the photo column over the section about Josef has no number.
  - `briefing`, `comp3`: header is the name and the one link back to the Mainframe Route.
  - Every label sits on what it names and nothing overlaps. Worth knowing, not changed here: on the tool, Studio and product pages the header's text links are 24 px tall (the call button is 44); that's how they were before this item.
- **Josef, by hand:**
  1. Read the 14 pages from this branch (or the screenshots).
  2. Say "push it" to Claude in chat. That merges this into `main` and the site goes live.
- **Decided Nov 12:** Josef said leave "What this does not prove." full width at desktop. Nothing else changed.

---

## T-13 · The first drop-in date · GATED

**Gate:** Josef gives Claude the date, the hours and the place.

**Build:**
1. With no date set, the drop-in card shows one line, "No date set yet. Leave your email and you'll get it first.", written as its final wording in the no-date branch of `enhance.py` (T-16 put it there; `plain.py` and `intent.py` no longer touch the drop-in card, so setting a date can't fail the build on a missing match). Keep that branch as it is, so the no-date page comes out word for word as it is today. Prove that first: with no date set, every rebuilt root file is byte for byte unchanged.
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
