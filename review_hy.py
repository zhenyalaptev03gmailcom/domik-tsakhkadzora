#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вычитка армянского перевода носителем языка.

    python3 review_hy.py --export   → data/перевод-hy-на-проверку.csv
    python3 review_hy.py --apply    → применить исправления из того же файла

Как пользоваться:
 1. Выгрузить файл, открыть в Excel / Google Sheets / Numbers
 2. Отдать носителю языка: он правит ТОЛЬКО колонку «Исправление»
    (пустая ячейка = перевод верный, править не нужно)
 3. Сохранить обратно в CSV и запустить --apply
 4. Пересобрать сайт и книгу: generate_menu_html.py, generate_bar_html.py,
    generate_print_menu.py

Колонки: Тип | Ключ | Русский | Текущий перевод | Исправление
«Ключ» — техническая привязка, менять нельзя.
"""
import csv, io, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(ROOT, *a)
SITE = P("data", "menu.json")
GEN  = P("generate_print_menu.py")
CSV_ = P("data", "перевод-hy-на-проверку.csv")

HEADER = ["Тип", "Ключ", "Русский", "Текущий перевод", "Исправление"]


def gen_dicts():
    """Словари разделов/подзаголовков/подписей из генератора печати."""
    src = io.open(GEN, encoding="utf-8").read()
    out = {}
    for dname in ("SEC_TR", "SUB_TR", "SIZES_TR", "UI_TR", "SUPPLEMENT_NAME", "SUPPLEMENT_DESC"):
        m = re.search(dname + r"\s*=\s*\{.*?\n\}", src, re.S)
        if not m:
            continue
        ns = {}
        exec(m.group(0), ns)
        out[dname] = ns[dname]
    return out


def export():
    site = json.load(io.open(SITE, encoding="utf-8"))
    rows, seen = [], set()

    for c in site:
        for it in c.get("items", []):
            if not it.get("name"):
                continue
            if it.get("name_hy"):
                rows.append(["блюдо", "name:" + it["name"], it["name"], it["name_hy"], ""])
            if it.get("composition") and it.get("composition_hy"):
                rows.append(["состав", "comp:" + it["name"], it["composition"], it["composition_hy"], ""])

    for dname, d in gen_dicts().items():
        kind = {"SEC_TR": "раздел", "SUB_TR": "подраздел", "SIZES_TR": "порция",
                "UI_TR": "надпись", "SUPPLEMENT_NAME": "блюдо", "SUPPLEMENT_DESC": "состав"}[dname]
        for ru, pair in d.items():
            key = f"{dname}:{ru}"
            if key in seen:
                continue
            seen.add(key)
            rows.append([kind, key, ru, pair[1], ""])

    with io.open(CSV_, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    print(f"Файл для вычитки: {CSV_}")
    print(f"Строк: {len(rows)}  (носитель правит только колонку «Исправление»)")


def apply():
    if not os.path.exists(CSV_):
        sys.exit(f"Нет файла {CSV_} — сначала --export и вычитка.")
    rows = list(csv.DictReader(io.open(CSV_, encoding="utf-8-sig")))
    fixes = {r["Ключ"].strip(): r["Исправление"].strip()
             for r in rows if r.get("Ключ") and (r.get("Исправление") or "").strip()}
    if not fixes:
        print("Исправлений в файле нет — колонка «Исправление» пустая.")
        return

    site = json.load(io.open(SITE, encoding="utf-8"))
    applied, gen_fixes = 0, {}
    for key, val in fixes.items():
        if key.startswith("name:") or key.startswith("comp:"):
            what, dish = key.split(":", 1)
            fld = "name_hy" if what == "name" else "composition_hy"
            for c in site:
                for it in c.get("items", []):
                    if (it.get("name") or "").strip() == dish and it.get(fld) != val:
                        print(f"  {dish[:34]:36} {it.get(fld)}  →  {val}")
                        it[fld] = val
                        applied += 1
        else:
            gen_fixes[key] = val

    if applied:
        json.dump(site, io.open(SITE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # правки словарей внутри generate_print_menu.py
    if gen_fixes:
        src = io.open(GEN, encoding="utf-8").read()
        for key, val in gen_fixes.items():
            dname, ru = key.split(":", 1)
            pat = re.compile(r'("' + re.escape(ru) + r'"\s*:\s*\(\s*"(?:[^"\\]|\\.)*"\s*,\s*)"(?:[^"\\]|\\.)*"')
            src, n = pat.subn(lambda m: m.group(1) + '"' + val.replace('"', r'\"') + '"', src, count=1)
            if n:
                print(f"  [{dname}] {ru}  →  {val}")
                applied += 1
            else:
                print(f"  !! не нашёл в генераторе: {key}")
        io.open(GEN, "w", encoding="utf-8").write(src)

    print(f"\nПрименено правок: {applied}")
    print("Теперь пересоберите: generate_menu_html.py, generate_bar_html.py, generate_print_menu.py")


if __name__ == "__main__":
    if "--apply" in sys.argv:
        apply()
    else:
        export()
