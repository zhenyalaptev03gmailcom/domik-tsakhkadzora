#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Перестраивает menu.json (сайт) под структуру print-menu.json (печатное = источник правды
для разделов / порядка / цен / описаний). Фото и переводы EN/HY переносятся с текущего
menu.json по совпадению имени или по курированной карте переименований.

Выход: data/menu.json.staged (НЕ перезаписывает боевой) + отчёт в stdout.
"""
import json, re, unicodedata, sys

ROOT = "data/"
print_menu = json.load(open(ROOT + "print-menu.json", encoding="utf-8"))
site_menu  = json.load(open(ROOT + "menu.json", encoding="utf-8"))

def norm(s):
    s = unicodedata.normalize("NFC", str(s)).lower().strip().replace("ё", "е")
    s = re.sub(r"[^a-zа-я0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# индекс сайта: норм-имя -> dish (подзаголовки пропускаем)
site_idx = {}
for sec in site_menu:
    for it in sec["items"]:
        if "sub" in it or "name" not in it:
            continue
        site_idx[norm(it["name"])] = it

# КУРИРОВАННАЯ КАРТА ПЕРЕИМЕНОВАНИЙ: печатное имя -> имя на сайте (откуда взять фото/переводы)
RENAME = {
    "Панкейк с нутеллой": "Панкейк с нутеллой и маком",
    "Брускетта с томатами": "Брускетта",
    "Домашние соленья": "Соления",
    "Классическая бурата": "Бурата",
    "Армянский салат с гранатовым соусом": "Армянский салат",
    "Овощной крем-суп": "Крем-суп",
    "Паста карбонара": "Паста панчетта",
    "Баклажан фаршированный": "Баклажаны фаршированные",
    "Цыплёнок с овощами": "Курица с овощами",
    "Бефстроганов (телятина / курица)": "Бефстроганов из телятины (рис/картофель)",
    "Свиные рёбрышки острые": "Свиные ребрышки",
    "Баварские сосиски": "Ассорти немецких сосисок",
    "Хашлама": "Рагу из баранины с овощами",
    "Паде": "Запечённое мясо и овощи в тесте",
    "Форель цельная": "Форель",
    "Хариса": "Хашариса",
    "Шоколадный тарт": "Шоколадный пирог",
    "Домашний хлеб": "Свежий хлеб",
    "Тайландский с рисом": "Тай салат",          # клиент: тот же салат + рис
    "Семейный домик": "Ассорти шашлыков",         # печатное описание = «Большое ассорти шашлыков на углях»
    "Стейк лосося": "Лосось",                     # переименование: перенести фото одного филе лосося
    "Домашняя аришта": "Аришта",                  # переименование: перенести фото
    "Паде мясной": "Паде",                        # переименование: перенести фото
}

# Переводы для реально НОВЫХ блюд (RU были только на печатном): имя + состав EN/HY
NEW_TR = {
    "Армянская закуска": {
        "name_en": "Armenian appetizer", "name_hy": "Հայկական նախուտեստ",
        "composition_en": "Matsun, hummus, rezhan, house chips",
        "composition_hy": "Մածուն, հումուս, ռեժան, տնական չիպս"},
    "Куриное равиоли в белом соусе": {
        "name_en": "Chicken ravioli in white sauce", "name_hy": "Հավի ռավիոլի սպիտակ սոուսով",
        "composition_en": "Classic recipe: ravioli with chicken and parmesan in cream sauce",
        "composition_hy": "Դասական բաղադրատոմս՝ ռավիոլի հավով և պարմեզանով սերուցքային սոուսում"},
    "Шпик свиной": {
        "name_en": "Pork entrecôte & ribs", "name_hy": "Խոզի անտրեկոտ և կողիկ",
        "composition_en": "Pork: entrecôte and ribs",
        "composition_hy": "Խոզի միս՝ անտրեկոտ և կողիկներ"},
    "Паде с овощами": {
        "name_en": "Pide with vegetables", "name_hy": "Փիդե բանջարեղենով",
        "composition_en": "Vegetables baked in dough",
        "composition_hy": "Բանջարեղեն՝ թխված խմորի մեջ"},
    "Кесадилья с курицей": {
        "name_en": "Chicken quesadilla", "name_hy": "Կեսադիլյա հավով",
        "composition_en": "Tortilla, chicken, cheese",
        "composition_hy": "Տորտիլյա, հավ, պանիր"},
    "Кесадилья с говядиной": {
        "name_en": "Beef quesadilla", "name_hy": "Կեսադիլյա տավարով",
        "composition_en": "Tortilla, beef, cheese",
        "composition_hy": "Տորտիլյա, տավար, պանիր"},
    "Наггетсы": {
        "name_en": "Chicken nuggets", "name_hy": "Հավի նագետս",
        "composition_en": "Chicken nuggets with french fries",
        "composition_hy": "Հավի նագետս ֆրի կարտոֆիլով"},
    "Котлеты по-домашнему с картофельным пюре": {
        "name_en": "Homestyle cutlets with mashed potatoes",
        "name_hy": "Տնական կոտլետներ կարտոֆիլի պյուրեով"},
}

# EN/HY для разделов (берём существующие где есть, для новых — заданы тут)
SECTR = {
    "Завтрак": ("Breakfast", "Նախաճաշ"),
    "Закуски": ("Appetizers", "Նախուտեստներ"),
    "Салаты": ("Salads", "Աղցաններ"),
    "Суп": ("Soup", "Ապուր"),
    "Паста": ("Pasta", "Մակարոնեղեն"),
    "Основные блюда": ("Main dishes", "Հիմնական ուտեստներ"),
    "К пиву": ("With beer", "Գարեջրի հետ"),
    "Блюда от шеф-повара": ("Chef's specials", "Շեֆ-խոհարարի ուտեստներ"),
    "Печь и гриль": ("Oven & grill", "Փուռ և գրիլ"),
    "Жареная рыба и морепродукты": ("Fried fish & seafood", "Տապակած ձուկ և ծովամթերք"),
    "Армянские традиции": ("Armenian traditions", "Հայկական ավանդույթներ"),
    "Гарниры": ("Sides", "Կողմնակի ուտեստներ"),
    "Детское меню": ("Kids' menu", "Մանկական մենյու"),
    "Часть любви": ("Desserts", "Աղանդերներ"),
    "Хлеб": ("Bread", "Հաց"),
}
SUBTR = {
    "Пицца": ("Pizza", "Պիցցա"),
    "Хачапури": ("Khachapuri", "Խաչապուրի"),
    "Бургеры и сэндвичи": ("Burgers & sandwiches", "Բուրգերներ և սենդվիչներ"),
}

def translit(s):
    m = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i',
         'й':'i','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t',
         'у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'',
         'э':'e','ю':'yu','я':'ya',' ':'-'}
    s = unicodedata.normalize("NFC", s).lower()
    out = "".join(m.get(c, c if c.isalnum() else "-") for c in s)
    return re.sub(r"-+", "-", out).strip("-")

used_ids = set()
def make_id(name):
    base = translit(name) or "dish"
    i = base; n = 2
    while i in used_ids:
        i = f"{base}-{n}"; n += 1
    used_ids.add(i)
    return i

# pre-register existing ids we keep
new_menu = []
report = {"matched": [], "renamed": [], "new": [], "subs": [], "removed": []}
consumed = set()   # норм-имена сайта, перенесённые в новое меню

cat_id = 2138
for sec in print_menu:
    en, hy = SECTR.get(sec["name"], ("", ""))
    cat = {"id": str(cat_id), "name": sec["name"], "name_en": en, "name_hy": hy,
           "slug": translit(sec["name"]), "items": []}
    if sec.get("note"):
        cat["note"] = sec["note"]
    cat_id += 1
    for it in sec["items"]:
        if "sub" in it:
            sen, shy = SUBTR.get(it["sub"], ("", ""))
            cat["items"].append({"sub": it["sub"], "sub_en": sen, "sub_hy": shy})
            report["subs"].append(f"{sec['name']} › {it['sub']}")
            continue
        nm = it["name"]
        n = norm(nm)
        src = site_idx.get(n)
        rename_from = None
        if src is None and nm in RENAME:
            rfn = norm(RENAME[nm]); src = site_idx.get(rfn); rename_from = RENAME[nm]
        dish = {"name": nm, "price": it["price"]}
        if it.get("desc"):
            dish["composition"] = it["desc"]
        if it.get("sizes"):
            dish["sizes"] = it["sizes"]
        if src:
            consumed.add(norm(src["name"]))
            dish["id"] = src.get("id") or make_id(nm)
            used_ids.add(dish["id"])
            if src.get("local_image"):
                dish["local_image"] = src["local_image"]
                dish["has_image"] = True
            for k in ("name_en", "name_hy"):
                if src.get(k):
                    dish[k] = src[k]
            # переводы состава переносим только если RU-описание не изменилось
            same_desc = norm(it.get("desc", "")) == norm(src.get("composition", ""))
            if same_desc:
                for k in ("composition_en", "composition_hy"):
                    if src.get(k):
                        dish[k] = src[k]
            elif it.get("desc"):
                dish["_needs_tr"] = True
            if rename_from:
                report["renamed"].append(f"{sec['name']} / {nm}  ←  {rename_from}"
                                         + ("  [фото✓]" if dish.get("local_image") else "  [без фото]"))
            else:
                report["matched"].append(f"{sec['name']} / {nm}")
        else:
            dish["id"] = make_id(nm)
            dish["has_image"] = False
            dish["_new"] = True
            dish["_needs_photo"] = True
            tr = NEW_TR.get(nm)
            if tr:
                for k, v in tr.items():
                    dish[k] = v
            elif it.get("desc"):
                dish["_needs_tr"] = True
            report["new"].append(f"{sec['name']} / {nm} — {it['price']}"
                                 + ("  [EN/HY✓]" if tr else "  [RU-only]"))
        cat["items"].append(dish)
    new_menu.append(cat)

# удалённые: были на сайте, не перенесены
for sec in site_menu:
    for it in sec["items"]:
        if "sub" in it or "name" not in it:
            continue
        if norm(it["name"]) not in consumed:
            report["removed"].append(it["name"])

json.dump(new_menu, open(ROOT + "menu.json.staged", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

# ── отчёт ──
def line(t): print(t)
nf = sum(len(c["items"]) for c in new_menu)
nd = sum(1 for c in new_menu for x in c["items"] if "sub" not in x)
line(f"=== НОВЫЙ menu.json: разделов {len(new_menu)}, элементов {nf} (блюд {nd}, подзаголовков {nf-nd}) ===")
line(f"  совпало точно: {len(report['matched'])}")
line(f"  переименовано (фото/переводы сохранены): {len(report['renamed'])}")
line(f"  реально новых (RU, без фото, EN/HY=TODO): {len(report['new'])}")
line(f"  подзаголовков: {len(report['subs'])}")
line(f"  удалено с сайта: {len(report['removed'])}")
line("\n--- ПЕРЕИМЕНОВАНО ---")
for x in report["renamed"]: line("  ↻ " + x)
line("\n--- НОВЫЕ (без фото) ---")
for x in report["new"]: line("  + " + x)
line("\n--- УДАЛЕНО НАСОВСЕМ ---")
for x in report["removed"]: line("  − " + x)
