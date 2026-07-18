# -*- coding: utf-8 -*-
"""Пересборка печатного меню-книги menu-print.html для «Домик Цахкадзора».
Выдаёт ПЛОСКИЙ поток элементов в #book; постранично по A4 раскладывает
js/print-paginate.js (экран = печать).
Кухня — из data/print-menu.json (curated, ОТВЯЗАНА от сайта; правится напрямую).
Барная карта — из menu.html (#menu-bar): раздел «К пиву» вынесен в кухню,
безалкогольные напитки идут первыми, карта начинается с нового листа.
Запуск:  python generate_print_menu.py
"""
import re, io, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.abspath(__file__))

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

# подзаголовок-подраздел внутри раздела (напр. «Пицца», «Бургеры») — мельче заголовка
SUBCAT_TITLE = '<h3 class="book-subcat flow-keep"><span class="dia">&#9670;</span>{{TITLE}}<span class="dia">&#9670;</span></h3>'

DISH_TPL = '''<article class="book-dish">
  <div class="book-dish__head">
    <span class="book-dish__name">{{NAME}}</span>
    <span class="book-dish__leader"></span>
    <span class="book-dish__price">{{PRICE}}</span>
  </div>
  <p class="book-dish__desc">{{DESC}}</p>
</article>'''

# Барная карта начинается с нового листа: .book-break
BAR_PART = '''<section class="bar-part flow-keep book-break">
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
<link rel="stylesheet" href="css/print-menu.css?v=10">
<style>
  .book-dish__name .dish-size{font-weight:400;font-style:italic;opacity:.6;font-size:.8em;margin-left:.45em;letter-spacing:.02em}
  .book-cat__note{text-align:center;font-style:italic;font-size:.84rem;letter-spacing:.03em;color:#8f6f3e;margin:-.55rem 0 1.1rem}
  .book-subcat{font-family:'Cormorant Garamond',serif;font-weight:600;font-size:14pt;letter-spacing:.14em;text-transform:uppercase;color:#8f6f3e;text-align:center;margin:7mm 0 4.5mm;display:flex;align-items:center;justify-content:center;gap:4mm}
  .book-subcat .dia{flex:0 0 auto;color:#b08d4e;font-size:7pt}
  .book-subcat::before,.book-subcat::after{content:"";flex:0 0 12mm;height:0;border-top:.8px solid #cdb88e}
</style>
<meta name="description" content="Печатное меню ресторана «Домик Цахкадзора» — книгой, для печати и сохранения в PDF.">
<meta name="robots" content="noindex, follow">
<meta name="theme-color" content="#f0e3c6">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="img/favicon-32.png">
<link rel="apple-touch-icon" href="img/favicon-180.png">
</head>
<body>'''

SCRIPT = '<script src="js/print-paginate.js?v=6"></script>'


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def price_kitchen(p):
    p = (p or '').strip()
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


# ============================================================
#  КАТАЛОГ-РАЗВОРОТЫ — журнальные фото-страницы между группами
# ============================================================
# Карта «имя блюда -> фото» из сайтового menu.json (там реальные фото).
try:
    _site = json.load(io.open(os.path.join(ROOT, "data", "menu.json"), encoding='utf-8'))
    DISH_PHOTO = {it["name"].strip(): it["local_image"]   # с ?v — кэш-бастинг и в книге
                  for c in _site for it in c.get("items", [])
                  if it.get("local_image")}
except Exception:
    DISH_PHOTO = {}

