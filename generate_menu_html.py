#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Регенерирует #menu-food в menu.html и бандл #domik-menu-bundle в dish.html из data/menu.json.
Поддержка: подзаголовки (sub), двойные порции (sizes), note у раздела, карточки без фото.
"""
import json, re, html, os

ROOT = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(ROOT, *a)

MENU = json.load(open(P("data","menu.json"), encoding="utf-8"))
try:
    STORIES = json.load(open(P("data","dish-stories.json"), encoding="utf-8"))
except Exception:
    STORIES = {}

def esc(s): return html.escape(str(s), quote=True)

NOTE_TR = {
    "На выбор вид пасты: феттучини, спагетти, пенне":
        ("Choose your pasta: fettuccine, spaghetti, penne",
         "Ընտրեք մակարոնի տեսակը՝ ֆետուչինի, սպագետի, պենne"),
}

def webp_of(local):
    return re.sub(r"\.jpg(\?|$)", r".webp\1", local)

def price_html(price):
    # нечисловую цену («уточняйте») рендерим без ֏
    if re.search(r"\d", str(price)):
        return f"{esc(price)} ֏"
    return esc(price)

def card(it, delay):
    cid = esc(it["id"]); name = esc(it["name"])
    cls = "menu-card menu-card--link"
    has = it.get("local_image")
    if not has:
        cls += " menu-card--noimg"
    aria = f'{name} — {price_html(it.get("price",""))}'
    parts = [f'<a href="dish.html?id={cid}" class="{cls}" data-dish-id="{cid}" '
             f'style="transition-delay:{delay:.2f}s" aria-label="{aria}">']
    if has:
        jpg = esc(it["local_image"]); wp = esc(webp_of(it["local_image"]))
        parts.append(f'<picture><source srcset="{wp}" type="image/webp">'
                     f'<img src="{jpg}" alt="{name}" width="800" height="600" '
                     f'loading="lazy" decoding="async"></picture>')
    else:
        parts.append('<div class="menu-card__ph" aria-hidden="true"><span>DoMik</span></div>')
    # имя с переводами (если есть)
    tr = ""
    if it.get("name_en"): tr += f' data-tr-en="{esc(it["name_en"])}"'
    if it.get("name_hy"): tr += f' data-tr-hy="{esc(it["name_hy"])}"'
    size = ""
    if it.get("sizes"):
        size = f'<span class="menu-card__size">{esc(it["sizes"])}</span>'
    parts.append('<div class="menu-card__body">'
                 f'<span class="menu-card__name"{tr}>{name}</span>'
                 f'{size}<span class="price">{price_html(it.get("price",""))}</span>'
                 '</div></a>')
    return "".join(parts)

def grid(items):
    out = ['<div class="menu-grid">']
    for i, it in enumerate(items):
        out.append("        " + card(it, min(0.25, i * 0.05)))
    out.append("        </div>")
    return "\n".join(out)

# ── nav ──
nav = ['<nav class="menu-nav container" aria-label="Разделы меню">']
for i, c in enumerate(MENU):
    tr = ""
    if c.get("name_en"): tr += f' data-tr-en="{esc(c["name_en"])}"'
    if c.get("name_hy"): tr += f' data-tr-hy="{esc(c["name_hy"])}"'
    nav.append(f'  <a href="#cat-{i}" class="menu-tab" data-category="cat-{i}"{tr}>{esc(c["name"])}</a>')
nav.append('</nav>')
nav_html = "\n".join(nav)

# ── категории ──
secs = []
for i, c in enumerate(MENU):
    tr = ""
    if c.get("name_en"): tr += f' data-tr-en="{esc(c["name_en"])}"'
    if c.get("name_hy"): tr += f' data-tr-hy="{esc(c["name_hy"])}"'
    s = [f'      <section class="menu-category" id="cat-{i}" data-category="cat-{i}">',
         f'        <h3{tr}>{esc(c["name"])}</h3>']
    if c.get("note"):
        ntr = ""
        en_hy = NOTE_TR.get(c["note"])
        if en_hy:
            ntr = f' data-tr-en="{esc(en_hy[0])}" data-tr-hy="{esc(en_hy[1])}"'
        s.append(f'        <p class="menu-cat-note"{ntr}>{esc(c["note"])}</p>')
    # разбиваем на грид-ряды по подзаголовкам
    rows = []  # список (sub_or_None, [items])
    cur = (None, [])
    for it in c["items"]:
        if it.get("hidden"):        # стоп-лист: сегодня нет в наличии — не показываем
            continue
        if "sub" in it:
            if cur[1]: rows.append(cur)
            rows.append((it, []))   # маркер подзаголовка, отдельно
            cur = (None, [])
        else:
            cur[1].append(it)
    if cur[1]: rows.append(cur)
    for marker, items in rows:
        if marker is not None and "sub" in marker:
            stt = ""
            if marker.get("sub_en"): stt += f' data-tr-en="{esc(marker["sub_en"])}"'
            if marker.get("sub_hy"): stt += f' data-tr-hy="{esc(marker["sub_hy"])}"'
            s.append(f'        <h4 class="menu-subcat"{stt}>{esc(marker["sub"])}</h4>')
        if items:
            s.append("        " + grid(items))
    s.append('      </section>')
    secs.append("\n".join(s))

food_inner = (nav_html + "\n<div class=\"menu-page-wrap\">\n  <div class=\"container menu-page\">\n"
              + "\n".join(secs) + "\n  </div>\n</div>")
food_block = '<div id="menu-food">\n' + food_inner + "\n</div>\n"

# ── вставка в menu.html ──
mh = open(P("menu.html"), "r", encoding="utf-8", newline="").read()
a = mh.index('<div id="menu-food">')
b = mh.index('<div id="menu-bar"')
mh2 = mh[:a] + food_block + mh[b:]
open(P("menu.html"), "w", encoding="utf-8", newline="").write(mh2)

# ── чистим служебные ключи для бандла ──
def clean(cat):
    cc = {k: v for k, v in cat.items() if not k.startswith("_")}
    cc["items"] = [{k: v for k, v in it.items() if not k.startswith("_")}
                   for it in cat["items"] if not it.get("hidden")]
    return cc
bundle = {"categories": [clean(c) for c in MENU]}
# истории — только для существующих id
ids = {it["id"] for c in MENU for it in c["items"] if "id" in it}
bundle["stories"] = {k: v for k, v in STORIES.items() if k in ids} if isinstance(STORIES, dict) else {}

dh = open(P("dish.html"), "r", encoding="utf-8", newline="").read()
dh2 = re.sub(r'(<script id="domik-menu-bundle" type="application/json">).*?(</script>)',
             lambda m: m.group(1) + json.dumps(bundle, ensure_ascii=False) + m.group(2),
             dh, count=1, flags=re.DOTALL)
open(P("dish.html"), "w", encoding="utf-8", newline="").write(dh2)

ncards = sum(1 for c in MENU for it in c["items"] if "sub" not in it)
nnoimg = sum(1 for c in MENU for it in c["items"] if "sub" not in it and not it.get("local_image"))
print(f"menu.html: {len(MENU)} разделов, {ncards} карточек ({nnoimg} без фото); бандл обновлён, историй {len(bundle['stories'])}")
