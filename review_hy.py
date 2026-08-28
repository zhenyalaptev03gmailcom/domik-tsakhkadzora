#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вычитка армянского перевода носителем языка — весь текст меню в одной таблице.

    python3 review_hy.py --export   → data/перевод-hy-на-проверку.csv
    python3 review_hy.py --apply    → применить исправления из того же файла

Порядок работы:
 1. --export, открыть файл в Excel / Numbers / Google Sheets
 2. Носитель правит ТОЛЬКО последнюю колонку «Исправление».
    Пустая ячейка = перевод верный, трогать не нужно.
 3. Сохранить обратно тем же именем в формате CSV (UTF-8)
 4. python3 review_hy.py --apply
 5. Пересобрать: generate_menu_html.py, generate_bar_html.py, generate_print_menu.py

Колонку «Ключ» менять нельзя — по ней скрипт находит, куда класть правку.
Охват: блюда и составы кухни (menu.json), названия разделов/подразделов/порций
и подписи книги (словари в generate_print_menu.py), разделы и подписи бара
(атрибуты data-tr-hy в menu.html — оттуда их берут и сайт, и печатная книга).
"""
import csv, io, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(ROOT, *a)
SITE, GEN, MENU_HTML = P("data", "menu.json"), P("generate_print_menu.py"), P("menu.html")
CSV_ = P("data", "перевод-hy-на-проверку.csv")
# рабочая копия на рабочем столе — её и правит носитель языка
DESK = os.path.join(os.path.expanduser("~"), "Desktop", "Домик — армянский перевод.xlsx")
DESK_CSV = os.path.join(os.path.expanduser("~"), "Desktop", "Домик — армянский перевод.csv")


def newest_csv():
    """Берём тот файл, который правили последним: в репозитории или на рабочем столе."""
    have = [p for p in (DESK, DESK_CSV, CSV_) if os.path.exists(p)]
    return max(have, key=os.path.getmtime) if have else None
HEADER = ["Раздел", "Тип", "Ключ", "Русский", "Текущий перевод", "Исправление"]

KIND = {"SEC_TR": "раздел", "SUB_TR": "подраздел", "SIZES_TR": "порция", "UI_TR": "подпись",
        "SUPPLEMENT_NAME": "блюдо", "SUPPLEMENT_DESC": "состав"}


def gen_dicts():
    src = io.open(GEN, encoding="utf-8").read()
    out = {}
    for d in KIND:
        m = re.search(d + r"\s*=\s*\{.*?\n\}", src, re.S)
        if m:
            ns = {}; exec(m.group(0), ns); out[d] = ns[d]
    return out


def bar_segment():
    h = io.open(MENU_HTML, encoding="utf-8").read()
    a = h.find('<div id="menu-bar"')
    return h, (h[a:] if a >= 0 else "")


def bar_rows():
    """Разделы, названия и подписи барной карты из атрибутов data-tr-hy."""
    _, seg = bar_segment()
    rows, seen = [], set()
    pats = [(r'<h[34][^>]*data-tr-hy="([^"]*)"[^>]*>([^<]+)</h[34]>', "bar_sec", "раздел бара"),
            (r'class="bar-name-t"[^>]*data-tr-hy="([^"]*)"[^>]*>([^<]+)<', "bar_name", "позиция бара"),
            (r'class="bar-item__note"[^>]*data-tr-hy="([^"]*)"[^>]*>([^<]*)<', "bar_note", "подпись бара")]
    for pat, pfx, kind in pats:
        for hy, ru in re.findall(pat, seg):
            ru = ru.strip()
            if not ru or (pfx, ru) in seen:
                continue
            if hy.strip() == ru:      # бренды (Coca-Cola, Jameson) не переводятся — не тащим в таблицу
                continue
            seen.add((pfx, ru))
            rows.append(["Барная карта", kind, f"{pfx}:{ru}", ru, hy, ""])
    return rows


def export():
    site = json.load(io.open(SITE, encoding="utf-8"))
    rows = []
    for c in site:
        sec = c["name"]
        if c.get("name_hy"):
            rows.append([sec, "раздел", "cat:" + sec, sec, c["name_hy"], ""])
        for it in c.get("items", []):
            if it.get("sub"):
                if it.get("sub_hy"):
                    rows.append([sec, "подраздел", "sub:" + it["sub"], it["sub"], it["sub_hy"], ""])
                continue
            if not it.get("name"):
                continue
            if it.get("name_hy"):
                rows.append([sec, "блюдо", "name:" + it["name"], it["name"], it["name_hy"], ""])
            if it.get("composition") and it.get("composition_hy"):
                rows.append([sec, "состав", "comp:" + it["name"], it["composition"], it["composition_hy"], ""])
    # разделы и подразделы уже выгружены из menu.json — второй раз не показываем,
    # иначе одну и ту же фразу правят в двух строках и получаются разные варианты
    done = {r[3] for r in rows if r[1] in ("раздел", "подраздел")}
    seen = set()
    for dname, d in gen_dicts().items():
        for ru, pair in d.items():
            key = f"{dname}:{ru}"
            if key in seen or (dname in ("SEC_TR", "SUB_TR") and ru in done):
                continue
            seen.add(key)
            rows.append(["Печатная книга", KIND[dname], key, ru, pair[1], ""])
    rows += bar_rows()

    with io.open(CSV_, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(HEADER); w.writerows(rows)
    made = write_xlsx(rows)
    print(f"Таблица для вычитки: {made or DESK_CSV}")
    print(f"Копия в репозитории:  {CSV_}")
    print(f"Строк: {len(rows)}. Носитель правит только колонку «Исправление».")


def write_xlsx(rows):
    """Готовая книга Excel: шапка закреплена, колонка «Исправление» подсвечена,
    служебный «Ключ» спрятан. Без openpyxl откатываемся на CSV."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        with io.open(DESK_CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(HEADER); w.writerows(rows)
        return None
    wb = Workbook(); ws = wb.active; ws.title = "Перевод"
    ws.append(HEADER); ws.append([]) if False else None
    for r in rows: ws.append(r)
    head_fill = PatternFill("solid", fgColor="3E2C18")
    edit_fill = PatternFill("solid", fgColor="FFF6DC")
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = head_fill
        c.alignment = Alignment(vertical="center")
    for w, letter in zip((16, 14, 34, 42, 46, 46), "ABCDEF"):
        ws.column_dimensions[letter].width = w
    ws.column_dimensions["C"].hidden = True          # «Ключ» — служебный
    wrap = Alignment(wrap_text=True, vertical="top")
    for row in ws.iter_rows(min_row=2):
        for c in row[3:]: c.alignment = wrap
        row[5].fill = edit_fill                       # «Исправление»
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:F{ws.max_row}"
    wb.save(DESK)
    unlock_xlsx(DESK)
    if os.path.exists(DESK_CSV): os.remove(DESK_CSV)  # чтобы не путались две копии
    return DESK