# before — раздел, ПЕРЕД которым вставляется разворот (открывает главу).
# bg — полностраничный атмосферный фон (img/print/catalog-N.jpg).
# dishes — блюда для коллажа (фото тянутся из menu.json по имени).
CATALOGS = [
    {"before": "Завтрак", "bg": "img/print/catalog-1.jpg",
     "title": "Начало трапезы",
     "cats": ["Завтрак", "Закуски", "Салаты", "Суп"],
     "dishes": ["Французский завтрак", "Английский завтрак", "Панкейк с нутеллой",
                "Фирменная бурата", "Салат Домик", "Брускетта с томатами",
                "Греческий салат", "Салат капрезе", "Томатный крем суп"],
     "note": "Утро, лёгкие закуски и салаты"},
    {"before": "Паста", "bg": "img/print/catalog-2.jpg",
     "title": "Главные блюда",
     "cats": ["Паста", "Основные блюда", "От шеф-повара"],
     "dishes": ["Паста карбонара", "Паста четыре сыра", "Фирменный кебаб",
                "Пеппер стейк", "Долма", "Куриное филе по-французски",
                "Стейк рибай", "Домик", "Медуза"],
     "note": "Паста, мясо на углях и авторские сеты"},
    {"before": "Печь и гриль", "bg": "img/print/catalog-3.jpg",
     "title": "Огонь и море",
     "cats": ["Печь и гриль", "Рыба и морепродукты", "Армянские традиции"],
     "dishes": ["Пицца Пеперони", "Кесадилья с курицей", "Пицца Прошутто",
                "Хачапури аджарский", "Мидии", "Бургер гриль",
                "Паде мясной", "Стейк лосося", "Хаш"],
     "note": "С открытого огня, печи и тандыра"},
    {"before": "Гарниры", "bg": "img/print/catalog-4.jpg",
     "title": "Сладкая часть",
     "cats": ["Гарниры", "Детское меню", "Десерты", "Хлеб"],
     "dishes": ["Тирамису", "Чизкейк сан-себастьян", "Шоколадный вулкан",
                "Брауни", "Кокосовый тарт", "Яблочный пирог",
                "Гата армянская", "Фруктовый ассорти", "Мороженое"],
     "note": "Десерты, детям и к столу"},
]
CATALOG_BEFORE = {c["before"]: c for c in CATALOGS}

# Прощальный разворот (в КОНЦЕ книги) и барный (вместо кремового bar-part).
FAREWELL = {
    "bg": "img/print/catalog-welcome.jpg",
    "kicker": "Ресторан «Домик» · Цахкадзор",
    "title": "Ждём вас снова",
    "subtitle": "Спасибо, что были с нами",
    "dishes": ["Домик", "Стейк рибай", "Долма"],
    "note": "Цахкадзор, ул. Хачатура Кечареци 6 · +374 95 505 656",
}
BAR_SPREAD = {
    "bg": "img/print/catalog-bar.jpg",
    "kicker": "DoMik",
    "title": "Барная карта",
    "subtitle": "Вино · Коктейли · Кофе · Чай",
    "dishes": [],
    "note": "Напитки и авторские коктейли",
}

def render_catalog(cat):
    srcs = []
    for dn in cat.get("dishes", []):
        img = DISH_PHOTO.get(dn)
        if img:
            srcs.append((img, dn))
    photos = [f'<figure class="catalog__photo"><img src="{img}" alt="{esc(dn)}" loading="lazy"></figure>'
              for img, dn in srcs]
    # раскладка: >3 фото — редакционная мозаика (герой+лента+блок), 3 — аккуратный ряд
    photos_cls = "catalog__photos catalog__photos--" + ("mosaic" if len(srcs) > 3 else "trio")
    if cat.get("cats"):
        line = ' &#183; '.join(esc(c) for c in cat["cats"])
    else:
        line = esc(cat.get("subtitle", ""))
    cls = "catalog-spread" + ("" if photos else " catalog-spread--divider")
    photos_html = (f'<div class="{photos_cls}">' + ''.join(photos) + '</div>') if photos else ''
    return (f'<section class="{cls}">'
            f'<img class="catalog__bg" src="{cat["bg"]}" alt="" aria-hidden="true">'
            '<div class="catalog__overlay" aria-hidden="true"></div>'
            '<div class="catalog__frame" aria-hidden="true"></div>'
            '<div class="catalog__inner">'
            '<div class="catalog__top">'
            f'<div class="catalog__kicker">{esc(cat.get("kicker", "Меню · DoMik"))}</div>'
            f'<h2 class="catalog__title">{esc(cat["title"])}</h2>'
            '<div class="catalog__diamonds" aria-hidden="true">&#9670;&nbsp;&#9670;&nbsp;&#9670;</div>'
            f'<div class="catalog__cats">{line}</div>'
            '</div>'
            + photos_html +
            f'<div class="catalog__note">{esc(cat.get("note", ""))}</div>'
            '</div></section>')


parts = [COVER_HTML]   # обложка; первый разворот — «Начало трапезы» перед «Завтрак»

