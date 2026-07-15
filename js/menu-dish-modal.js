/**
 * Клик по карточке меню → модальное окно.
 */
(function () {
  const MODAL_ID = "dish-modal";
  const BUNDLE_ID = "domik-menu-bundle";

  const labels = {
    ru: {
      composition: "Состав",
      story: "О блюде",
      noComposition: "Состав уточняйте у официанта — скоро добавим на сайт.",
      loading: "Загрузка…",
      error: "Не удалось открыть блюдо. Обновите страницу.",
      photoSoon: "Фото скоро",
    },
    en: {
      composition: "Ingredients",
      story: "About the dish",
      noComposition: "Ask your server for ingredients — we will add details soon.",
      loading: "Loading…",
      error: "Could not open this dish. Please refresh the page.",
      photoSoon: "Photo coming soon",
    },
    hy: {
      composition: "Բաղադրություն",
      story: "Ուտեստի մասին",
      noComposition: "Հարցրեք մատուցողին — շուտով կհրապարակենք կայքում։",
      loading: "Բեռնում…",
      error: "Չհաջողվեց բացել։ Թարմացրեք էջը։",
      photoSoon: "Ֆոտո շուտով",
    },
  };

  let menuIndex = null;
  let stories = Object.create(null);
  let dataReady = null;

  function lang() {
    return localStorage.getItem("siteLang") || "ru";
  }

  function t(key) {
    return (labels[lang()] || labels.ru)[key] || labels.ru[key];
  }

  function buildIndex(categories) {
    menuIndex = Object.create(null);
    categories.forEach((cat, catIdx) => {
      (cat.items || []).forEach((it) => {
        if (it.id) menuIndex[it.id] = { ...it, category_index: catIdx };
      });
    });
  }

  function loadData() {
    if (dataReady) return dataReady;
    dataReady = (async () => {
      const embedded = document.getElementById(BUNDLE_ID);
      if (embedded && embedded.textContent.trim()) {
        const bundle = JSON.parse(embedded.textContent);
        buildIndex(bundle.categories || []);
        stories = bundle.stories || {};
        return;
      }
      const root = window.location.pathname.replace(/[^/]+$/, "");
      const menuUrl = new URL("data/menu.json?v=22", window.location.origin + root).href;
      const storiesUrl = new URL("data/dish-stories.json", window.location.origin + root).href;
      const [menuRes, storiesRes] = await Promise.all([
        fetch(menuUrl, { cache: "no-cache" }),
        fetch(storiesUrl, { cache: "no-cache" }),
      ]);
      if (!menuRes.ok) throw new Error("menu.json");
      buildIndex(await menuRes.json());
      if (storiesRes.ok) {
        const raw = await storiesRes.json();
        stories = Object.fromEntries(
          Object.entries(raw).filter(([k]) => !String(k).startsWith("_"))
        );
      }
    })();
    return dataReady;
  }

  function getModal() {
    return document.getElementById(MODAL_ID);
  }

  function showModalShell(titleText) {
    const modal = getModal();
    if (!modal) return null;
    modal.querySelector("#dish-modal-title").textContent = titleText || "";
    modal.querySelector("#dish-modal-price").textContent = "";
    modal.querySelector("#dish-modal-composition").textContent = t("loading");
    modal.querySelector("#dish-modal-story").textContent = "";
    modal.querySelector(".dish-modal__story-block").hidden = true;
    modal.querySelector(".dish-modal__media").innerHTML =
      '<div class="menu-card__ph"><span>…</span></div>';
    modal.classList.add("active");
    modal.removeAttribute("hidden");
    document.body.classList.add("modal-open");
    return modal;
  }

  function fillModal(dishId) {
    const modal = getModal();
    const it = menuIndex[dishId];
    if (!modal || !it) {
      if (modal) modal.querySelector("#dish-modal-composition").textContent = t("error");
      return;
    }

    const lng = lang();
    modal.querySelector("#dish-modal-title").textContent =
      (lng === "en" ? it.name_en : lng === "hy" ? it.name_hy : null) || it.name;
    const askMap = { ru: "Уточняйте", en: "On request", hy: "ճշտել" };
    modal.querySelector("#dish-modal-price").textContent =
      /\d/.test(it.price || "") ? `${it.price} ֏` : (it.price ? (askMap[lng] || it.price) : "");

    const composition = ((lng === "en" ? it.composition_en : lng === "hy" ? it.composition_hy : null) || it.composition || "").trim();
    modal.querySelector("#dish-modal-composition").textContent =
      composition || t("noComposition");
    modal.querySelector(".dish-modal__composition-block h3").textContent =
      t("composition");

    const st = stories[dishId];
    const storyText = ((st && typeof st === "object" ? (st[lng] || st.ru) : st) || it.story || "").trim();
    const storyBlock = modal.querySelector(".dish-modal__story-block");
    if (storyText) {
      modal.querySelector("#dish-modal-story").textContent = storyText;
      storyBlock.hidden = false;
      storyBlock.querySelector("h3").textContent = t("story");
    } else {
      storyBlock.hidden = true;
    }

    const media = modal.querySelector(".dish-modal__media");
    if (it.has_image && it.local_image) {
      media.innerHTML = `<img src="${it.local_image}" alt="">`;
    } else {
      media.innerHTML =
        `<div class="menu-card__ph"><span>${t("photoSoon")}</span></div>`;
    }
  }

  function closeModal() {
    const modal = getModal();
    if (!modal) return;
    modal.classList.remove("active");
    modal.setAttribute("hidden", "");
    document.body.classList.remove("modal-open");
  }

  function openDish(card) {
    const dishId = card.dataset.dishId;
    if (!dishId) return;
    const name =
      card.querySelector(".menu-card__name")?.textContent?.trim() ||
      card.getAttribute("aria-label")?.replace(/^Подробнее:\s*/i, "") ||
      "";
    showModalShell(name);
    loadData()
      .then(() => fillModal(dishId))
      .catch((err) => {
        console.error("menu-dish-modal:", err);
        const modal = getModal();
        if (modal) modal.querySelector("#dish-modal-composition").textContent = t("error");
      });
  }

  function bindCards() {
    document.querySelectorAll(".menu-card[data-dish-id]").forEach((card) => {
      card.addEventListener("click", (e) => { e.preventDefault(); openDish(card); });
    });

    document.querySelectorAll(".menu-page").forEach((page) => {
      page.addEventListener("selectstart", (e) => {
        if (e.target.closest(".menu-card[data-dish-id]")) e.preventDefault();
      });
    });
  }

  function bindModal() {
    const modal = getModal();
    if (!modal) return;
    modal.querySelector(".modal-close")?.addEventListener("click", closeModal);
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("active")) closeModal();
    });
  }

  function init() {
    bindCards();
    bindModal();
    loadData().catch(() => {});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
