/**
 * Страница блюда: dish.html?id=...
 */
(function () {
  const BUNDLE_ID = "domik-menu-bundle";

  const labels = {
    ru: {
      composition: "Состав",
      story: "О блюде",
      noComposition: "Состав уточняйте у официанта — скоро добавим на сайт.",
      notFound: "Блюдо не найдено",
      photoSoon: "Фото скоро",
    },
    en: {
      composition: "Ingredients",
      story: "About the dish",
      noComposition: "Ask your server for ingredients — we will add details soon.",
      notFound: "Dish not found",
      photoSoon: "Photo coming soon",
    },
    hy: {
      composition: "Բաղադրություն",
      story: "Ուտեստի մասին",
      noComposition: "Հարցրեք մատուցողին — շուտով կհրապարակենք կայքում։",
      notFound: "Ուտեստը չի գտնվել",
      photoSoon: "Ֆոտո շուտով",
    },
  };

  function lang() {
    return localStorage.getItem("siteLang") || "ru";
  }

  function t(key) {
    return (labels[lang()] || labels.ru)[key] || labels.ru[key];
  }

  function getDishId() {
    return new URLSearchParams(window.location.search).get("id")?.trim() || "";
  }

  function loadBundle() {
    const embedded = document.getElementById(BUNDLE_ID);
    if (!embedded?.textContent.trim()) throw new Error("no bundle");
    return JSON.parse(embedded.textContent);
  }

  function findDish(bundle, dishId) {
    let found = null;
    let foundCat = null;
    (bundle.categories || []).forEach((cat) => {
      (cat.items || []).forEach((it) => {
        if (it.id === dishId) {
          found = it;
          foundCat = cat;
        }
      });
    });
    return { dish: found, category: foundCat, stories: bundle.stories || {} };
  }

  function showError() {
    document.getElementById("dish-content")?.setAttribute("hidden", "");
    const err = document.getElementById("dish-error");
    if (err) err.hidden = false;
    document.title = t("notFound");
  }

  function render(dish, category, stories) {
    const dishId = dish.id;
    const lng = localStorage.getItem("siteLang") || "ru";
    const name = (lng === "en" ? dish.name_en : lng === "hy" ? dish.name_hy : null) || dish.name;
    document.title = `${name} — DoMik`;
    const titleEl = document.getElementById("dish-title");
    if (titleEl) titleEl.textContent = name;

    const catEl = document.getElementById("dish-category");
    if (catEl && category) catEl.textContent =
      (lng === "en" ? category.name_en : lng === "hy" ? category.name_hy : null) || category.name || "";

    const askMap = { ru: "Уточняйте", en: "On request", hy: "ճշտել" };
    const priceEl = document.getElementById("dish-price");
    if (priceEl) priceEl.textContent =
      /\d/.test(dish.price || "") ? `${dish.price} ֏` : (dish.price ? (askMap[lng] || dish.price) : "");

    const compEl = document.getElementById("dish-composition");
    if (compEl) {
      const composition = ((lng === "en" ? dish.composition_en : lng === "hy" ? dish.composition_hy : null) || dish.composition || "").trim();
      compEl.textContent = composition || t("noComposition");
    }

    const storySection = document.getElementById("dish-story-section");
    const storyEl = document.getElementById("dish-story");
    const storyText = (stories[dishId] || dish.story || "").trim();
    if (storySection && storyEl) {
      if (storyText) {
        storyEl.textContent = storyText;
        storySection.hidden = false;
      } else {
        storySection.hidden = true;
      }
    }

    const media = document.getElementById("dish-media");
    if (media) {
      if (dish.has_image && dish.local_image) {
        const alt = dish.name.replace(/"/g, "&quot;");
        const webp = dish.local_image.replace(/\.(jpe?g|png)(\?|$)/i, ".webp$2");
        media.innerHTML =
          `<picture><source srcset="${webp}" type="image/webp">` +
          `<img src="${dish.local_image}" alt="${alt}" decoding="async"></picture>`;
      } else {
        media.innerHTML = `<div class="menu-card__ph"><span>${t("photoSoon")}</span></div>`;
      }
    }
  }

  function markMenuReturn() {
    try {
      if (document.referrer && /menu\.html/i.test(document.referrer)) {
        sessionStorage.setItem("domik-menu-scroll-restore", "1");
      }
    } catch (_) {}
  }

  function init() {
    markMenuReturn();
    const dishId = getDishId();
    if (!dishId) {
      showError();
      return;
    }
    try {
      const bundle = loadBundle();
      const { dish, category, stories } = findDish(bundle, dishId);
      if (!dish) {
        showError();
        return;
      }
      render(dish, category, stories);
      window.onLangChange = () => render(dish, category, stories);
    } catch (e) {
      console.error("dish-page:", e);
      showError();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
