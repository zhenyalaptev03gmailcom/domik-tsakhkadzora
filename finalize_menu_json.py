#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""menu.json.staged + найденные фото -> чистый data/menu.json (боевой)."""
import json

staged = json.load(open("data/menu.json.staged", encoding="utf-8"))
photos = json.load(open("menu_photos.json", encoding="utf-8"))

NAME2SLUG = {
    "Омлет классический": "омлет-классический",
    "Омлет с грибами, бастурмой и зеленью": "омлет-с-грибами",
    "Фирменная бурата": "фирменная-бурата",
    "Блинчики с мясом": "блинчики-с-мясом",
    "Тако с овощами": "тако-с-овощами",
    "Тако с курицей": "тако-с-курицей",
    "Тако с креветками": "тако-с-креветками",
    "Цезарь с креветками": "цезарь-с-креветками",
    "Домашний куриный суп": "домашний-куриный-суп",
    "Паста песто": "паста-песто",
    "Немецкий гуляш с пивным соусом": "немецкий-гуляш",
    "Куриное филе по-французски": "куриное-филе-по-французски",
    "Пеппер стейк": "пеппер-стейк",
    "Солёные орехи": "солёные-орехи",
    "Сырные шарики": "сырные-шарики",
    "Чесночный хлеб": "чесночный-хлеб",
    "Брецель (2 шт) со сливочным маслом": "брецель",
    "Домик": "домик-сет",
    "Хачапури аджарский": "хачапури-аджарский",
    "Хачапури имеретинский": "хачапури-имеретинский",
    "Хачапури мегрельский": "хачапури-мегрельский",
    "Арбуз и дыня": "арбуз-и-дыня",
}

filled, still_no = 0, []
out = []
for cat in staged:
    c = {k: v for k, v in cat.items() if not k.startswith("_")}
    items = []
    for it in cat["items"]:
        if "sub" in it:
            items.append({k: v for k, v in it.items() if not k.startswith("_")})
            continue
        d = {k: v for k, v in it.items() if not k.startswith("_")}
        if not d.get("local_image"):
            slug = NAME2SLUG.get(d["name"])
            if slug and slug in photos:
                d["local_image"] = photos[slug]
                d["has_image"] = True
                filled += 1
            else:
                d["has_image"] = False
                still_no.append(d["name"])
        items.append(d)
    c["items"] = items
    out.append(c)

json.dump(out, open("data/menu.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
ndish = sum(1 for c in out for it in c["items"] if "sub" not in it)
withimg = sum(1 for c in out for it in c["items"] if "sub" not in it and it.get("local_image"))
print(f"data/menu.json записан: разделов {len(out)}, блюд {ndish}, с фото {withimg}")
print(f"  проставлено новых фото: {filled}")
if still_no:
    print(f"  БЕЗ фото ({len(still_no)}): " + ", ".join(still_no))
