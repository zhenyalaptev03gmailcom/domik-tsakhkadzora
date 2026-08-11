# Сайт ресторана «Домик Цахкадзора»

Статический сайт (HTML/CSS/JS, без бэкенда и базы данных) + печатное меню-книга A4
на трёх языках. Хостинг — GitHub Pages, сборка — GitHub Actions.

**Живой сайт:** https://zhenyalaptev03gmailcom.github.io/domik-tsakhkadzora/

> Документ для разработчика. Инструкция для сотрудников ресторана — в
> [ИНСТРУКЦИЯ-ДЛЯ-РЕСТОРАНА.md](ИНСТРУКЦИЯ-ДЛЯ-РЕСТОРАНА.md).

---

## Главный принцип: HTML не редактируется руками

Меню на сайте и печатная книга **генерируются из JSON-файлов**. Если поправить
`menu.html` вручную, изменения затрёт следующая сборка.

```
data/menu.json        ─┬─→ generate_menu_html.py  ─→ menu.html (#menu-food) + dish.html (бандл)
data/dish-stories.json ┘
data/print-bar.json   ─┬─→ generate_bar_html.py   ─→ menu.html (#menu-bar)
data/print-menu.json  ─┘
data/print-menu.json  ─┬─→ generate_print_menu.py ─→ menu-print.html → PDF
data/print-bar.json   ─┘
data/menu.json (фото) ─┘
```

| Файл | Что в нём | Кто использует |
|---|---|---|
| `data/menu.json` | меню сайта: блюда, цены, составы, переводы EN/HY, пути к фото | сайт |
| `data/print-menu.json` | меню печатной книги (кухня) | печать |
| `data/print-bar.json` | барная карта | печать **и** сайт |
| `data/dish-stories.json` | тексты «О блюде» для модалки, RU/EN/HY | сайт |
| `data/popular-pool.json` | id блюд для блока «Популярное» на главной | сайт |

`menu.json` и `print-menu.json` **дублируют друг друга по составу** — так исторически
сложилось (печатное меню отвязано от сайта, чтобы правки в печати не ломали сайт).
Правки цен и стоп-листа синхронизируются автоматически (см. Google-таблицу ниже),
остальное — правится в обоих файлах. Проверить расхождения:

```bash
python3 - <<'PY'
import json
a={i["name"]:i.get("price") for s in json.load(open("data/menu.json",encoding="utf-8")) for i in s["items"] if i.get("name")}
b={i["name"]:i.get("price") for s in json.load(open("data/print-menu.json",encoding="utf-8")) for i in s["items"] if i.get("name")}
print("только на сайте:", set(a)-set(b)); print("только в печати:", set(b)-set(a))
print("разные цены:", {k:(a[k],b[k]) for k in set(a)&set(b) if a[k]!=b[k]})
PY
```

---

## Сборка

Нужен Python 3 и Pillow (`pip install pillow`) — только для обработки фото.

```bash
python3 generate_menu_html.py     # меню сайта + бандл для карточек блюд
python3 generate_bar_html.py      # барная карта на сайте
python3 generate_print_menu.py    # печатная книга menu-print.html
```

Скрипты работают из любой директории (пути считаются от самого файла).

**Порядок важен:** `generate_bar_html.py` берёт переводы EN/HY из уже
сгенерированного `#menu-bar` в `menu.html`, поэтому запускать его нужно после
`generate_menu_html.py` (или просто оба подряд).

### Печатная книга: флаги

```bash
python3 generate_print_menu.py --no-bar      # без барной карты
python3 generate_print_menu.py --lang=en     # английская версия
python3 generate_print_menu.py --lang=hy     # армянская (подключается Noto Serif Armenian)
```

Переводы для печати берутся из `data/menu.json` (`name_en`, `composition_hy` …),
пропуски — из словарей `SUPPLEMENT_*` внутри `generate_print_menu.py`.
Барная карта переводится по картам из сгенерированного `#menu-bar`, поэтому перед
сборкой переведённой книги прогоняйте `generate_bar_html.py`.

### PDF

Не собирайте локально — есть workflow **«Сборка PDF для типографии»**
(вкладка Actions → Run workflow). Готовые файлы скачиваются из раздела Artifacts.

Локально (если очень нужно) — headless Chrome:

```bash
python3 -m http.server 8899 &
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=menu.pdf "http://127.0.0.1:8899/menu-print.html"
```

⚠️ Путь к папке не должен содержать кириллицу — Chrome на macOS с ней падает.
Копируйте проект во временную папку с латинским путём.

---

## Автоматика (GitHub Actions)

| Workflow | Когда | Что делает |
|---|---|---|
| `build-site.yml` | правка `data/**`, кнопка, раз в час | тянет Google-таблицу → пересобирает сайт → коммитит |
| `build-pdf.yml` | вручную | собирает 3 PDF (RU/EN/HY) и кладёт в Artifacts |

