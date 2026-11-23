---
version: alpha
name: Dragoman's Journey
description: Bush Pilot Chart. A light aeronautical-chart look for a one-person AI studio in Santa Rosa. The feeling is being in calm, competent hands.
colors:
  chart: "#E4ECD8"
  card: "#F7F9F3"
  ink: "#17212B"
  ink-muted: "#4F5A63"
  orange: "#E8592B"
  orange-text: "#A93F17"
  blue: "#1C5FA8"
  contour: "#A88B5C"
  on-ink: "#F7F9F3"
  on-ink-muted: "#B9C3CC"
  orange-on-ink: "#F07A4E"
  blue-on-ink: "#8FB8E8"
typography:
  display:
    fontFamily: Barlow Semi Condensed
    fontSize: 5rem
    fontWeight: 700
    lineHeight: 0.92
  heading:
    fontFamily: Barlow Semi Condensed
    fontSize: 2.5rem
    fontWeight: 700
    lineHeight: 1
  label:
    fontFamily: Barlow Semi Condensed
    fontSize: 1.125rem
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: Barlow
    fontSize: 1.125rem
    fontWeight: 400
    lineHeight: 1.55
  body-strong:
    fontFamily: Barlow
    fontSize: 1.125rem
    fontWeight: 600
    lineHeight: 1.4
  data:
    fontFamily: JetBrains Mono
    fontSize: 0.9375rem
    fontWeight: 400
    lineHeight: 1.5
  long-read:
    fontFamily: Newsreader
    fontSize: 1.25rem
    fontWeight: 400
    lineHeight: 1.6
rounded:
  none: 0px
  pill: 999px
spacing:
  xs: 8px
  sm: 16px
  md: 24px
  lg: 32px
  xl: 64px
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.on-ink}"
    typography: "{typography.body-strong}"
    rounded: "{rounded.none}"
    height: 52px
    padding: 26px
  card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: 24px
  status-pill:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.on-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
  link:
    textColor: "{colors.ink}"
    typography: "{typography.body-strong}"
  link-hover:
    textColor: "{colors.orange-text}"
---

## Overview

Dragoman's Journey is one person, Josef Stephens, building AI tools for small businesses and nonprofits around Santa Rosa, and checking COBOL translations for banks. The look borrows from an aeronautical chart: chart-paper green, an orange route, blue airspace, brown contour lines. The feeling it borrows is the one a good bush pilot gives you: you are in calm, competent hands, and you always know what happens next.

It is the feeling, not a theme. No aviation words in the copy. What carries over is behavior:

- You always know what happens next, and when.
- A clear no when the work isn't a fit, and where to go instead.
- The loop gets closed after the work is done.
- One obvious next step per page.
- A calm, specific voice.

## Colors

- **Chart (#E4ECD8):** the page background. Pages are light.
- **Card (#F7F9F3):** cards, panels and form fields.
- **Ink (#17212B):** text, 2px card borders, the main button, and dark bands (the footer and the closing call box).
- **Ink muted (#4F5A63):** secondary text, 5.8:1 on chart.
- **Orange (#E8592B fill, #A93F17 text on light):** the Local route and the one next step: its ring, route lines and short labels. Never body text, never a background.
- **Blue (#1C5FA8):** the Mainframe route's accent, in place of orange on the Mainframe pages, and data marks.
- **Contour (#A88B5C):** background contour lines only, at about 38% opacity. Never text.
- **On ink (#F7F9F3), on ink muted (#B9C3CC), orange on ink (#F07A4E), blue on ink (#8FB8E8):** the same roles inside a dark band.
- Every text pair keeps WCAG AA: 4.5:1 for body text, 3:1 for large text and controls.

## Typography

- Barlow Semi Condensed 700 for headlines and the site name, in sentence case. 600 for short labels in the accent color.
- Barlow 400 for everything people read; 600 for buttons and links.
- JetBrains Mono only where the content is data: receipts, tables, the COBOL tools.
- Newsreader only for long reading on the Mainframe pages.
- Lines of text at most 34em wide. No all-caps labels above headings.

## Layout

- Left-aligned. One column of text at most 34em; cards in a grid that stacks under 900px.
- At least 64px between sections; 24px inside a card.

## Elevation & Depth

- Flat. No shadows. Depth comes from the 2px ink border and the card sitting on the chart.

## Shapes

- Square corners on cards, buttons and fields. Status pills are the only rounded shape.
- **The ring:** one hand-drawn orange ellipse around the page's one next step. One per page, never more.
- **The route:** a dashed orange line (3px, 10 on, 8 off) linking the steps of a process, from where you are to done.
- **The pen underline:** a slightly wavy hand-drawn line under a headline's marked words, in the accent (blue on the Mainframe pages). Headlines never switch to italic: marked words stay upright in their color, and three words or fewer also get the pen underline. Decoration only, never on a tap target.
- **The location mark:** the ringed crosshair from the logo, next to "Santa Rosa".
- Contour lines behind heroes; blue airspace circles only on the Mainframe pages.

## Motion & Micro-interaction

- Almost none. The route line may draw itself once when it scrolls into view; reduced motion turns that off. A link turns orange on hover.

## Voice & Content Strategy

- Short, steady, specific: what happens, when, and what's next. Real times instead of "soon".
- Say no plainly when it's not a fit, and say where to go instead.
- No hype, no exclamation marks, no em dashes, no emoji.
- No aviation words in the copy: flight plan, cleared, runway, logbook, weather hold, pilot, cockpit. The chart is a look, not a theme.

## Components

- **button-primary:** ink, square, 52px tall. The page's one next step gets the ring around it.
- **card:** 2px ink border, card background, square corners.
- **status-pill:** an ink pill with an on-ink label, like "In testing on iPhone".
- **link / link-hover:** ink, underlined 4px below the text, orange on hover.

## Do's and Don'ts

- Do give each page one next step, ringed.
- Do say when someone will hear back.
- Don't draw a second ring on a page.
- Don't use orange for body text or as a background.
- Don't build dark hero sections; dark is for the footer and the closing call box.
- Don't put all-caps tracked labels above headings, or monospace labels outside data.
