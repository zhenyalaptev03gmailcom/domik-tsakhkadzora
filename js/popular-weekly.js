/**
 * Популярные блюда на главной: 5 разных из пула 20, меняются каждую ISO-неделю.
 * Работает на статическом хостинге без cron и без пересборки сайта.
 */
(function () {
  const GRID_ID = "popular-dishes-grid";
  const POOL_URL = "data/popular-pool.json?v=2";
  const MENU_URL = "data/menu.json?v=26";
  const PLACEHOLDER_IMG = "img/dish-khachapuri.jpg";
  const PICK_COUNT = 5;

  function isoWeekKey(date) {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const day = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - day);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    const week = Math.ceil(((d - yearStart) / 86400000 + 1) / 7);
    return `${d.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
  }

  /** Тот же алгоритм, что в weekly_popular.py */
  function fnvSeed(weekKey) {
    let h = 2166136261;
    for (let i = 0; i < weekKey.length; i++) {
      h ^= weekKey.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h >>> 0;
  }

  function randNext(state) {
    state[0] = (state[0] + 0x6d2b79f5) >>> 0;
    let t = state[0];
    t = Math.imul(t ^ (t >>> 15), t | 1) >>> 0;
    t = (t ^ Math.imul(t ^ (t >>> 7), t | 61)) >>> 0;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  function pickForWeek(pool, weekKey, count) {
    const state = [fnvSeed(weekKey)];
    const arr = pool.slice();
    for (let i = 0; i < count; i++) {
      const j = i + Math.floor(randNext(state) * (arr.length - i));
      const tmp = arr[i];
      arr[i] = arr[j];
      arr[j] = tmp;
    }
    return arr.slice(0, count);
  }

  function buildMenuIndex(categories) {
    const index = Object.create(null);
    categories.forEach((cat, catIdx) => {
      (cat.items || []).forEach((it) => {
        if (it.id) index[it.id] = { ...it, category_index: catIdx };
      });
    });
    return index;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function trAttrs(it) {
    if (!it.name_en && !it.name_hy) return "";
    return ` data-tr-en="${escapeHtml(it.name_en || it.name)}" data-tr-hy="${escapeHtml(it.name_hy || it.name)}"`;
  }

  function renderCard(it) {
    const img =
      it.has_image && it.local_image ? it.local_image : PLACEHOLDER_IMG;
    const name = escapeHtml(it.name);
    const price = escapeHtml(it.price);
    const href = `dish.html?id=${encodeURIComponent(it.id)}`;
    const webp = img.replace(/\.(jpe?g|png)(\?|$)/i, ".webp$2");
    return (
      `<a href="${href}" class="dish-card">` +
      `<picture><source srcset="${escapeHtml(webp)}" type="image/webp">` +
      `<img src="${escapeHtml(img)}" alt="${name}" loading="lazy" decoding="async"></picture>` +
      `<h4${trAttrs(it)}>${name}</h4>` +
      `<span class="price">${price} &#1423;</span>` +
      `</a>`
    );
  }

  async function loadPopularDishes() {
    const grid = document.getElementById(GRID_ID);
    if (!grid) return;

    try {
      const [poolRes, menuRes] = await Promise.all([
        fetch(POOL_URL, { cache: "no-cache" }),
        fetch(MENU_URL, { cache: "no-cache" }),
      ]);
      if (!poolRes.ok) throw new Error("popular-pool.json");
      if (!menuRes.ok) throw new Error("menu.json");

      const poolData = await poolRes.json();
      const menu = await menuRes.json();
      const pool = poolData.dish_ids || poolData.ids;
      if (!Array.isArray(pool) || pool.length < PICK_COUNT) {
        throw new Error("pool size");
      }

      const menuIndex = buildMenuIndex(menu);
      const weekKey = isoWeekKey(new Date());
      const picked = pickForWeek(pool, weekKey, PICK_COUNT);

      const cards = [];
      for (const id of picked) {
        const it = menuIndex[id];
        if (!it) throw new Error("missing " + id);
        cards.push(renderCard(it));
      }
      grid.innerHTML = cards.join("\n");
      grid.dataset.popularWeek = weekKey;
      // карточки отрисованы после старта i18n — применим текущий язык к новым узлам
      if (window.applyI18n) window.applyI18n(localStorage.getItem("siteLang") || "ru");
    } catch (err) {
      console.error("popular-weekly:", err);
      grid.innerHTML =
        '<p class="popular-dishes-fallback">Не удалось загрузить популярные блюда. Обновите страницу.</p>';
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadPopularDishes);
  } else {
    loadPopularDishes();
  }
})();
