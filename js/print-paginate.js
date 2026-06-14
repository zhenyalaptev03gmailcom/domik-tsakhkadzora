/* Печатное меню-книга: клиентская постраничная вёрстка A4.
   Берёт плоский поток элементов из #book и раскладывает его по листам .sheet
   фиксированного размера A4, заполняя каждый лист сверху вниз. Экран = печать.
   Заголовки/баннер помечены классом .flow-keep — они не «осиротеют» внизу листа. */
(function () {
  'use strict';

  function mmToPx(mm) {
    var d = document.createElement('div');
    d.style.cssText = 'position:absolute;visibility:hidden;height:' + mm + 'mm;';
    document.body.appendChild(d);
    var px = d.getBoundingClientRect().height;
    d.parentNode.removeChild(d);
    return px;
  }

  function paginate() {
    var book = document.getElementById('book');
    if (!book || book.classList.contains('is-paginated')) return;

    var items = Array.prototype.slice.call(book.children);
    book.textContent = '';
    book.classList.add('is-paginated');

    var sheet = null, inner = null;
    var contentSheets = [];

    function addSheet() {
      sheet = document.createElement('div');
      sheet.className = 'sheet';
      inner = document.createElement('div');
      inner.className = 'sheet__inner';
      sheet.appendChild(inner);
      book.appendChild(sheet);
      contentSheets.push(sheet);
    }

    addSheet();

    for (var i = 0; i < items.length; i++) {
      var node = items[i];

      // Обложка — отдельный полноформатный лист
      if (node.classList && node.classList.contains('book-cover')) {
        if (inner.childNodes.length === 0) {        // текущий пустой лист отдаём под обложку
          book.removeChild(sheet);
          contentSheets.pop();
        }
        var cs = document.createElement('div');
        cs.className = 'sheet sheet--cover';
        cs.appendChild(node);
        book.appendChild(cs);
        addSheet();                                  // свежий лист под следующий контент
        continue;
      }

      inner.appendChild(node);

      if (inner.scrollHeight > inner.clientHeight + 1) {   // переполнение
        inner.removeChild(node);
        // перенести вместе с ним хвостовые «неотрывные» элементы (заголовки/баннер)
        var carry = [];
        while (inner.lastElementChild &&
               inner.lastElementChild.classList.contains('flow-keep')) {
          carry.unshift(inner.lastElementChild);
          inner.removeChild(inner.lastElementChild);
        }
        addSheet();
        for (var c = 0; c < carry.length; c++) inner.appendChild(carry[c]);
        inner.appendChild(node);
        // если одиночный элемент выше листа — оставляем как есть (overflow:hidden обрежет)
      }
    }

    // убрать последний пустой лист
    if (inner && inner.childNodes.length === 0) {
      book.removeChild(sheet);
      contentSheets.pop();
    }

    // номера страниц (обложка без номера)
    for (var p = 0; p < contentSheets.length; p++) {
      var f = document.createElement('div');
      f.className = 'sheet__folio';
      f.textContent = String(p + 1);
      contentSheets[p].appendChild(f);
    }

    fitToWidth();
  }

  // Экранная подгонка под узкие окна (на печать не влияет)
  function fitToWidth() {
    var book = document.getElementById('book');
    if (!book) return;
    var sheetW = mmToPx(210);
    var avail = document.documentElement.clientWidth - 24;
    book.style.zoom = avail < sheetW ? (avail / sheetW) : '';
  }

  function start() {
    var run = function () { try { paginate(); } catch (e) { /* оставляем плоский поток как фолбэк */ } };
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(run);
      setTimeout(run, 1500);            // подстраховка, если fonts.ready молчит
    } else {
      window.addEventListener('load', run);
    }
    window.addEventListener('resize', fitToWidth);
    // пагинировать перед печатью, если ещё не успели
    window.addEventListener('beforeprint', run);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
