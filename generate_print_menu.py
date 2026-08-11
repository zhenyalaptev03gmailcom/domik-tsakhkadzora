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

# --no-bar: собрать книгу БЕЗ барной карты (пока бар не готов к печати).
# «К пиву» тогда рендерится обычным разделом кухни на своём месте.
NO_BAR = '--no-bar' in sys.argv
LANG = 'ru'
for _a in sys.argv:
    if _a.startswith('--lang='):
        LANG = _a.split('=',1)[1].strip().lower()
assert LANG in ('ru','en','hy'), 'lang must be ru|en|hy'

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
<link rel="stylesheet" href="css/print-menu.css?v=14">
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

# ============================================================
#  ПЕРЕВОДЫ (для --lang=en|hy): имена/составы из menu.json сайта,
#  пропуски — из SUPPLEMENT_*; разделы/UI — словари ниже.
# ============================================================
SITE_ITEM = {}
try:
    for _c in _site:
        for _it in _c.get("items", []):
            if _it.get("name"):
                SITE_ITEM[_it["name"].strip()] = _it
except Exception:
    pass

SUPPLEMENT_NAME = {
 "Фирменная бурата": ("Signature Burrata", "Ֆիրմային բուռատա"),
 "Блинчики с мясом": ("Crepes with Meat", "Բլիթներ մսով"),
 "Тако с курицей": ("Chicken Tacos", "Տակո հավով"),
 "Тако с креветками": ("Shrimp Tacos", "Տակո ծովախեցգետնով"),
 "Цезарь с креветками": ("Caesar with Shrimp", "Ցեզար ծովախեցգետնով"),
 "Домашний куриный суп": ("Homemade Chicken Soup", "Տնական հավի ապուր"),
 "Паста песто": ("Pasta Pesto", "Պաստա պեստո"),
 "Куриное филе по-французски": ("Chicken Fillet French-Style", "Հավի ֆիլե ֆրանսիական ձևով"),
 "Пеппер стейк": ("Pepper Steak", "Պեպպեր սթեյք"),
 "Солёные орехи": ("Salted Nuts", "Աղի ընկույզ"),
 "Домик": ("Domik", "Դոմիկ"),
 "Хачапури аджарский": ("Adjarian Khachapuri", "Աջարական խաչապուրի"),
 "Хачапури имеретинский": ("Imeretian Khachapuri", "Իմերեթական խաչապուրի"),
 "Хачапури мегрельский": ("Megrelian Khachapuri", "Մեգրելական խաչապուրի"),
 "Арбуз и дыня": ("Watermelon & Melon", "Ձմերուկ և սեխ"),
}
SUPPLEMENT_DESC = {
 "Французский завтрак": ("Croissants, jam, Nutella, European cheese", "Կրուասաններ, ջեմ, նուտելլա, եվրոպական պանիր"),
 "Английский завтрак": ("Sausages, fried eggs, bacon, beans, mushrooms", "Նրբերշիկ, տապակած ձու, բեկոն, լոբի, սունկ"),
 "Панкейк с нутеллой": ("Pancakes, Nutella", "Փանքեյքեր, նուտելլա"),
 "Круассан": ("Your choice: salmon, shrimp, avocado, pastrami or Nutella", "Ընտրությամբ՝ սաղմոն, ծովախեցգետին, ավոկադո, պաստրամի կամ նուտելլա"),
 "Фирменная бурата": ("Focaccia, tomato, burrata, greens mix", "Ֆոկաչա, լոլիկ, բուռատա, կանաչիների խառնուրդ"),
 "Мацун сцеженный": ("Strained matsun", "Քամած մածուն"),
 "Жареный сыр": ("Breaded fried cheese, sauce", "Պանիր պաքսիմատով, սոուս"),
 "Блинчики с мясом": ("Thin crepes with meat filling", "Բարակ բլիթներ մսի միջուկով"),
 "Тако с курицей": ("Tortillas, chicken, vegetables, sauce", "Տորտիլյա, հավ, բանջարեղեն, սոուս"),
 "Тако с креветками": ("Tortillas, shrimp, vegetables, sauce", "Տորտիլյա, ծովախեցգետին, բանջարեղեն, սոուս"),
 "Классическая бурата": ("Burrata, tomatoes, olive oil, greens mix", "Բուռատա, լոլիկ, ձիթապտղի յուղ, կանաչիներ"),
 "Цезарь с креветками": ("Shrimp, romaine, Parmesan, croutons, Caesar dressing", "Ծովախեցգետին, ռոմեն, պարմեզան, կրուտոններ, Ցեզար սոուս"),
 "Армянский салат с гранатовым соусом": ("Grilled veal, eggplant, plum, walnut, pomegranate sauce", "Գրիլի հորթի միս, սմբուկ, սալոր, ընկույզ, նռան սոուս"),
 "Домашний куриный суп": ("Chicken, noodles, vegetables", "Հավ, արիշտա, բանջարեղեն"),
 "Паста песто": ("Pesto sauce, Parmesan", "Պեստո սոուս, պարմեզան"),
 "Паста карбонара": ("Pasta, pancetta, cream, egg, Parmesan, black pepper", "Մակարոն, պանչետտա, սերուցք, ձու, պարմեզան, սև պղպեղ"),
 "Цыплёнок с овощами": ("Grilled chicken with vegetables", "Գրիլի ճուտ բանջարեղենով"),
 "Бефстроганов (курица / телятина)": ("Chicken or veal in cream sauce, rice or potatoes", "Հավ կամ հորթի միս սերուցքային սոուսում, բրինձ կամ կարտոֆիլ"),
 "Пеппер стейк": ("Steak with pepper sauce", "Սթեյք պղպեղի սոուսով"),
 "Баклажан фаршированный": ("With meat or vegetables", "Մսով կամ բանջարեղենով"),
 "Домик": ("Chicken and beef kebab, signature barbecue, vegetables · For 3–5 people", "Հավի և տավարի քյաբաբ, ֆիրմային խորոված, բանջարեղեն · 3–5 հոգու համար"),
 "Семейный домик": ("Large charcoal barbecue platter with vegetables · For 3–5 people", "Խորովածի մեծ տեսականի ածուխի վրա, բանջարեղեն · 3–5 հոգու համար"),
 "Фламинго": ("Chicken, chicken fillet, turkey, chicken wings, vegetables · For 3–5 people", "Ճուտ, հավի ֆիլե, հնդկահավ, հավի թևիկներ, բանջարեղեն · 3–5 հոգու համար"),
 "Немецкий сет": ("Assorted sausages, cheese balls, garlic bread, vegetables · For 3–5 people", "Նրբերշիկների տեսականի, պանրի գնդիկներ, սխտորով հաց, բանջարեղեն · 3–5 հոգու համար"),
 "Медуза": ("Trout, seafood, mussels, squid · For 3–5 people", "Իշխան, ծովամթերք, միդիա, կաղամար · 3–5 հոգու համար"),
 "Хачапури аджарский": ("Boat-shaped bread with cheese, egg and butter", "Նավակաձև խաչապուրի պանրով, ձվով և կարագով"),
 "Хачапури имеретинский": ("Closed, with cheese", "Փակ, պանրով"),
 "Хачапури мегрельский": ("Cheese inside and on top", "Պանիր՝ ներսում և վրան"),
 "Креветки": ("Regular shrimp 250 g or king prawns 200 g", "Սովորական ծովախեցգետին 250 գ կամ արքայական՝ 200 գ"),
 "Форель": ("Grilled rainbow trout", "Ծիածանագույն իշխան գրիլի վրա"),
 "Стейк лосося": ("Grilled salmon steak", "Սաղմոնի սթեյք գրիլի վրա"),
 "Овощи гриль": ("Mushrooms, eggplant, zucchini, pepper", "Սունկ, սմբուկ, դդմիկ, պղպեղ"),
 "Домашний хлеб": ("Fresh warm homemade bread", "Թարմ տաք տնական հաց"),
 "Шоколадный тарт": ("Chocolate tart", "Շոկոլադե տարտ"),
 "Фруктовый ассорти": ("Seasonal fresh fruit platter", "Սեզոնային թարմ մրգերի տեսականի"),
 "Немецкая закуска": ("Idaho potatoes, cheese balls, garlic bread", "Այդահո կարտոֆիլ, պանրի գնդիկներ, սխտորով հաց"),
}
SEC_TR = {
 "Завтрак": ("Breakfast", "Նախաճաշ"),
 "Закуски": ("Appetizers", "Նախուտեստներ"),
 "Горячие закуски": ("Hot Appetizers", "Տաք նախուտեստներ"),
 "Салаты": ("Salads", "Աղցաններ"),
 "Суп": ("Soup", "Ապուր"),
 "Паста": ("Pasta", "Մակարոնեղեն"),
 "Основные блюда": ("Main Dishes", "Հիմնական ուտեստներ"),
 "К пиву": ("Beer Snacks", "Գարեջրի խորտիկներ"),
 "Блюда от шеф-повара": ("Chef's Specials", "Շեֆ-խոհարարի ուտեստներ"),
 "Печь и гриль": ("Oven & Grill", "Փուռ և գրիլ"),
 "Жареная рыба и морепродукты": ("Fried Fish & Seafood", "Տապակած ձուկ և ծովամթերք"),
 "Армянские традиции": ("Armenian Traditions", "Հայկական ավանդույթներ"),
 "Гарниры": ("Sides", "Կողմնակի ուտեստներ"),
 "Детское меню": ("Kids' Menu", "Մանկական մենյու"),
 "Часть любви": ("Part of Love", "Սիրո մասը"),
 "Хлеб": ("Bread", "Հաց"),
}
SUB_TR = {
 "Пицца": ("Pizza", "Պիցցա"),
 "Хачапури": ("Khachapuri", "Խաչապուրի"),
 "Бургеры и сэндвичи": ("Burgers & Sandwiches", "Բուրգերներ և սենդվիչներ"),
 "Горячий кофе": ("Hot Coffee", "Տաք սուրճ"),
 "Холодный кофе": ("Cold Coffee", "Սառը սուրճ"),
}
SIZES_TR = {
 "1 кг": ("1 kg", "1 կգ"),
 "куриный / говяжий": ("chicken / beef", "հավի / տավարի"),
 "обычный / с бастурмой": ("regular / with basturma", "սովորական / բաստուրմայով"),
}
UI_TR = {
 "Барная карта": ("Bar List", "Բարային քարտ"),
 "Вино · Коктейли · Кофе · Чай": ("Wine · Cocktails · Coffee · Tea", "Գինի · Կոկտեյլներ · Սուրճ · Թեյ"),
 "Напитки и авторские коктейли": ("Drinks and signature cocktails", "Ըմպելիքներ և հեղինակային կոկտեյլներ"),
 "DoMik": ("DoMik", "DoMik"),
 "На выбор вид пасты: феттучини, спагетти, пенне": ("Choice of pasta: fettuccine, spaghetti, penne", "Ընտրությամբ մակարոն՝ ֆետուչինի, սպագետտի, պեննե"),
 "Начало трапезы": ("To Start", "Ճաշի սկիզբ"),
 "Главные блюда": ("Main Courses", "Հիմնական ուտեստներ"),
 "Огонь и море": ("Fire & Sea", "Կրակ և ծով"),
 "Сладкая часть": ("Sweet Part", "Քաղցր մաս"),
 "От шеф-повара": ("Chef's Specials", "Շեֆ-խոհարարից"),
 "Рыба и морепродукты": ("Fish & Seafood", "Ձուկ և ծովամթերք"),
 "Десерты": ("Desserts", "Աղանդեր"),
 "Утро, лёгкие закуски и салаты": ("Morning, light bites and salads", "Առավոտ, թեթև նախուտեստներ և աղցաններ"),
 "Паста, мясо на углях и авторские сеты": ("Pasta, charcoal-grilled meat and signature sets", "Մակարոնեղեն, ածխի վրա միս և հեղինակային սեթեր"),
 "С открытого огня, печи и тандыра": ("From open fire, oven and tandoor", "Բաց կրակից, փռից և թոնիրից"),
 "Десерты, детям и к столу": ("Desserts, for kids and for the table", "Աղանդեր, երեխաներին և սեղանին"),
 "Меню · DoMik": ("Menu · DoMik", "Մենյու · DoMik"),
 "Ресторан «Домик» · Цахкадзор": ("Domik Restaurant · Tsaghkadzor", "Ռեստորան «Դոմիկ» · Ծաղկաձոր"),
 "Ждём вас снова": ("See You Again", "Սպասում ենք կրկին"),
 "Спасибо, что были с нами": ("Thank you for dining with us", "Շնորհակալություն, որ մեզ հետ էիք"),
 "Цахкадзор, ул. Хачатура Кечареци 6 · +374 95 505 656": ("Tsaghkadzor, 6 Khachatur Kecharetsi St · +374 95 505 656", "Ծաղկաձոր, Խաչատուր Կեչառեցու փ. 6 · +374 95 505 656"),
}
# ── переводы барной карты: из сгенерированного #menu-bar в menu.html ──
BAR_NAME_TR, BAR_VOL_TR, BAR_SEC_TR, BAR_NOTE_TR = {}, {}, {}, {}
try:
    import html as _html
    _mh = io.open(os.path.join(ROOT, "menu.html"), encoding="utf-8").read()
    _seg = _mh[_mh.index('<div id="menu-bar"'):]
    _seg = _seg[:_seg.index('<script>')]
    for _en, _hy, _ru in re.findall(
            r'<span class="bar-name-t" data-tr-en="([^"]*)" data-tr-hy="([^"]*)">(.*?)</span>', _seg):
        BAR_NAME_TR[_html.unescape(_ru)] = (_html.unescape(_en), _html.unescape(_hy))
    for _en, _hy, _ru in re.findall(
            r'<small data-tr-en="([^"]*)" data-tr-hy="([^"]*)">(.*?)</small>', _seg):
        BAR_VOL_TR[_html.unescape(_ru)] = (_html.unescape(_en), _html.unescape(_hy))
    for _en, _hy, _ru in re.findall(
            r'<h3 data-tr-en="([^"]*)" data-tr-hy="([^"]*)">(.*?)</h3>', _seg):
        BAR_SEC_TR[_html.unescape(_ru)] = (_html.unescape(_en), _html.unescape(_hy))
    for _en, _hy, _ru in re.findall(
            r'<span class="bar-item__note" data-tr-en="([^"]*)" data-tr-hy="([^"]*)">(.*?)</span>', _seg):
        BAR_NOTE_TR[_html.unescape(_ru)] = (_html.unescape(_en), _html.unescape(_hy))
