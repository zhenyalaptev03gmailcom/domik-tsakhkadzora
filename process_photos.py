#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработка выбранных фото из ../../../rest под галерею и фоны.
Вход: selection.json  { "gallery":[{"file","caption"}...],
                        "heroes":{"home","page_gallery","contacts","reviews","events"} }
Выход: img/gallery-1..N.jpg/.webp (1200x800) + фоновые файлы (2000x1333) + img/hero-poster.jpg
"""
import os, json, sys
from PIL import Image, ImageOps

REST = "/Users/laptevevgenij/Desktop/Сайты/rest"
IMG  = "img"
GAL  = (1200, 800)      # 3:2 галерея
HERO = (2000, 1333)     # 3:2 фоны (полноэкранные)

def load(fn):
    im = Image.open(os.path.join(REST, fn))
    im = ImageOps.exif_transpose(im).convert("RGB")
    return im

def finish(im, size):
    im = ImageOps.fit(im, size, method=Image.LANCZOS, centering=(0.5, 0.5))
    im = ImageOps.autocontrast(im, cutoff=0.4)
    return im

def save(im, base, q_jpg=84, q_webp=82, webp=True):
    im.save(base + ".jpg", "JPEG", quality=q_jpg, optimize=True, progressive=True)
    if webp:
        im.save(base + ".webp", "WEBP", quality=q_webp, method=6)

def main():
    sel = json.load(open("selection.json", encoding="utf-8"))
    os.makedirs(IMG, exist_ok=True)
    # галерея
    gal = sel["gallery"]
    for i, item in enumerate(gal, 1):
        im = finish(load(item["file"]), GAL)
        save(im, os.path.join(IMG, f"gallery-{i}"))
    print(f"галерея: {len(gal)} фото -> gallery-1..{len(gal)}")
    # фоны
    H = sel["heroes"]
    mapping = {
        "home":         "hero-bg",
        "page_gallery": "page-gallery",
        "contacts":     "bg-contacts",
        "reviews":      "bg-reviews",
        "events":       "team-hall",
    }
    for key, base in mapping.items():
        im = finish(load(H[key]), HERO)
        save(im, os.path.join(IMG, base))
        print(f"фон {key}: {H[key]} -> {base}.jpg/.webp")
    # poster главной = тот же кадр, что hero-bg (jpg, без webp — poster видео)
    save(finish(load(H["home"]), HERO), os.path.join(IMG, "hero-poster"), webp=False)
    print("hero-poster.jpg = home")

if __name__ == "__main__":
    main()
