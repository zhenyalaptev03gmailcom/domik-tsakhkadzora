/**
 * Рейтинг и отзывы с карт — data/map-reviews.json (см. fetch_map_reviews.py).
 */
(function () {
  const DATA_URL = "data/map-reviews.json";
  const SOURCE_LABELS = {
    yandex: { ru: "Яндекс", en: "Yandex", hy: "Yandex" },
    google: { ru: "Google", en: "Google", hy: "Google" },
    tripadvisor: { ru: "Tripadvisor", en: "Tripadvisor", hy: "Tripadvisor" },
  };
  const SOURCE_ORDER = ["yandex", "google", "tripadvisor"];

  function lang() {
    return document.documentElement.lang || localStorage.getItem("siteLang") || "ru";
  }

  function t(key, fallback) {
    const pack = window.SITE_I18N && window.SITE_I18N[lang()];
    return (pack && pack[key]) || fallback;
  }

  function labelForSource(id) {
    const L = SOURCE_LABELS[id] || { ru: id };
    return L[lang()] || L.ru || id;
  }

  function fmtRating(v) {
    if (v == null || v === "") return "";
    const n = Number(v);
    if (Number.isNaN(n)) return "";
    return n.toFixed(1);
  }

  function stars(rating) {
    const r = Math.round(Math.max(0, Math.min(5, Number(rating) || 0)));
    return "★".repeat(r) + "☆".repeat(5 - r);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  var RU_MONTH={"Январь":["January","Հունվար"],"Февраль":["February","Փետրվար"],"Март":["March","Մարտ"],"Апрель":["April","Ապրիլ"],"Май":["May","Մայիս"],"Июнь":["June","Հունիս"],"Июль":["July","Հուլիս"],"Август":["August","Օգոստոս"],"Сентябрь":["September","Սեպտեմբեր"],"Октябрь":["October","Հոկտեմբեր"],"Ноябрь":["November","Նոյեմբեր"],"Декабрь":["December","Դեկտեմբեր"]};
  function locDate(x){ var l=lang(); if(l==="ru"||!x) return x; var i=l==="en"?0:1; return x.replace(/Январь|Февраль|Март|Апрель|Май|Июнь|Июль|Август|Сентябрь|Октябрь|Ноябрь|Декабрь/, function(m){ return RU_MONTH[m]?RU_MONTH[m][i]:m; }); }

  function buildChip(id, meta) {
    const rating = fmtRating(meta.rating);
    if (!rating) return "";
    const count = meta.review_count != null ? Number(meta.review_count) : null;
    const url = meta.url || "#";
    const countText =
      count != null && !Number.isNaN(count)
        ? t("maps.reviewsCount", "{n} отзывов").replace("{n}", String(count))
        : "";
    return (
      '<a class="map-rating-chip map-rating-chip--' +
      escapeHtml(id) +
      '" href="' +
      escapeHtml(url) +
      '" target="_blank" rel="noopener noreferrer">' +
      '<span class="map-rating-chip__brand">' +
      escapeHtml(labelForSource(id)) +
      "</span>" +
      '<span class="map-rating-chip__score">' +
      escapeHtml(rating) +
      "</span>" +
      '<span class="map-rating-chip__stars" aria-hidden="true">' +
      stars(meta.rating) +
      "</span>" +
      (countText
        ? '<span class="map-rating-chip__count">' + escapeHtml(countText) + "</span>"
        : "") +
      "</a>"
    );
  }

  function renderBar(root, data) {
    const sources = data.sources || {};
    const chips = SOURCE_ORDER.map((k) => (sources[k] ? buildChip(k, sources[k]) : "")).filter(Boolean);
    if (!chips.length) {
      root.hidden = true;
      return;
    }
    root.innerHTML =
      '<div class="map-rating-bar__inner">' +
      chips.join("") +
      '<a href="reviews.html" class="map-rating-bar__more">' +
      escapeHtml(t("maps.allReviews", "Все отзывы →")) +
      "</a></div>";
    root.hidden = false;
  }

  function renderReviewsList(root, data) {
    const sources = data.sources || {};
    const summary = [];
    SOURCE_ORDER.forEach((k) => {
      if (sources[k] && sources[k].rating != null) {
        summary.push(buildChip(k, sources[k]));
      }
    });

    const reviews = data.reviews || [];
    let html = "";
    if (summary.length) {
      html +=
        '<div class="reviews-summary map-rating-bar__inner reviews-summary--page">' +
        summary.join("") +
        "</div>";
    }

    if (!reviews.length) {
      html +=
        '<p class="reviews-empty">' +
        escapeHtml(t("maps.noReviews", "Пока нет загруженных отзывов. Запустите обновление на сервере.")) +
        "</p>";
    } else {
      html += '<div class="reviews-list">';
      reviews.forEach((rv) => {
        const src = labelForSource(rv.source || "");
        const date = rv.date ? '<span class="review-card__date">' + escapeHtml(locDate(rv.date)) + "</span>" : "";
        html +=
          '<article class="review-card review-card--' +
          escapeHtml(rv.source || "") +
          '">' +
          '<div class="review-card__head">' +
          '<span class="review-card__source">' +
          escapeHtml(src) +
          "</span>" +
          date +
          "</div>" +
          '<div class="stars">' +
          (rv.stars || stars(rv.rating)) +
          "</div>" +
          "<p>" +
          escapeHtml(rv.text) +
          "</p>" +
          '<p class="review-card__author">— ' +
          escapeHtml(rv.author || t("maps.guest", "Гость")) +
          "</p></article>";
      });
      html += "</div>";
    }

    if (data.updated_at) {
      const d = new Date(data.updated_at);
      const when = Number.isNaN(d.getTime()) ? data.updated_at : d.toLocaleDateString(lang() === "hy" ? "hy-AM" : lang() === "en" ? "en-GB" : "ru-RU");
      html +=
        '<p class="reviews-updated">' +
        escapeHtml(t("maps.updated", "Обновлено: {date}").replace("{date}", when)) +
        "</p>";
    }

    root.innerHTML = html;
  }

  function load() {
    return fetch(DATA_URL, { cache: "no-store" })
      .then((r) => {
        if (!r.ok) throw new Error(String(r.status));
        return r.json();
      })
      .catch(() => null);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const bar = document.getElementById("map-rating-bar");
    const list = document.getElementById("reviews-dynamic");
    if (!bar && !list) return;

    load().then((data) => {
      if (!data) return;
      var draw = function () { if (bar) renderBar(bar, data); if (list) renderReviewsList(list, data); };
      draw();
      var prev = window.onLangChange;
      window.onLangChange = function () { if (prev) prev.apply(null, arguments); draw(); };
    });
  });
})();
