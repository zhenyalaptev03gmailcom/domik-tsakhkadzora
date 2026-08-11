#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Синхронизация меню с Google-таблицей: ЦЕНЫ и СТОП-ЛИСТ.

Ресторан правит таблицу → GitHub Action запускает этот скрипт → цены и наличие
переносятся в data/menu.json (сайт) и data/print-menu.json (печатная книга).

Таблица публикуется как CSV: Файл → Поделиться → Опубликовать в интернете → CSV.
Ссылка кладётся в data/sheet-config.json (ключ "csv_url") или в переменную
окружения SHEET_CSV_URL.

Колонки таблицы (заголовки в первой строке, регистр не важен):
    ID        — технический код блюда, НЕ МЕНЯТЬ
    Раздел    — справочно, не используется
    Блюдо     — справочно, не используется
    Цена      — «2 500» или «2 300 / 2 500»
    В наличии — «да»/«нет» (или ИСТИНА/ЛОЖЬ, TRUE/FALSE, 1/0)

БЕЗОПАСНОСТЬ: если таблица повреждена (нет колонок, неизвестные ID, кривые цены),
скрипт завершается с ошибкой и НИЧЕГО не меняет — сайт продолжает работать.

Запуск:
    python3 sync_from_sheet.py            # применить
    python3 sync_from_sheet.py --dry-run  # только показать, что изменится
    python3 sync_from_sheet.py --export   # выгрузить текущее меню в seed-таблицу CSV
"""
import csv, io, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(ROOT, *a)

SITE_JSON  = P("data", "menu.json")
PRINT_JSON = P("data", "print-menu.json")
CONFIG     = P("data", "sheet-config.json")
SEED_CSV   = P("data", "menu-sheet-seed.csv")

PRICE_RE = re.compile(r"^\d[\d\s ]*(?:[/–-]\s*\d[\d\s ]*)*$")
YES = {"да", "yes", "true", "истина", "1", "y", "+", "✓"}
NO  = {"нет", "no", "false", "ложь", "0", "n", "-", ""}


def norm_price(v):
    """«2 500 » → «2 500»; «2300/2500» → «2 300 / 2 500»."""
    v = str(v or "").replace(" ", " ").strip()
    if not v:
        return ""
    parts = [p.strip() for p in re.split(r"[/–]", v)]
    out = []
    for p in parts:
        digits = re.sub(r"\D", "", p)
        if not digits:
            return ""
        n = int(digits)
        out.append(f"{n:,}".replace(",", " "))
    return " / ".join(out)


def load_json(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def iter_dishes(doc):
    for sec in doc:
        for it in sec.get("items", []):
            if it.get("name"):
                yield sec, it


# ---------------------------------------------------------------- export seed
def export_seed():
    site = load_json(SITE_JSON)
    rows = [("ID", "Раздел", "Блюдо", "Цена", "В наличии")]
    for sec, it in iter_dishes(site):
        if not it.get("id"):
            continue
        rows.append((it["id"], sec["name"], it["name"], it.get("price", ""),
                     "нет" if it.get("hidden") else "да"))
    with io.open(SEED_CSV, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"Таблица-заготовка: {SEED_CSV}  ({len(rows)-1} блюд)")
    print("Импортируйте её в Google Sheets: Файл → Импорт → Загрузить.")


# ------------------------------------------------------------------ csv fetch
def fetch_rows():
    url = os.environ.get("SHEET_CSV_URL", "").strip()
    if not url and os.path.exists(CONFIG):
        url = (load_json(CONFIG).get("csv_url") or "").strip()
    if not url or url.startswith("ВСТАВЬТЕ"):
        sys.exit("Не задана ссылка на таблицу: заполните data/sheet-config.json "
                 "(csv_url) или переменную SHEET_CSV_URL.")
    req = urllib.request.Request(url, headers={"User-Agent": "domik-menu-sync/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read().decode("utf-8-sig", "replace")
    if "<html" in raw[:400].lower():
        sys.exit("По ссылке пришла HTML-страница, а не CSV. Проверьте, что таблица "
                 "опубликована в интернете именно как CSV.")
    rows = list(csv.DictReader(io.StringIO(raw)))
    if not rows:
        sys.exit("Таблица пуста — ничего не меняю.")
    return rows


def pick(row, *names):
    for k, v in row.items():
        if k and k.strip().lower() in names:
            return (v or "").strip()
    return None


# ----------------------------------------------------------------------- main
def main():
    dry = "--dry-run" in sys.argv
    if "--export" in sys.argv:
        return export_seed()

    rows = fetch_rows()
    if pick(rows[0], "id") is None:
        sys.exit("В таблице нет колонки ID — синхронизация отменена.")

    site, prnt = load_json(SITE_JSON), load_json(PRINT_JSON)
    by_id = {it["id"]: it for _, it in iter_dishes(site) if it.get("id")}
    # печатное меню связываем по названию (там нет id)
    by_name = {}
    for _, it in iter_dishes(prnt):
        by_name.setdefault(it["name"].strip(), []).append(it)

    errors, changes = [], []
    for i, row in enumerate(rows, start=2):
        did = (pick(row, "id") or "").strip()
        if not did:
            continue
        it = by_id.get(did)
        if it is None:
            errors.append(f"строка {i}: неизвестный ID «{did}» — блюдо не найдено в меню")
            continue

        raw_price = pick(row, "цена", "price")
        if raw_price:
            price = norm_price(raw_price)
            if not price or not PRICE_RE.match(price):
                errors.append(f"строка {i} ({it['name']}): цена «{raw_price}» непонятна — "
                              "должно быть число, например 2 500 или 2 300 / 2 500")
            elif price != it.get("price"):
                changes.append(f"цена  {it['name']}: {it.get('price')} → {price}")
                if not dry:
                    it["price"] = price
                    for p in by_name.get(it["name"].strip(), []):
                        p["price"] = price

        raw_av = pick(row, "в наличии", "наличие", "available")
        if raw_av is not None:
            v = raw_av.strip().lower()
            if v not in YES and v not in NO:
                errors.append(f"строка {i} ({it['name']}): «{raw_av}» в колонке «В наличии» — "
                              "напишите «да» или «нет»")
            else:
                hidden = v in NO and v != ""
                if bool(it.get("hidden")) != hidden:
                    changes.append(f"стоп-лист {it['name']}: {'скрыто' if hidden else 'показано'}")
                    if not dry:
                        if hidden:
                            it["hidden"] = True
                        else:
                            it.pop("hidden", None)

    if errors:
        print("ОШИБКИ В ТАБЛИЦЕ — изменения НЕ применены:", file=sys.stderr)
        for e in errors:
            print("  •", e, file=sys.stderr)
        sys.exit(1)

    if not changes:
        print("Изменений нет — меню уже соответствует таблице.")
        return

    print(f"Изменений: {len(changes)}")
    for c in changes:
        print("  •", c)
    if dry:
        print("(--dry-run: файлы не тронуты)")
        return
    save_json(site, SITE_JSON)
    save_json(prnt, PRINT_JSON)
    print("data/menu.json и data/print-menu.json обновлены.")


if __name__ == "__main__":
    main()
