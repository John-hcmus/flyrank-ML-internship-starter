#!/usr/bin/env python3
"""Apply work/portfolio/site.json to everything served out of docs/.

Three values live in one place and get stamped into the pages from here, so
going live on a new address is one command instead of a hunt through the HTML:

    base_url          the address the site is canonical on
    goatcounter_code  the GoatCounter site code (analytics)
    badge_verify_url  where the FlyRank graduate badge points

Usage
    python3 work/scripts/configure_site.py                    # apply site.json as-is
    python3 work/scripts/configure_site.py --go-live          # switch to base_url_target
    python3 work/scripts/configure_site.py --base https://x.dev
    python3 work/scripts/configure_site.py --analytics hoangtu
    python3 work/scripts/configure_site.py --verify https://.../verify/abc
    python3 work/scripts/configure_site.py --check            # report only, change nothing

Safe to run repeatedly: every rewrite is idempotent.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG = ROOT / "work" / "portfolio" / "site.json"
DOCS = ROOT / "docs"
CNAME = DOCS / "CNAME"

# Every file that may carry an absolute site URL.
TARGETS = ["index.html", "portfolio/index.html", "sitemap.xml"]


def load():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def save(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rewrite(path, old_base, new_base, code, verify):
    """Return (text, [what changed]) for one served file."""
    text = path.read_text(encoding="utf-8")
    changed = []

    if old_base != new_base:
        n = text.count(old_base)
        if n:
            text = text.replace(old_base, new_base)
            changed.append(f"{n} absolute URL(s) -> {new_base}")

    # analytics: the data attribute is the only thing that varies
    if code is not None:
        before = text
        text = re.sub(
            r'(data-goatcounter=")[^"]*(")',
            lambda m: m.group(1) + (f"https://{code}.goatcounter.com/count" if code else "") + m.group(2),
            text,
        )
        if text != before:
            changed.append(f"analytics code -> {code or '(unset)'}")

    # badge link
    if verify is not None:
        before = text
        text = re.sub(
            r'(<a class="grad-badge"[^>]*?href=")[^"]*(")',
            lambda m: m.group(1) + (verify or "#badge-not-configured") + m.group(2),
            text,
        )
        if text != before:
            changed.append("badge verify link updated")

    return text, changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="canonical base URL, no trailing slash")
    ap.add_argument("--go-live", action="store_true", help="use base_url_target from site.json")
    ap.add_argument("--analytics", help="GoatCounter site code")
    ap.add_argument("--verify", help="badge verification URL")
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    cfg = load()
    old_base = cfg["base_url"].rstrip("/")

    new_base = old_base
    if args.go_live:
        new_base = cfg["base_url_target"].rstrip("/")
    if args.base:
        new_base = args.base.rstrip("/")

    code = args.analytics if args.analytics is not None else cfg.get("goatcounter_code", "")
    verify = args.verify if args.verify is not None else cfg.get("badge_verify_url", "")

    if not new_base.startswith("https://"):
        sys.exit(f"base URL must start with https:// — got {new_base!r}")

    print(f"base     {old_base}" + (f"  ->  {new_base}" if new_base != old_base else "  (unchanged)"))
    print(f"analytics {code or '(unset — no analytics will load)'}")
    print(f"badge    {verify or '(unset — badge link is a placeholder)'}")
    print()

    dirty = False
    for rel in TARGETS:
        path = DOCS / rel
        if not path.exists():
            print(f"  skip {rel} (missing)")
            continue
        text, changed = rewrite(path, old_base, new_base, code, verify)
        if changed:
            dirty = True
            print(f"  {rel}: " + "; ".join(changed))
            if not args.check:
                path.write_text(text, encoding="utf-8")
        else:
            print(f"  {rel}: already current")

    # The paper's URL is a required deliverable: exactly one line, and it has to
    # follow the site to its new address.
    paper_url = ROOT / "submission" / "paper_url.txt"
    want = f"{new_base}/\n"
    print()
    if paper_url.read_text() != want:
        print(f"  submission/paper_url.txt: -> {new_base}/")
        if not args.check:
            paper_url.write_text(want, encoding="utf-8")
        dirty = True
    else:
        print("  submission/paper_url.txt: already current")

    # CNAME tells GitHub Pages which host to serve. It must NOT exist until DNS
    # for that host actually resolves — otherwise Pages serves the custom host
    # (404) and redirects the github.io address to it, taking the site down.
    host = new_base.split("://", 1)[1].split("/", 1)[0]
    on_github_pages = host.endswith("github.io")
    print()
    if on_github_pages:
        if CNAME.exists():
            print(f"  CNAME: removing (base is {host}, no custom domain)")
            if not args.check:
                CNAME.unlink()
            dirty = True
        else:
            print("  CNAME: absent, correct for a github.io base")
    else:
        want = host + "\n"
        if not CNAME.exists() or CNAME.read_text() != want:
            print(f"  CNAME: writing {host}")
            if not args.check:
                CNAME.write_text(want, encoding="utf-8")
            dirty = True
        else:
            print(f"  CNAME: already {host}")

    if not args.check:
        cfg["base_url"] = new_base
        cfg["goatcounter_code"] = code
        cfg["badge_verify_url"] = verify
        save(cfg)

    print()
    if args.check:
        print("CHECK ONLY — nothing written." if dirty else "CHECK ONLY — already in sync.")
    else:
        print("site.json applied." if dirty else "Nothing to change; already in sync.")


if __name__ == "__main__":
    main()
