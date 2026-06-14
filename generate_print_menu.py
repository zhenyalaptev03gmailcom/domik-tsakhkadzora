# -*- coding: utf-8 -*-
"""Пересборка печатного меню-книги menu-print.html для «Домик Цахкадзора».
Выдаёт ПЛОСКИЙ поток элементов в #book; постранично по A4 раскладывает
js/print-paginate.js (экран = печать). Данные кухни — из data/menu.json,
барная карта — из menu.html (#menu-bar). Стиль — css/print-menu.css (не трогаем).
Запуск:  python generate_print_menu.py
"""
import re, io, json, sys
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r"C:\общее\domik-tsakhkadzora"

# ---------- обложка (отдельный лист, .book-cover распознаёт пагинатор) ----------
COVER_HTML = '''<div class="book-cover">
  <div class="book-cover__frame"></div>
  <div class="book-cover__corners" aria-hidden="true">
    <span></span><span></span><span></span><span></span>
  </div>
  <div class="book-cover__inner">
    <svg class="book-cover__house" viewBox="0 -6 240 82" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DoMik">
      <path d="M44 22 120 -4 196 22"/>
      <path d="M158 10V-2h6v12"/>
    </svg>
    <div class="book-cover__wordmark"><b>Do</b>Mik</div>
    <div class="book-cover__sub">Ресторан Цахкадзора</div>
    <div class="book-cover__rule" aria-hidden="true"><span>&#9670;</span></div>
    <div class="book-cover__menu">Меню</div>
    <div class="book-cover__diamonds" aria-hidden="true">&#9670;&nbsp;&#9670;&nbsp;&#9670;</div>
  </div>
  <div class="book-cover__foot">
    Цахкадзор, ул.&nbsp;Хачатура&nbsp;Кечареци&nbsp;6 &nbsp;&middot;&nbsp; <b>+374&nbsp;95&nbsp;505&nbsp;656</b> &nbsp;&middot;&nbsp; ежедневно&nbsp;11:00&ndash;23:00
  </div>
</div>'''

# плоские «флоу»-элементы. .flow-keep = не отрывать от следующего (заголовки/баннер)
CAT_TITLE = '<h2 class="book-cat__title flow-keep"><span class="dia">&#9670;</span>{{TITLE}}<span class="dia">&#9670;</span></h2>'

DISH_TPL = '''<article class="book-dish">
  <div class="book-dish__head">
    <span class="book-dish__name">{{NAME}}</span>
    <span class="book-dish__leader"></span>
    <span class="book-dish__price">{{PRICE}}</span>
  </div>
  <p class="book-dish__desc">{{DESC}}</p>
</article>'''

BAR_PART = '''<section class="bar-part flow-keep">
  <div class="bar-part__frame"></div>
  <div class="bar-part__inner">
    <div class="bar-part__diamonds" aria-hidden="true">&#9670;&nbsp;&#9670;&nbsp;&#9670;</div>
    <h2 class="bar-part__title">Барная&nbsp;карта</h2>
    <div class="bar-part__sub">Напитки и коктейли</div>
  </div>
</section>'''

BAR_SEC_TITLE = '<h3 class="bar-sec__title flow-keep"><span class="dia">&#9670;</span>{{TITLE}}<span class="dia">&#9670;</span></h3>'

BAR_ROW_TPL = '''<div class="bar-row">
  <span class="bar-row__name">{{NAME}}</span><span class="bar-row__vol">{{VOL}}</span>
  <span class="bar-row__leader"></span>
  <span class="bar-row__price">{{PRICE}}</span>
</div>'''

TOOLBAR = '''<div class="book-toolbar" aria-hidden="true">
  <a href="menu.html">&larr;&nbsp;К меню сайта</a>
  <button type="button" onclick="window.print()">Распечатать / PDF</button>
</div>'''

HEAD = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Меню книгой — Домик Цахкадзора</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/print-menu.css?v=3">
<meta name="description" content="Печатное меню ресторана «Домик Цахкадзора» — книгой, для печати и сохранения в PDF.">
<meta name="robots" content="noindex, follow">
<meta name="theme-color" content="#f6efdd">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="img/favicon-32.png">
<link rel="apple-touch-icon" href="img/favicon-180.png">
</head>
<body>'''

SCRIPT = '<script src="js/print-paginate.js?v=2"></script>'


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def price_kitchen(p):
    p = p.strip()
    if any(ch.isdigit() for ch in p):
        return f'{esc(p)} <span class="cur">֏</span>'
    return esc(p)  # нечисловая цена (напр. «уточняйте») — без символа ֏

def price_bar(p):
    p = p.strip()
    if p.endswith('֏'):
        return f'{p[:-1].rstrip()} <span class="cur">֏</span>'
    return p

def fill(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace('{{' + k + '}}', v)
    return tpl


parts = [COVER_HTML]

# ---------- кухня из menu.json ----------
data = json.load(io.open(ROOT + r"\data\menu.json", encoding='utf-8'))
cats = data if isinstance(data, list) else data['categories']
dish_count = 0
for c in cats:
    parts.append(fill(CAT_TITLE, TITLE=esc(c.get('name', '').strip())))
    for it in c.get('items', []):
        parts.append(fill(DISH_TPL,
                          NAME=esc(it.get('name', '').strip()),
                          DESC=esc((it.get('composition') or '').strip()),
                          PRICE=price_kitchen(it.get('price', ''))))
        dish_count += 1
print("kitchen categories:", len(cats), "| dishes:", dish_count)

# ---------- барная карта из menu.html ----------
parts.append(BAR_PART)
mh = io.open(ROOT + r"\menu.html", encoding='utf-8').read()
start = mh.find('class="bar-list"')
foot = mh.find('<footer', start)
region = mh[max(0, start - 400): foot if foot > 0 else len(mh)]
BLOCK = {"основное меню", "меню", "бар", "барная карта", "напитки и бар"}
heads = [(m.start(), re.sub('<.*?>', '', m.group(1)).strip())
         for m in re.finditer(r'<h[234][^>]*>(.*?)</h[234]>', region, re.S)]
bar_secs, bar_rows_total = 0, 0
for m in re.finditer(r'<ul class="bar-list">', region):
    u = m.start()
    cand = [t for p, t in heads if p < u and t.lower() not in BLOCK]
    title = cand[-1] if cand else '—'
    ulhtml = region[u:region.find('</ul>', u)]
    parts.append(fill(BAR_SEC_TITLE, TITLE=title))
    for name_raw, price in re.findall(
            r'<span class="bar-item__name">(.*?)</span>\s*<span class="bar-item__price">(.*?)</span>',
            ulhtml, re.S):
        ms = re.search(r'<small>(.*?)</small>', name_raw, re.S)
        vol = ms.group(1).strip() if ms else ''
        name = re.sub(r'\s+', ' ', re.sub(r'<small>.*?</small>', '', name_raw, flags=re.S)).strip()
        parts.append(fill(BAR_ROW_TPL, NAME=name, VOL=vol, PRICE=price_bar(price)))
        bar_rows_total += 1
    bar_secs += 1
print("bar sections:", bar_secs, "| bar rows:", bar_rows_total)
assert bar_secs == 18 and bar_rows_total == 142, "bar parse mismatch!"

# ---------- сборка ----------
out = (HEAD + "\n" + TOOLBAR + '\n<div id="book" class="book">\n'
       + "\n".join(parts) + "\n"
       + "</div>\n" + SCRIPT + "\n</body>\n</html>\n")
io.open(ROOT + r"\menu-print.html", 'w', encoding='utf-8').write(out)
print("menu-print.html written:", len(out), "chars")
