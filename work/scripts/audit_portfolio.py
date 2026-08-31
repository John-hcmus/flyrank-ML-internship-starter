import pathlib, re, sys

html = pathlib.Path("docs/portfolio/index.html").read_text(encoding="utf-8")
issues = []

# --- links ---
anchors = re.findall(r'<a\s[^>]*href="([^"]+)"[^>]*>', html)
ids = set(re.findall(r'\sid="([^"]+)"', html))
for h in anchors:
    if h == "#":
        issues.append(f"DEAD LINK: href='#'")
    elif h.startswith("#") and h[1:] not in ids:
        issues.append(f"BROKEN ANCHOR: {h} has no matching id")
print(f"links: {len(anchors)} total, {len(set(a for a in anchors if a.startswith('http')))} external")

# external links must be safe
for m in re.finditer(r'<a\s([^>]*target="_blank"[^>]*)>', html):
    if "rel=" not in m.group(1) or "noopener" not in m.group(1):
        issues.append(f"target=_blank without rel=noopener: {m.group(1)[:70]}")

# --- images ---
imgs = re.findall(r'<img\s', html)
print(f"images: {len(imgs)} (none = nothing to break, nothing slow to load)")

# --- external requests ---
ext = set(re.findall(r'https://([a-z0-9.-]+)/', html))
print("external hosts:", ", ".join(sorted(ext)))

# --- contrast ---
def lum(hexcol):
    c = hexcol.lstrip("#")
    rgb = [int(c[i:i+2], 16)/255 for i in (0, 2, 4)]
    rgb = [v/12.92 if v <= 0.03928 else ((v+0.055)/1.055)**2.4 for v in rgb]
    return 0.2126*rgb[0] + 0.7152*rgb[1] + 0.0722*rgb[2]

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

pairs = [
    ("body text",        "#18181b", "#fafaf9", 4.5),
    ("secondary text",   "#52525b", "#fafaf9", 4.5),
    ("muted text",       "#71717a", "#fafaf9", 4.5),
    ("muted on white",   "#71717a", "#ffffff", 4.5),
    ("accent link",      "#0369a1", "#fafaf9", 4.5),
    ("accent on white",  "#0369a1", "#ffffff", 4.5),
    ("white on accent",  "#ffffff", "#0369a1", 4.5),
    ("callout text",     "#0c4a6e", "#e0f2fe", 4.5),
    ("live badge",       "#15803d", "#f0fdf4", 4.5),
    ("error text",       "#b91c1c", "#fafaf9", 4.5),
    ("setup note",       "#92400e", "#fffbeb", 4.5),
    ("success status",   "#15803d", "#fafaf9", 4.5),
]
print("\ncontrast (WCAG AA needs 4.5:1 for body text):")
for name, fg, bg, need in pairs:
    r = ratio(fg, bg)
    ok = r >= need
    print(f"  {'ok  ' if ok else 'FAIL'} {name:18s} {r:5.2f}:1")
    if not ok:
        issues.append(f"CONTRAST: {name} is {r:.2f}:1, needs {need}:1")

print("\n" + ("=" * 50))
if issues:
    print(f"{len(issues)} ISSUE(S):")
    for i in issues:
        print("  -", i)
    sys.exit(1)
print("NO ISSUES FOUND")
