#!/usr/bin/env python3
"""Render docs/og-paper.png — the 1200x630 social-share card for the paper page.

Rendered from HTML through the same engine that draws the site, so the card
matches the page instead of approximating it.

    pip install playwright && python3 work/scripts/make_paper_og.py
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "og-paper.png"

CARD = """
<style>
  @page { margin:0 }
  *{box-sizing:border-box; margin:0}
  body{width:1200px; height:630px; background:#0d1219; color:#e7edf4;
       font-family:"IBM Plex Sans","Liberation Sans",system-ui,sans-serif;
       display:flex; flex-direction:column; justify-content:space-between;
       padding:74px 80px 66px; position:relative; overflow:hidden}
  .glow{position:absolute; width:760px; height:760px; right:-280px; top:-320px; border-radius:50%;
        background:radial-gradient(circle,rgba(108,176,245,.20),rgba(108,176,245,0) 68%)}
  .eyebrow{font-family:"IBM Plex Mono","Liberation Mono",monospace; font-size:20px;
           letter-spacing:.17em; text-transform:uppercase; color:#8698ab}
  h1{font-family:"IBM Plex Serif","Liberation Serif",Georgia,serif; font-weight:600;
     font-size:70px; line-height:1.09; letter-spacing:-.02em; max-width:17ch; color:#fff}
  .deck{font-size:26px; color:#bcc9d8; max-width:34ch; margin-top:22px; line-height:1.45}
  .stats{display:flex; gap:56px; border-top:1px solid #243140; padding-top:26px}
  .n{font-family:"IBM Plex Mono","Liberation Mono",monospace; font-size:36px;
     font-weight:600; color:#6cb0f5}
  .l{font-size:17px; color:#8698ab; margin-top:5px}
  .by{margin-left:auto; text-align:right; font-size:17px; color:#8698ab; align-self:flex-end}
</style>
<div class="glow"></div>
<div>
  <p class="eyebrow">FlyRank ML Internship &middot; Capstone</p>
  <h1>Which page should an editor open first?</h1>
  <p class="deck">Ranking 18,010 pages by 30-day search-decline risk &mdash; and
     the baseline rule that could not rank at all.</p>
</div>
<div class="stats">
  <div><div class="n">18,010</div><div class="l">pages ranked out-of-fold</div></div>
  <div><div class="n">0.88</div><div class="l">precision@50</div></div>
  <div><div class="n">0.74</div><div class="l">rule baseline</div></div>
  <div class="by">Nguy&#7877;n Ho&agrave;ng T&uacute;<br>August 2026</div>
</div>
"""


def chromium():
    for p in sorted(pathlib.Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome")):
        return str(p)
    return shutil.which("chromium") or shutil.which("google-chrome")


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("needs playwright: pip install playwright")

    tmp = ROOT / "work" / "outputs" / "_og_card.html"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(CARD, encoding="utf-8")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=chromium())
            page = browser.new_page(viewport={"width": 1200, "height": 630})
            page.goto("file://" + str(tmp))
            page.wait_for_timeout(500)
            page.screenshot(path=str(OUT))
            browser.close()
    finally:
        tmp.unlink(missing_ok=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