except Exception:
    pass

def _pick(pair):
    return pair[0] if LANG == 'en' else pair[1]
def T_ui(s):
    if LANG == 'ru' or not s: return s
    return _pick(UI_TR[s]) if s in UI_TR else s
def T_sec(s):
    if LANG == 'ru': return s
    if s in SEC_TR: return _pick(SEC_TR[s])
    return T_ui(s)
def T_sub(s):
    if LANG == 'ru': return s
    return _pick(SUB_TR[s]) if s in SUB_TR else s
def T_sizes(s):
    if LANG == 'ru' or not s: return s
    return _pick(SIZES_TR[s]) if s in SIZES_TR else s
def T_name(nm):
    if LANG == 'ru': return nm
    it = SITE_ITEM.get(nm.strip())
    key = 'name_en' if LANG == 'en' else 'name_hy'
    if it and it.get(key): return it[key]
    if nm.strip() in SUPPLEMENT_NAME: return _pick(SUPPLEMENT_NAME[nm.strip()])
    return nm
def T_desc(nm, desc):
    if LANG == 'ru' or not desc: return desc
    it = SITE_ITEM.get(nm.strip())
    key = 'composition_en' if LANG == 'en' else 'composition_hy'
    if it and it.get(key): return it[key]
    if nm.strip() in SUPPLEMENT_DESC: return _pick(SUPPLEMENT_DESC[nm.strip()])
    return desc
