#!/usr/bin/env python3
"""Check that every internal link and asset in the built pages points at a real file."""
import pathlib, re, sys, urllib.parse
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
for page in ROOT.rglob("*.html"):
    if ".git" in page.parts:
        continue
    text = page.read_text(encoding="utf-8")
    ids = set(re.findall(r'id="([^"]+)"', text))
    for ref in re.findall(r'(?:href|src)="([^"]+)"', text):
        if ref.startswith(("http://", "https://", "mailto:", "data:")):
            continue
        u = urllib.parse.urlparse(ref)
        if not u.path:
            if u.fragment and u.fragment not in ids and not u.fragment.startswith("call-"):
                print(f"{page.relative_to(ROOT)}: missing anchor #{u.fragment}"); bad += 1
            continue
        target = (ROOT / u.path.lstrip("/")) if u.path.startswith("/") else (page.parent / u.path)
        if target.is_dir() or u.path.endswith("/"):
            target = target / "index.html"
        if not target.exists():
            print(f"{page.relative_to(ROOT)}: broken link {ref}"); bad += 1
print("0 broken links" if not bad else f"{bad} broken links")
sys.exit(1 if bad else 0)
