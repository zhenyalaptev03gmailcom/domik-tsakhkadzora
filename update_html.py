#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, re

sel = json.load(open("selection.json", encoding="utf-8"))
gal = sel["gallery"]

def read(p):  return open(p, "r", encoding="utf-8", newline="").read()
def write(p,s): open(p, "w", encoding="utf-8", newline="").write(s)

# ── gallery.html: 24 фигуры + page-gallery cache-bust ──
g = read("gallery.html")
figs = []
for i, it in enumerate(gal, 1):
    cap = it["caption"].replace('"', "&quot;")
    figs.append(
        f'<figure class="gallery-item"><picture><source srcset="img/gallery-{i}.webp?v=4" '
        f'type="image/webp"><img src="img/gallery-{i}.jpg?v=4" alt="{cap}" width="1200" '
        f'height="800" loading="lazy" decoding="async"></picture></figure>')
block = "\r\n".join(figs) + "\r\n"
g2 = re.sub(r'(?:<figure class="gallery-item">.*?</figure>\r?\n)+', block, g, count=1)
assert g2 != g and f'gallery-{len(gal)}.jpg' in g2, "gallery figures not replaced"
g2 = g2.replace("img/page-gallery.jpg'", "img/page-gallery.jpg?v=2'") \
       .replace('img/page-gallery.jpg"', 'img/page-gallery.jpg?v=2"')
write("gallery.html", g2)

# ── перенаправление героев ──
def swap(path, a, b):
    s = read(path); assert a in s, f"{a} not in {path}"; write(path, s.replace(a, b))

swap("contacts.html", "img/gallery-8.jpg?v=3",  "img/bg-contacts.jpg?v=1")
swap("reviews.html",  "img/gallery-14.jpg?v=3", "img/bg-reviews.jpg?v=1")
swap("events.html",   "img/team-hall.jpg?v=2",  "img/team-hall.jpg?v=3")
swap("index.html",    "img/hero-poster.jpg?v=2","img/hero-poster.jpg?v=3")
swap("404.html",      "img/hero-bg.jpg",        "img/hero-bg.jpg?v=2")

# ── style.css: hero-bg cache-bust ──
c = read("css/style.css")
c = c.replace("../img/hero-bg.jpg",  "../img/hero-bg.jpg?v=2") \
     .replace("../img/hero-bg.webp", "../img/hero-bg.webp?v=2")
write("css/style.css", c)

# ── bump style.css?v=54 -> 55 во всех html ──
import glob
n = 0
for p in glob.glob("*.html"):
    s = read(p)
    if "style.css?v=54" in s:
        write(p, s.replace("style.css?v=54", "style.css?v=55")); n += 1
print(f"gallery.html: {len(gal)} фигур; герои перенаправлены; hero-bg busted; style.css?v=55 в {n} файлах")
