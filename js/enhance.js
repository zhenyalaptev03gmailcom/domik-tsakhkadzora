/**
 * Премиальные микро-анимации: плавное появление блоков при прокрутке.
 * Не меняет разметку — вешает класс .reveal на уже существующие элементы.
 * Полностью отключается при prefers-reduced-motion: reduce.
 */
(function () {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!("IntersectionObserver" in window)) return;

  var io = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      });
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
  );

  function reveal(el, delay) {
    if (!el || el.classList.contains("reveal")) return;
    el.classList.add("reveal");
    if (delay) el.style.transitionDelay = delay + "s";
    io.observe(el);
  }

  function tagDishes(grid) {
    var cards = grid.querySelectorAll(".dish-card");
    for (var i = 0; i < cards.length; i++) {
      reveal(cards[i], (i % 5) * 0.08);
    }
  }

  function init() {
    // Галерея — со ступенчатой задержкой (раньше общего селектора)
    document.querySelectorAll(".gallery-grid img").forEach(function (el, i) {
      reveal(el, (i % 4) * 0.07);
    });

    // Главная: заголовки секций, блок «О ресторане»
    document
      .querySelectorAll(
        ".section-heading, .section-diamond, .about-split img, .about-split > div, .craft-card"
      )
      .forEach(function (el) {
        reveal(el);
      });
    // Направленный вход для блока «О ресторане» (фото слева, текст справа)
    document.querySelectorAll(".about-split img").forEach(function (el) {
      el.classList.add("reveal--left");
    });
    document.querySelectorAll(".about-split > div").forEach(function (el) {
      el.classList.add("reveal--right");
    });

    // Внутренние страницы: содержимое секций
    document
      .querySelectorAll(".page-section > .container > *, .contact-grid > *")
      .forEach(function (el) {
        reveal(el);
      });

    // Популярные блюда подгружаются асинхронно — ловим их появление
    var grid = document.getElementById("popular-dishes-grid");
    if (grid) {
      tagDishes(grid);
      new MutationObserver(function () {
        tagDishes(grid);
      }).observe(grid, { childList: true });
    }

    // Плавная смена языка: мягкое проявление переведённого текста
    document.querySelectorAll(".lang-switch button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var b = document.body;
        b.classList.remove("lang-switching");
        void b.offsetWidth; // перезапуск анимации
        b.classList.add("lang-switching");
        setTimeout(function () {
          b.classList.remove("lang-switching");
        }, 520);
      });
    });

    magnetic();
  }

  // Магнитная primary-CTA: кнопка мягко тянется к курсору (только мышь)
  function magnetic() {
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    document.querySelectorAll(".btn-book-solid").forEach(function (btn) {
      btn.addEventListener("mousemove", function (e) {
        var r = btn.getBoundingClientRect();
        var x = (e.clientX - r.left - r.width / 2) * 0.25;
        var y = (e.clientY - r.top - r.height / 2) * 0.4;
        btn.style.transform = "translate(" + x.toFixed(1) + "px," + y.toFixed(1) + "px)";
      });
      btn.addEventListener("mouseleave", function () {
        btn.style.transform = "";
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
