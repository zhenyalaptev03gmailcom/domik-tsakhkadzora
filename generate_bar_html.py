#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Регенерирует барную карту сайта (#menu-bar в menu.html) из data/print-bar.json
(+ раздел «К пиву» из print-menu.json, вставляется после «Пиво» — как в печатной книге).
Порядок разделов = порядок print-bar.json (безалкогольное вперёд), 1:1 с печатным.

Существующие EN/HY переводы названий/объёмов/разделов ПЕРЕНОСЯТСЯ из текущего
#menu-bar по совпадению русского текста; для новых позиций переводы берутся из ADD_*.
Объёмы («50 мл», «0,3 / 1 л» …) переводятся автоматически. Подзаголовки ({"sub"})
рендерятся как <li class="bar-subhead">.
"""
import json, re, html, os

ROOT = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(ROOT, *a)

esc = lambda s: html.escape(str(s), quote=True)

# ── переводы для НОВЫХ позиций (которых нет в текущем баре или отличается формулировка) ──
ADD_NAME = {
    "Острые куриные крылышки": ("Spicy chicken wings", "Կծու հավի թևիկներ"),
    "Немецкая закуска": ("German platter", "Գերմանական խորտիկ"),
    "Домашняя закуска": ("Home-style appetizer", "Տնական նախուտեստ"),
    "Домашняя рыбная закуска": ("Home-style fish appetizer", "Տնական ձկան նախուտեստ"),
    "Немецкий сет": ("German set", "Գերմանական սեթ"),
    "Свиная рулька": ("Pork knuckle", "Խոզի սրունք"),
    # Фирменные коктейли
    "Фирменный Домик": ("Signature Domik", "Ֆիրմային Դոմիկ"),
    "Фирменный Домина": ("Signature Domina", "Ֆիրմային Դոմինա"),
    # Домашние лимонады
    "Фирменный домик": ("Signature Domik", "Ֆիրմային Դոմիկ"),
    "Мандарин/апельсин-мята": ("Mandarin/orange-mint", "Մանդարին/նարինջ-անանուխ"),
    "Лайм-мята": ("Lime-mint", "Լայմ-անանուխ"),
    "Грейпфрут-базилик": ("Grapefruit-basil", "Գրեյպֆրուտ-ռեհան"),
    "Арбузный лимонад": ("Watermelon lemonade", "Ձմերուկի լիմոնադ"),
    "Клубника-базилик": ("Strawberry-basil", "Ելակ-ռեհան"),
    "Фирменный лимонад (облепиха/цитрус/фалерно/мохито)":
        ("Signature lemonade (sea buckthorn/citrus/falerno/mojito)",
         "Ֆիրմային լիմոնադ (չիչխան/ցիտրուս/ֆալերնո/մոխիտո)"),
    "Фирменный лимонад (облепиха/цитрус/фалерно/мохито/ягодный)":
        ("Signature lemonade (sea buckthorn/citrus/falerno/mojito/berry)",
         "Ֆիրմային լիմոնադ (չիչխան/ցիտրուս/ֆալերնո/մոխիտո/հատապտուղ)"),
    "Лимонад Домик (цитрусовый/лайм-мята/грейпфрут-базилик/арбузный/ягодный)":
        ("Domik lemonade (citrus/lime-mint/grapefruit-basil/watermelon/berry)",
         "Լիմոնադ «Դոմիկ» (ցիտրուս/լայմ-անանուխ/գրեյպֆրուտ-ռեհան/ձմերուկ/հատապտուղ)"),
    "Тан": ("Tan", "Թան"),
    "Meyron Areni": ("Meyron Areni", "Meyron Areni"),
    "Jose Cuervo (silver/gold)": ("Jose Cuervo (silver/gold)", "Jose Cuervo (silver/gold)"),
    "Jack Daniel's Honey": ("Jack Daniel's Honey", "Jack Daniel's Honey"),
    "Лимон с мятой": ("Lemon-mint", "Կիտրոն անանուխով"),
    "Лимонад Домик": ("Domik lemonade", "Լիմոնադ «Դոմիկ»"),
    "Фирменный лимонад": ("Signature lemonade", "Ֆիրմային լիմոնադ"),
    # Арарат по именам (Ани 7 лет, Ахтамар 10, Двин 10, Васпуракан 15, Наири 20)
    "Ararat 5 звёзд": ("Ararat 5 stars", "Արարատ 5 աստղ"),
    "Ararat Ани (7 лет)": ("Ararat Ani (7 y.o.)", "Արարատ Անի (7 տարեկան)"),
    "Ararat Ахтамар (10 лет)": ("Ararat Akhtamar (10 y.o.)", "Արարատ Ախթամար (10 տարեկան)"),
    "Ararat Васпуракан (15 лет)": ("Ararat Vaspurakan (15 y.o.)", "Արարատ Վասպուրական (15 տարեկան)"),
    "Ararat Двин (10 лет)": ("Ararat Dvin (10 y.o.)", "Արարատ Դվին (10 տարեկան)"),
    "Ararat Наири (20 лет)": ("Ararat Nairi (20 y.o.)", "Արարատ Նաիրի (20 տարեկան)"),
    # Кофе
    "Раф": ("Raf coffee", "Ռաֆ"),
    "Латте макиато": ("Latte macchiato", "Լատտե մակիատո"),   # в старом переводе были кириллические «к»
    "Айс латте": ("Iced latte", "Սառը լատտե"),
    "Бамбл": ("Bumble", "Բամբլ"),
    "Эспрессо тоник": ("Espresso tonic", "Էսպրեսո տոնիկ"),
    "Сироп (кокосовый, ванильный, апельсиновый, шоколадный, ореховый)":
        ("Syrup (coconut, vanilla, orange, chocolate, nut)",
         "Օշարակ (կոկոս, վանիլ, նարինջ, շոկոլադ, ընկույզ)"),
    # Вино
    "Просекко extra dry": ("Prosecco Extra Dry", "Պրոսեկկո Extra Dry"),
    "Просекко extra dry, бутылка": ("Prosecco Extra Dry, bottle", "Պրոսեկկո Extra Dry, շիշ"),
    "Takar (розе)": ("Takar (rosé)", "Takar (վարդագույն)"),
    # Водка
    "ODEVI (фруктовая водка)": ("ODEVI (fruit vodka)", "ODEVI (մրգային օղի)"),
    # Ром
    "Bacardi Black": ("Bacardi Black", "Bacardi Black"),
    # Шоты и горячее
    "Глинтвейн белый": ("White mulled wine", "Սպիտակ գլինտվեյն"),
    "Глинтвейн красный": ("Red mulled wine", "Կարմիր գլինտվեյն"),
}
ADD_SEC = {
    "Напитки": ("Beverages", "Ըմպելիքներ"),
    "Фреши и лимонады": ("Fresh juices & lemonades", "Թարմ հյութեր և լիմոնադներ"),
    "Домашние лимонады": ("Homemade lemonades", "Տնական լիմոնադներ"),
    "Кофе": ("Coffee", "Սուրճ"),
    "Молочные коктейли": ("Milkshakes", "Կաթնային կոկտեյլներ"),
    "Чай": ("Tea", "Թեյ"),
    "Пиво": ("Beer", "Գարեջուր"),
    "К пиву": ("Beer snacks", "Գարեջրի խորտիկ"),
    "Вино по бокалам": ("Wine by the glass", "Գինի բաժակով"),
    "Вино — красное": ("Red wine", "Կարմիր գինի"),
    "Вино — белое": ("White wine", "Սպիտակ գինի"),
    "Вино — розовое / игристое": ("Rosé / Sparkling", "Վարդագույն / փրփրուն"),
    "Виски": ("Whisky", "Վիսկի"),
    "Водка": ("Vodka", "Օղի"),
    "Коньяк (Арарат)": ("Cognac (Ararat)", "Կոնյակ (Արարատ)"),
    "Ликёры": ("Liqueurs", "Լիկյորներ"),
    "Текила": ("Tequila", "Տեկիլա"),
    "Ром": ("Rum", "Ռոմ"),
    "Джин": ("Gin", "Ջին"),
    "Коктейли": ("Cocktails", "Կոկտեյլներ"),
    "Шоты и горячее": ("Shots & hot drinks", "Շոթեր և տաք ըմպելիք"),
}
ADD_SUB = {
    "Горячий кофе": ("Hot coffee", "Տաք սուրճ"),
    "Холодный кофе": ("Cold coffee", "Սառը սուրճ"),
}

# ── переносим существующие переводы из текущего #menu-bar ──
mh = open(P("menu.html"), "r", encoding="utf-8", newline="").read()
start = mh.index('<div id="menu-bar" hidden>')
script_idx = mh.index('<script>', start)
old_bar = mh[start:script_idx]

def unesc(s):
    return html.unescape(s)

name_tr, vol_tr_map, sec_tr = {}, {}, {}
for en, hy, ru in re.findall(
        r'<span class="bar-name-t" data-tr-en="([^"]*)" data-tr-hy="([^"]*)">(.*?)</span>', old_bar):
    name_tr[unesc(ru)] = (unesc(en), unesc(hy))
for en, hy, ru in re.findall(
        r'<small data-tr-en="([^"]*)" data-tr-hy="([^"]*)">(.*?)</small>', old_bar):
    vol_tr_map[unesc(ru)] = (unesc(en), unesc(hy))
for en, hy, ru in re.findall(
        r'<h3 data-tr-en="([^"]*)" data-tr-hy="([^"]*)">(.*?)</h3>', old_bar):
    sec_tr[unesc(ru)] = (unesc(en), unesc(hy))

fallbacks = []

def tr_name(ru):
    if ru in ADD_NAME:      return ADD_NAME[ru]
    if ru in name_tr:       return name_tr[ru]
    fallbacks.append(("name", ru));  return (ru, ru)   # бренды и т.п. — как есть

def tr_sec(ru):
    if ru in sec_tr:        return sec_tr[ru]
    if ru in ADD_SEC:       return ADD_SEC[ru]
    fallbacks.append(("sec", ru));   return (ru, ru)

def tr_vol(ru):
    ru = ru.strip()
    if not ru:              return None
    if ru in vol_tr_map:    return vol_tr_map[ru]
    en = ru.replace("мл", "ml").replace("л", "l").replace("фреш", "fresh")
    hy = ru.replace("мл", "մլ").replace("л", "լ").replace("фреш", "թարմ հյութ")
    return (en, hy)

def price_html(p):
    p = (p or "").strip()
    if any(ch.isdigit() for ch in p):
        return esc(p) + " ֏"
    return esc(p)   # «уточняйте» — без символа

# ── данные ──
bar = json.load(open(P("data","print-bar.json"), encoding="utf-8"))
pm  = json.load(open(P("data","print-menu.json"), encoding="utf-8"))
kpivu = next((s for s in pm if s.get("bar_after") == "Пиво"), None)

# переводы подписей-составов (note) под строкой
NOTE_TR = {
    "Цитрусовый · лайм-мята · грейпфрут-базилик · арбузный · ягодный":
        ("Citrus · lime-mint · grapefruit-basil · watermelon · berry",
         "Ցիտրուս · լայմ-անանուխ · գրեյպֆրուտ-ռեհան · ձմերուկ · հատապտուղ"),
    "Облепиха · цитрус · фалерно · мохито · ягодный":
        ("Sea buckthorn · citrus · falerno · mojito · berry",
         "Չիչխան · ցիտրուս · ֆալերնո · մոխիտո · հատապտուղ"),
}

def emit_item(name, vol, price, note=""):
    en, hy = tr_name(name)
    vt = tr_vol(vol or "")
    small = ""
    if vt:
        small = f' <small data-tr-en="{esc(vt[0])}" data-tr-hy="{esc(vt[1])}">{esc(vol.strip())}</small>'
    note_html = ""
    if note:
        nen, nhy = NOTE_TR.get(note, (note, note))
        note_html = (f'<span class="bar-item__note" data-tr-en="{esc(nen)}" '
                     f'data-tr-hy="{esc(nhy)}">{esc(note)}</span>')
    return (f'          <li class="bar-item"><span class="bar-item__name">'
            f'<span class="bar-name-t" data-tr-en="{esc(en)}" data-tr-hy="{esc(hy)}">{esc(name)}</span>'
            f'{small}</span><span class="bar-item__price">{price_html(price)}</span>{note_html}</li>')

def emit_subhead(ru):
    en, hy = ADD_SUB.get(ru, (ru, ru))
    return f'          <li class="bar-subhead" data-tr-en="{esc(en)}" data-tr-hy="{esc(hy)}">{esc(ru)}</li>'

def emit_section(bid, title, rows):
    en, hy = tr_sec(title)
    out = [f'      <section class="menu-category bar-category" id="bcat-{bid}" data-category="bcat-{bid}">',
           f'        <h3 data-tr-en="{esc(en)}" data-tr-hy="{esc(hy)}">{esc(title)}</h3>',
           '        <ul class="bar-list">']
    out += rows
    out += ['        </ul>', '      </section>']
    return "\r\n".join(out), (bid, title, en, hy)

sections, navmeta = [], []
bid = 0
def add(title, rows):
    global bid
    sec, meta = emit_section(bid, title, rows)
    sections.append(sec); navmeta.append(meta); bid += 1

for sec in bar:
    rows = []
    for it in sec["items"]:
        if "sub" in it:
            rows.append(emit_subhead(it["sub"]))
        else:
            rows.append(emit_item(it["name"], it.get("vol", ""), it.get("price", ""), it.get("note", "")))
    add(sec["section"].strip(), rows)
    if sec["section"].strip() == "Пиво" and kpivu:      # «К пиву» сразу после «Пиво»
        krows = [emit_item(it["name"], "", it.get("price", "")) for it in kpivu["items"] if "sub" not in it]
        add("К пиву", krows)

# ── nav ──
nav = ['<nav class="menu-nav container" aria-label="Разделы бара">']
for b, title, en, hy in navmeta:
    nav.append(f'  <a href="#bcat-{b}" class="menu-tab" data-category="bcat-{b}" '
               f'data-tr-en="{esc(en)}" data-tr-hy="{esc(hy)}">{esc(title)}</a>')
nav.append('</nav>')

bar_block = ('<div id="menu-bar" hidden>\r\n'
             + "\r\n".join(nav) + '\r\n'
             + '<div class="menu-page-wrap">\r\n  <div class="container menu-page">\r\n'
             + "\r\n".join(sections) + '\r\n'
             + '  </div>\r\n</div>\r\n</div>\r\n')

mh2 = mh[:start] + bar_block + mh[script_idx:]
open(P("menu.html"), "w", encoding="utf-8", newline="").write(mh2)

ndish = sum(1 for s in bar for it in s["items"] if "sub" not in it) + (
    sum(1 for it in kpivu["items"] if "sub" not in it) if kpivu else 0)
print(f"#menu-bar перегенерирован: разделов {len(sections)}, позиций {ndish}")
if fallbacks:
    uniq = sorted(set(fallbacks))
    print(f"  переводы-фолбэки (RU=EN=HY, проверить — обычно бренды): {len(uniq)}")
    for kind, ru in uniq:
        print(f"    [{kind}] {ru}")