def T_bar_sec(ru):
    if LANG == 'ru': return ru
    if ru in BAR_SEC_TR: return _pick(BAR_SEC_TR[ru])
    return T_sec(ru)
def T_bar_name(ru):
    if LANG == 'ru': return ru
    if ru in BAR_NAME_TR: return _pick(BAR_NAME_TR[ru])
    return T_name(ru)
def T_bar_vol(ru):
    if LANG == 'ru' or not ru: return ru
    if ru in BAR_VOL_TR: return _pick(BAR_VOL_TR[ru])
    if LANG == 'en': return ru.replace("мл","ml").replace("л","l").replace("фреш","fresh")
    return ru.replace("мл","մլ").replace("л","լ").replace("фреш","թարմ հյութ")
def T_bar_note(ru):
    if LANG == 'ru' or not ru: return ru
    return _pick(BAR_NOTE_TR[ru]) if ru in BAR_NOTE_TR else ru

# before — раздел, ПЕРЕД которым вставляется разворот (открывает главу).
# bg — полностраничный атмосферный фон (img/print/catalog-N.jpg).
# dishes — блюда для коллажа (фото тянутся из menu.json по имени).
CATALOGS = [
    {"before": "Завтрак", "bg": "img/print/catalog-1.jpg",
     "title": "Начало трапезы",
     "cats": ["Завтрак", "Закуски", "Горячие закуски", "Салаты", "Суп"],
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
     "dishes": ["Пицца Пеперони", "Креветки", "Пицца Прошутто",
                "Хачапури аджарский", "Мидии", "Бургер гриль",
                "Паде", "Стейк лосося", "Хаш"],
     "note": "С открытого огня, печи и тандыра"},
    {"before": "Гарниры", "bg": "img/print/catalog-4.jpg",
     "title": "Сладкая часть",
     "cats": ["Гарниры", "Детское меню", "Хлеб", "Десерты"],
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
        line = ' &#183; '.join(esc(T_sec(c)) for c in cat["cats"])
    else:
        line = esc(T_ui(cat.get("subtitle", "")))
    cls = "catalog-spread" + ("" if photos else " catalog-spread--divider")
    photos_html = (f'<div class="{photos_cls}">' + ''.join(photos) + '</div>') if photos else ''
    return (f'<section class="{cls}">'
            f'<img class="catalog__bg" src="{cat["bg"]}" alt="" aria-hidden="true">'
            '<div class="catalog__overlay" aria-hidden="true"></div>'
            '<div class="catalog__frame" aria-hidden="true"></div>'
            '<div class="catalog__inner">'
            '<div class="catalog__top">'
            f'<div class="catalog__kicker">{esc(T_ui(cat.get("kicker", "Меню · DoMik")))}</div>'
            f'<h2 class="catalog__title">{esc(T_ui(cat["title"]))}</h2>'
            '<div class="catalog__diamonds" aria-hidden="true">&#9670;&nbsp;&#9670;&nbsp;&#9670;</div>'
            f'<div class="catalog__cats">{line}</div>'
            '</div>'
            + photos_html +
            f'<div class="catalog__note">{esc(T_ui(cat.get("note", "")))}</div>'
            '</div></section>')


cover = COVER_HTML
if LANG == 'en':
    cover = cover.replace('Ресторан Цахкадзора', 'Restaurant of Tsaghkadzor') \
                 .replace('>Меню<', '>Menu<') \
                 .replace('Цахкадзор, ул.&nbsp;Хачатура&nbsp;Кечареци&nbsp;6', 'Tsaghkadzor, 6&nbsp;Khachatur&nbsp;Kecharetsi&nbsp;St') \
                 .replace('ежедневно&nbsp;11:00&ndash;23:00', 'daily&nbsp;11:00&ndash;23:00')
elif LANG == 'hy':
    cover = cover.replace('Ресторан Цахкадзора', 'Ծաղկաձորի ռեստորան') \
                 .replace('>Меню<', '>Մենյու<') \
                 .replace('Цахкадзор, ул.&nbsp;Хачатура&nbsp;Кечареци&nbsp;6', 'Ծաղկաձոր, Խաչատուր&nbsp;Կեչառեցու&nbsp;փ.&nbsp;6') \
                 .replace('ежедневно&nbsp;11:00&ndash;23:00', 'ամեն&nbsp;օր&nbsp;11:00&ndash;23:00')
parts = [cover]   # обложка; первый разворот — «Начало трапезы» перед «Завтрак»

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
    sec_title = T_sec(sec['name'].strip())
    cat_title = fill(CAT_TITLE, TITLE=esc(sec_title))
    if len(sec_title) > 20:                      # длинный заголовок — мельче, в одну строку
        cat_title = cat_title.replace('book-cat__title', 'book-cat__title book-cat__title--long', 1)
    parts.append(cat_title)
    if sec.get('note'):
        parts.append('<p class="book-cat__note flow-keep">' + esc(T_ui(sec['note'].strip())) + '</p>')
    for it in sec['items']:
        if it.get('break'):                     # принудительный разрыв листа
            parts.append('<div class="book-break"></div>')
            continue
        if it.get('sub'):                       # подзаголовок-подраздел
            parts.append(fill(SUBCAT_TITLE, TITLE=esc(T_sub(it['sub'].strip()))))
            continue
        name_html = esc(T_name(it['name'].strip()))
        if it.get('sizes'):
            name_html += f' <span class="dish-size">{esc(T_sizes(it["sizes"].strip()))}</span>'
        parts.append(fill(DISH_TPL,
                          NAME=name_html,
                          DESC=esc(T_desc(it['name'], (it.get('desc') or '').strip())),
                          PRICE=price_kitchen(it.get('price', ''))))
        dish_count += 1
print("kitchen sections:", len(pm), "| dishes:", dish_count)

# ---------- барная карта из data/print-bar.json (ОТВЯЗАНА от сайта) ----------
# Порядок разделов задаётся самим print-bar.json (безалкогольное идёт первым).
# «К пиву» остаётся curated-разделом из print-menu.json и вставляется после «Пиво».
bar = json.load(io.open(os.path.join(ROOT, "data", "print-bar.json"), encoding='utf-8'))
bar_rows_total = 0
if not NO_BAR:
    parts.append(render_catalog(BAR_SPREAD))   # фотографический барный разворот (вместо кремового)

def emit_curated_bar(sec):
    """Кухонная (curated) секция print-menu.json как раздел бара (К пиву)."""
    global bar_rows_total
    parts.append(fill(BAR_SEC_TITLE, TITLE=esc(T_bar_sec(sec['name'].strip()))))
    for it in sec['items']:
        p = (it.get('price') or '').strip()
        if any(ch.isdigit() for ch in p):
            p = p + ' ֏'
        parts.append(fill(BAR_ROW_TPL, NAME=esc(T_bar_name(it['name'].strip())), VOL='', PRICE=price_bar(p)))
        bar_rows_total += 1

for sec in (bar if not NO_BAR else []):
    title = sec['section'].strip()
    parts.append(fill(BAR_SEC_TITLE, TITLE=esc(T_bar_sec(title))))
    for it in sec['items']:
        if it.get('sub'):                   # подзаголовок-подраздел внутри раздела бара
            parts.append(fill(SUBCAT_TITLE, TITLE=esc(T_sub(it['sub'].strip()))))
            continue
        p = (it.get('price') or '').strip()
        if any(ch.isdigit() for ch in p):
            p = p + ' ֏'
        row = fill(BAR_ROW_TPL, NAME=esc(T_bar_name(it['name'].strip())),
                   VOL=esc(T_bar_vol((it.get('vol') or '').strip())), PRICE=price_bar(p))
        if it.get('note'):                      # подпись-состав под строкой
            row = row.replace('class="bar-row"', 'class="bar-row flow-keep"', 1)
            row += '\n<p class="bar-row__note">' + esc(T_bar_note(it['note'].strip())) + '</p>'
        parts.append(row)
        bar_rows_total += 1
    if title in bar_placed:                 # curated-раздел «К пиву» сразу после «Пиво»
        emit_curated_bar(bar_placed[title])

print("bar sections:", len(bar), "| bar rows:", bar_rows_total)

# ---------- прощальный разворот в самом конце книги ----------
# Без форзацев: клиент проверил схему печати своей типографии —
# финальная страница ложится на оборот и так.
parts.append(render_catalog(FAREWELL))

# ---------- сборка ----------
head_out = HEAD
if LANG == 'hy':
    head_out = head_out.replace(
        '<link rel="stylesheet" href="css/print-menu.css',
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+Armenian:wght@400;500;600&display=swap" rel="stylesheet">\n'
        '<style>:root{--serif:\'Cormorant Garamond\',\'Noto Serif Armenian\',Georgia,serif !important}</style>\n'
        '<link rel="stylesheet" href="css/print-menu.css')
out = (head_out + "\n" + TOOLBAR + '\n<div id="book" class="book">\n'
       + "\n".join(parts) + "\n"
       + "</div>\n" + SCRIPT + "\n</body>\n</html>\n")
io.open(os.path.join(ROOT, "menu-print.html"), 'w', encoding='utf-8').write(out)
print("menu-print.html written:", len(out), "chars")