def unlock_xlsx(path):
    """Excel на macOS открывает файл только для чтения из-за карантина Finder,
    а openpyxl всегда пишет пустой <workbookProtection/>. Убираем оба."""
    import zipfile, shutil, tempfile
    tmp = tempfile.mktemp(suffix=".xlsx")
    with zipfile.ZipFile(path) as z, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for item in z.infolist():
            data = z.read(item.filename)
            if item.filename == "xl/workbook.xml":
                data = re.sub(rb"<workbookProtection\s*/>", b"", data)
            out.writestr(item, data)
    shutil.move(tmp, path)
    # снимаем карантин Finder — иначе Excel открывает «только для чтения»
    subprocess.run(["xattr", "-d", "com.apple.quarantine", path],
                   stderr=subprocess.DEVNULL, check=False)


def apply():
    src_csv = newest_csv()
    if not src_csv:
        sys.exit("Таблицы нет — сначала python3 review_hy.py --export")
    print(f"Читаю правки из: {src_csv}\n")
    if src_csv.endswith(".xlsx"):
        from openpyxl import load_workbook
        ws = load_workbook(src_csv, data_only=True).active
        head = [str(c.value or "") for c in ws[1]]
        rows = [dict(zip(head, [("" if c.value is None else str(c.value)) for c in r]))
                for r in ws.iter_rows(min_row=2)]
    else:
        rows = list(csv.DictReader(io.open(src_csv, encoding="utf-8-sig")))
    fixes = {r["Ключ"].strip(): r["Исправление"].strip()
             for r in rows if r.get("Ключ") and (r.get("Исправление") or "").strip()}
    if not fixes:
        print("Колонка «Исправление» пустая — применять нечего."); return

    site = json.load(io.open(SITE, encoding="utf-8"))
    n, gen_fixes, bar_fixes = 0, {}, {}
    for key, val in fixes.items():
        kind, arg = key.split(":", 1)
        if kind in ("name", "comp"):
            fld = "name_hy" if kind == "name" else "composition_hy"
            for c in site:
                for it in c.get("items", []):
                    if (it.get("name") or "").strip() == arg and it.get(fld) != val:
                        print(f"  {arg[:32]:34} {it.get(fld)}  →  {val}"); it[fld] = val; n += 1
        elif kind == "cat":
            for c in site:
                if c["name"] == arg and c.get("name_hy") != val:
                    print(f"  [раздел] {arg}  →  {val}"); c["name_hy"] = val; n += 1
        elif kind == "sub":
            for c in site:
                for it in c.get("items", []):
                    if it.get("sub") == arg and it.get("sub_hy") != val:
                        print(f"  [подраздел] {arg}  →  {val}"); it["sub_hy"] = val; n += 1
        elif kind.startswith("bar_"):
            bar_fixes[key] = val
        else:
            gen_fixes[key] = val
    if n:
        json.dump(site, io.open(SITE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    if gen_fixes:                                    # словари внутри генератора печати
        src = io.open(GEN, encoding="utf-8").read()
        for key, val in gen_fixes.items():
            dname, ru = key.split(":", 1)
            pat = re.compile(r'("' + re.escape(ru) + r'"\s*:\s*\(\s*"(?:[^"\\]|\\.)*"\s*,\s*)"(?:[^"\\]|\\.)*"')
            src, k = pat.subn(lambda m: m.group(1) + '"' + val.replace('"', r'\"') + '"', src, count=1)
            print(f"  [{dname}] {ru}  →  {val}" if k else f"  !! не нашёл в генераторе: {key}")
            n += k
        io.open(GEN, "w", encoding="utf-8").write(src)

    if bar_fixes:                                    # атрибуты бара в menu.html
        h, seg = bar_segment()
        a = h.find('<div id="menu-bar"')
        new = seg
        for key, val in bar_fixes.items():
            ru = key.split(":", 1)[1]
            # заменяем data-tr-hy у того тега, чей видимый текст — этот русский
            pat = re.compile(r'(data-tr-hy=")([^"]*)("[^>]*>\s*' + re.escape(ru) + r'\s*<)')
            new, k = pat.subn(lambda m: m.group(1) + val + m.group(3), new, count=1)
            print(f"  [бар] {ru}  →  {val}" if k else f"  !! не нашёл в баре: {ru}")
            n += k
        io.open(MENU_HTML, "w", encoding="utf-8", newline="").write(h[:a] + new)

    print(f"\nПрименено правок: {n}")
    print("Теперь пересоберите:")
    print("  python3 generate_menu_html.py && python3 generate_bar_html.py && python3 generate_print_menu.py")


if __name__ == "__main__":
    apply() if "--apply" in sys.argv else export()
