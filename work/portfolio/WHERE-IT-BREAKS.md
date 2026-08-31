# Where it breaks

Hardening pass on the portfolio and its contact form. The goal was to break my own
site, not to confirm it works — so this is written around what failed, not what passed.

Everything below is reproducible:

```
python3 work/scripts/harden_portfolio.py     # the adversarial pass
python3 work/scripts/test_contact_form.py    # the happy path + obvious failures
python3 work/scripts/audit_portfolio.py      # links, contrast, SEO, assets
```

---

## What I tried

Not just an empty form. The list I actually ran:

**The form** — empty submit · whitespace-only fields · `<script>alert(1)</script>` and
`<img src=x onerror=...>` in name and message · `'; DROP TABLE users;--` · emoji and
right-to-left Arabic · 40 stacked combining marks on my own name · `user@localhost` (no
TLD) · `a@@b.co` · an address with a leading space · a 9,000-character message · a
400-character unbroken word · clicking Send twice with zero delay · hammering Enter five
times · sending a second message straight after the first.

**The page** — every nav link and every outbound link · JavaScript switched off · 320px
and 360px screens · 200% text zoom · keyboard-only navigation including whether the
honeypot can be reached by Tab.

Three things broke.

---

## Fixed

### 1. The sticky nav swallowed every in-page link — *serious*

Clicking **Projects**, **Approach**, **Skills** or **Contact** scrolled the section to
`top: 0`, directly underneath the 47px sticky bar. The heading you just asked for was
the one thing hidden. Every single nav link was affected, so any recruiter using the
nav landed on a page that looked broken.

I did not catch this by looking. I caught it by measuring the heading's position against
the nav's height after a programmatic click.

**Fix:** `scroll-margin-top: 4rem` on every section.
**Evidence:** heading top went from `-0px` (under a 47px nav) to `64px` (clear of it) on
all four links.

### 2. Email validated trimmed, but sent untrimmed

Validation ran on `value.trim()`, while the payload was built from the raw field. So
` me@example.com` passed the check and arrived at my inbox with the leading space still
attached — which is exactly the field Web3Forms uses for reply-to. The message would
land, and replying to it would fail.

A quiet one: nothing errors, nothing looks wrong, and you only find out when a reply
bounces.

**Fix:** trim string values when building the payload.
**Evidence:** the harden suite now asserts the delivered address is exactly `a@b.co`.

### 3. Nav row overflowed at 200% text zoom

At 200% font size on a 390px screen the page scrolled sideways — 391px of content in a
390px viewport, caused by the four nav links refusing to wrap. One pixel, but horizontal
scrolling at 200% zoom is a WCAG 1.4.10 reflow failure, and people who zoom are exactly
the people it hurts.

**Fix:** `flex-wrap: wrap` on the nav row.
**Evidence:** no horizontal scroll at 2× font size.

---

## Tried and did not break

Worth recording, because "I tested it" means nothing without the list:

| Attack | Result |
|---|---|
| Double-click Send, zero delay | one email — the button disables synchronously |
| Enter pressed five times | one email |
| `<script>` / `<img onerror>` in fields | delivered as plain text, nothing executes |
| SQL injection strings | delivered as text |
| Emoji, Arabic RTL, 40 combining marks | delivered intact, no mangling |
| Whitespace-only fields | rejected client-side |
| `user@localhost`, `a@@b.co` | rejected client-side |
| 9,000-character message | capped at 3,000 by the browser |
| 400-character unbroken word | does not widen the page |
| JavaScript off | form still posts natively; no spurious warning |
| 320px and 360px screens | no horizontal scroll |
| Keyboard only | every control reachable; honeypot never focusable |
| Second message, same session | works |

---

## Known limitations — not fixed, not hidden

**1. There is no server-side validation, and there cannot be.** Every check runs in the
browser. Anyone can read my access key in the HTML and POST straight to Web3Forms,
skipping all of it. I accept this: the key is an address, not a credential, so the worst
case is junk in my own inbox. If it becomes a problem I rotate the key.

**2. The honeypot only catches naive bots.** It stops scripts that parse HTML and fill
every field. A bot that renders CSS, or one aimed at this form specifically, walks
through it.

**3. I control no rate limit.** The free tier is 250 messages a month. Someone
determined could burn through that, and then the form **silently stops delivering** until
the quota resets — with no alert to me and a green "message sent" shown to the visitor.
This is the failure I would fix first if the site mattered commercially.

**4. `robots.txt` cannot work here.** Crawlers only read it at the domain root
(`john-hcmus.github.io/robots.txt`), which I do not control — this is a project page on
a shared domain. I shipped `sitemap.xml` instead and will submit it manually through
Search Console. A custom domain would remove this limitation.

**5. Google Fonts is a third-party render-blocking dependency.** On a slow or restricted
network the page renders in fallback fonts. Mitigated with `preconnect` and
`display=swap`, so text is never invisible — but the layout does shift slightly when the
webfont lands.

**6. Speed is measured on localhost, not in the world.** Numbers below are honest about
what they exclude.

**7. Tested in Chromium only.** No real iOS Safari, no real Android device. Safari is
the gap I would most like to close.

**8. No analytics.** I cannot tell whether anyone visits or where they drop off.

**9. Three of five projects have no repository link,** and the Transformer project's
result has no number attached. On a page that argues from evidence, those are the weak
items — named here rather than quietly left.

---

## SEO and meta added

| Item | Value |
|---|---|
| `<title>` | 55 chars, name + target role |
| `<meta description>` | 149 chars — under the ~155 Google shows |
| Canonical URL | set |
| `robots` | `index, follow, max-image-preview:large` |
| Open Graph | title, description, url, type, locale, site_name |
| `og:image` | real 1200×630 PNG, absolute URL, with `og:image:alt` |
| Twitter | `summary_large_image` |
| JSON-LD | `Person` — job title, `knowsAbout`, `sameAs` → GitHub + LinkedIn |
| Favicon | inline SVG monogram |
| Sitemap | `docs/sitemap.xml`, both pages |

The share image is generated, not a screenshot: name, target role, one-line value
proposition, and the three numbers that matter (18,010 · 0.88 · public paper + code).
The audit script asserts it is exactly 1200×630 so it can never silently rot.

## Speed

Measured over localhost, so **network latency is excluded** — treat these as a floor,
not a real-world score.

| Metric | Value |
|---|---|
| Visitor payload | **41 KB** total (HTML + favicon) |
| First contentful paint | 108 ms |
| DOMContentLoaded | 30 ms |
| DOM nodes | 234 |
| Requests | 3 — the document, the favicon, and Google Fonts |
| Render-blocking external resources | 1 (Google Fonts) |

No images on the page, no JavaScript frameworks, no CSS files: everything is inlined in
one 41 KB document. The 62 KB `og.png` is fetched only by social crawlers, never by a
visitor.

---

## Still needs a human

Three things I could not do myself, and why:

1. **A real PageSpeed Insights / Lighthouse run.** It has to hit the live URL from
   outside. My numbers exclude network latency entirely.
2. **Searching my own name to check findability.** Indexing takes days to weeks after
   the meta went live; the sitemap still needs submitting to Google Search Console.
3. **The hardening review itself** — a mentor or structured peer read of this document
   and the fixes. Their must-fixes get added here as a new section.