# ---------- кухня из curated data/print-menu.json ----------
pm = json.load(io.open(os.path.join(ROOT, "data", "print-menu.json"), encoding='utf-8'))
dish_count = 0
bar_placed = {}   # секции с "bar_after" рендерятся не в кухне, а в баре после указанного раздела
for sec in pm:
    if sec.get('bar_after'):
        bar_placed[sec['bar_after']] = sec
        continue
    if sec['name'] in CATALOG_BEFORE:            # журнальный разворот открывает главу
        parts.append(render_catalog(CATALOG_BEFORE[sec['name']]))
    if sec.get('page_break'):                    # раздел начинается с нового листа
        parts.append('<div class="book-break"></div>')
    parts.append(fill(CAT_TITLE, TITLE=esc(sec['name'].strip())))
    if sec.get('note'):
        parts.append('<p class="book-cat__note flow-keep">' + esc(sec['note'].strip()) + '</p>')
    for it in sec['items']:
        if it.get('break'):                     # принудительный разрыв листа
            parts.append('<div class="book-break"></div>')
            continue
        if it.get('sub'):                       # подзаголовок-подраздел
            parts.append(fill(SUBCAT_TITLE, TITLE=esc(it['sub'].strip())))
            continue
        name_html = esc(it['name'].strip())
        if it.get('sizes'):
            name_html += f' <span class="dish-size">{esc(it["sizes"].strip())}</span>'
        parts.append(fill(DISH_TPL,
                          NAME=name_html,
                          DESC=esc((it.get('desc') or '').strip()),
                          PRICE=price_kitchen(it.get('price', ''))))
        dish_count += 1
print("kitchen sections:", len(pm), "| dishes:", dish_count)

# ---------- барная карта из data/print-bar.json (ОТВЯЗАНА от сайта) ----------
# Порядок разделов задаётся самим print-bar.json (безалкогольное идёт первым).
# «К пиву» остаётся curated-разделом из print-menu.json и вставляется после «Пиво».
parts.append(render_catalog(BAR_SPREAD))   # фотографический барный разворот (вместо кремового)
bar = json.load(io.open(os.path.join(ROOT, "data", "print-bar.json"), encoding='utf-8'))
bar_rows_total = 0

def emit_curated_bar(sec):
    """Кухонная (curated) секция print-menu.json как раздел бара (К пиву)."""
    global bar_rows_total
    parts.append(fill(BAR_SEC_TITLE, TITLE=esc(sec['name'].strip())))
    for it in sec['items']:
        p = (it.get('price') or '').strip()
        if any(ch.isdigit() for ch in p):
            p = p + ' ֏'
        parts.append(fill(BAR_ROW_TPL, NAME=esc(it['name'].strip()), VOL='', PRICE=price_bar(p)))
        bar_rows_total += 1

for sec in bar:
    title = sec['section'].strip()
    parts.append(fill(BAR_SEC_TITLE, TITLE=esc(title)))
    for it in sec['items']:
        if it.get('sub'):                   # подзаголовок-подраздел внутри раздела бара
            parts.append(fill(SUBCAT_TITLE, TITLE=esc(it['sub'].strip())))
            continue
        p = (it.get('price') or '').strip()
        if any(ch.isdigit() for ch in p):
            p = p + ' ֏'
        parts.append(fill(BAR_ROW_TPL, NAME=esc(it['name'].strip()),
                          VOL=esc((it.get('vol') or '').strip()), PRICE=price_bar(p)))
        bar_rows_total += 1
    if title in bar_placed:                 # curated-раздел «К пиву» сразу после «Пиво»
        emit_curated_bar(bar_placed[title])

print("bar sections:", len(bar), "| bar rows:", bar_rows_total)

# ---------- прощальный разворот в самом конце книги ----------
parts.append(render_catalog(FAREWELL))

# ---------- сборка ----------
out = (HEAD + "\n" + TOOLBAR + '\n<div id="book" class="book">\n'
       + "\n".join(parts) + "\n"
       + "</div>\n" + SCRIPT + "\n</body>\n</html>\n")
io.open(os.path.join(ROOT, "menu-print.html"), 'w', encoding='utf-8').write(out)
print("menu-print.html written:", len(out), "chars")