Перед публикацией `build-site.yml` **проверяет результат**: если блюд осталось
меньше 50, потерялись файлы фото или в `menu.html` мало карточек — сборка падает
и сайт не обновляется.

### Google-таблица (цены и стоп-лист)

Ресторан правит таблицу, сайт подхватывает изменения в течение часа.

1. Выгрузить заготовку: `python3 sync_from_sheet.py --export` → `data/menu-sheet-seed.csv`
2. Импортировать её в Google Sheets (Файл → Импорт → Загрузить)
3. Опубликовать: Файл → Поделиться → Опубликовать в интернете → лист, формат **CSV**
4. Ссылку вставить в `data/sheet-config.json` (`csv_url`) либо в переменную
   репозитория `SHEET_CSV_URL` (Settings → Secrets and variables → Actions → Variables)

Колонка `ID` — техническая связь со строкой меню, **менять нельзя**.
Синхронизируются только **цена** и **наличие** (`да`/`нет`). Названия, составы и фото
таблица не трогает — это осознанно: их правка требует перевода на три языка.

Проверить, что применится, ничего не меняя:

```bash
python3 sync_from_sheet.py --dry-run
```

---

## Фотографии

- Формат: **800×600** (4:3), рядом `.jpg` и `.webp`, имена — кириллический слаг
  (`img/menu/куриная-темпура.jpg`)
- В `menu.json` путь указывается **с версией**: `img/menu/файл.jpg?v=cl3`.
  При замене файла **обязательно поднимайте версию**, иначе у посетителей
  останется старая картинка из кеша
- Обработка нового фото:

```python
from PIL import Image, ImageOps, ImageEnhance
im = ImageOps.exif_transpose(Image.open("исходник.jpg").convert("RGB"))
out = ImageOps.fit(im, (800, 600), Image.LANCZOS)          # кроп по центру
out = ImageEnhance.Color(out).enhance(1.04)
out.save("img/menu/блюдо.jpg", quality=88, optimize=True)
out.save("img/menu/блюдо.webp", quality=86, method=6)
```

⚠️ **Проверяйте фото на водяные знаки.** Часть присланных клиентом снимков —
стоковые, с логотипами чужих сайтов (art-lunch.ru, IAMCOOK.RU, «Рыбоедовъ»).
Такие использовать нельзя, обрезать логотип — тоже.

Фото из `img/menu/` попадают и в фото-коллажи печатной книги (список блюд для
коллажей — в `CATALOGS` внутри `generate_print_menu.py`).

---

## Кеш-бастинг

При любой правке `style.css`, JS или картинки — поднимайте номер версии в ссылках,
иначе браузеры отдадут старое:

- `css/style.css?v=58` — во всех `*.html`
- `js/menu-dish-modal.js?v=…`, `js/popular-weekly.js?v=…` — там же
- `data/menu.json?v=41` — внутри `js/menu-dish-modal.js` и `js/popular-weekly.js`
- `img/...?v=…` — в `data/menu.json`

---

## Грабли

- **`.nojekyll` в корне обязателен.** Без него GitHub Pages запускает Jekyll, который
  падает на кириллических именах файлов, и сайт не деплоится.
- **Кириллица в путях** ломает Chrome на macOS при печати PDF (см. выше).
- **CRLF.** Часть файлов пришла с Windows. В репозитории стоит `core.autocrlf=input`;
  предупреждения git про CRLF — нормальны.
- **Unicode-нормализация имён файлов** (macOS пишет «й» как NFD): включено
  `core.precomposeunicode=true`, иначе git видит «новые» картинки на пустом месте.
- **Стоп-лист** (`"hidden": true`) скрывает блюдо только на сайте. В печатной книге
  оно остаётся — это правильно, книга печатается редко.
- **«Доме»** (десерт дня) есть только в печатном меню: на сайте карточка с
  фиксированным фото вводила бы в заблуждение.

---

## Структура

```
index.html menu.html gallery.html events.html reviews.html contacts.html
dish.html            карточка блюда (данные — из инлайн-бандла #domik-menu-bundle)
menu-print.html      печатная книга (генерируется, вручную не править)
css/style.css        сайт
css/print-menu.css   печатная книга (A4, экран = печать)
js/i18n.js           переключение RU/EN/HY
js/print-paginate.js разбивка книги на листы A4
img/menu/            фото блюд (800×600)
img/print/           фоны фото-разворотов книги
data/                все данные меню
```

## Что делать, если сайт «сломался»

1. Вкладка **Actions** — посмотреть, не упала ли последняя сборка (красный крестик)
2. Частая причина — ошибка в Google-таблице; текст ошибки виден прямо в логе шага
3. Откатить последнюю автосборку: `git revert <хеш коммита>` и запушить
