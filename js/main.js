document.addEventListener('DOMContentLoaded', () => {
  // Floating WhatsApp button (all pages) — quick booking/question from anywhere
  if (!document.querySelector('.wa-float')) {
    const wa = document.createElement('a');
    wa.className = 'wa-float';
    wa.href = 'https://wa.me/37495505656?text=' + encodeURIComponent('Здравствуйте! Хочу забронировать столик в «Домик Цахкадзора».');
    wa.target = '_blank'; wa.rel = 'noopener';
    wa.setAttribute('aria-label', 'Написать в WhatsApp');
    wa.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.5 14.4c-.3-.15-1.7-.83-2-.93-.26-.1-.45-.15-.64.15-.19.29-.73.92-.9 1.1-.16.2-.33.22-.62.07-.3-.15-1.25-.46-2.38-1.47-.88-.78-1.47-1.75-1.64-2.04-.17-.3-.02-.46.13-.6.13-.13.3-.34.44-.51.15-.17.2-.3.3-.49.1-.2.05-.37-.02-.52-.08-.15-.64-1.55-.88-2.12-.23-.56-.47-.48-.64-.49l-.55-.01c-.19 0-.5.07-.76.36-.26.29-1 .98-1 2.38 0 1.4 1.02 2.76 1.17 2.95.14.2 2 3.05 4.85 4.28.68.29 1.2.46 1.62.59.68.21 1.3.18 1.79.11.55-.08 1.68-.69 1.92-1.35.24-.66.24-1.23.17-1.35-.07-.12-.26-.19-.55-.34z M12 2a10 10 0 00-8.55 15.2L2 22l4.92-1.4A10 10 0 1012 2zm0 18.2a8.2 8.2 0 01-4.18-1.14l-.3-.18-2.92.83.78-2.85-.2-.3A8.2 8.2 0 1112 20.2z"/></svg>';
    document.body.appendChild(wa);
  }

  const header = document.querySelector('.site-header') || document.querySelector('header');
  const progress = document.createElement('div');
  progress.className = 'scroll-progress';
  document.body.appendChild(progress);
  let progressTicking = false;
  const onScroll = () => {
    if (header) header.classList.toggle('scrolled', window.scrollY > 40);
    if (!progressTicking) {
      progressTicking = true;
      requestAnimationFrame(() => {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        progress.style.transform = 'scaleX(' + (max > 0 ? window.scrollY / max : 0) + ')';
        progressTicking = false;
      });
    }
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });

  const burger = document.querySelector('.burger');
  const nav = document.querySelector('nav');
  if (burger && nav) {
    burger.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      if (header) header.classList.toggle('nav-open', open);
    });
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      nav.classList.remove('open');
      if (header) header.classList.remove('nav-open');
    }));
  }

  const currentPage = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('nav a').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPage || (currentPage === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });

  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const lang = localStorage.getItem('siteLang') || 'ru';
      const okMsg = window.SITE_I18N?.[lang]?.['toast.form'] || 'Спасибо! Мы свяжемся с вами в ближайшее время.';
      const action = form.getAttribute('action');
      const key = form.querySelector('[name="access_key"]')?.value || '';

      // Демо-режим: пока приём не настроен (нет action или ключ-заглушка) — просто благодарим.
      if (!action || !key || key.indexOf('ВАШ-КЛЮЧ') !== -1) {
        showToast(okMsg);
        form.reset();
        return;
      }

      const btn = form.querySelector('button[type="submit"]');
      const orig = btn ? btn.textContent : '';
      if (btn) { btn.disabled = true; btn.textContent = '…'; }
      try {
        const res = await fetch(action, {
          method: 'POST',
          headers: { Accept: 'application/json' },
          body: new FormData(form),
        });
        if (res.ok) {
          showToast(okMsg);
          form.reset();
        } else {
          showToast('Не удалось отправить заявку. Позвоните нам, пожалуйста.');
        }
      } catch (_) {
        showToast('Нет связи с сервером. Проверьте интернет или позвоните нам.');
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = orig; }
      }
    });
  });

  document.querySelectorAll('.menu-tab').forEach(tab => {
    tab.addEventListener('click', e => {
      const id = tab.getAttribute('href');
      if (!id || !id.startsWith('#')) return;
      const el = document.querySelector(id);
      if (!el) return;
      e.preventDefault();
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  const modal = document.getElementById('gallery-modal');
  if (modal) {
    document.querySelectorAll('.gallery-grid img').forEach(img => {
      img.addEventListener('click', () => {
        modal.querySelector('img').src = img.src;
        modal.classList.add('active');
      });
    });
    modal.querySelector('.modal-close')?.addEventListener('click', () => modal.classList.remove('active'));
    modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });
  }

  // Премиальный набор цен: узкий неразрывный пробел в числах + подчинённый знак ֏
  formatPrices(document);
  setTimeout(() => formatPrices(document), 0); // ловит цену на странице блюда (ставится скриптом позже)
  const priceGrid = document.getElementById('popular-dishes-grid');
  if (priceGrid) new MutationObserver(() => formatPrices(priceGrid)).observe(priceGrid, { childList: true });

  // Menu category rows -> elegant carousel: arrows (desktop) + drag + native swipe (phone)
  document.querySelectorAll('.menu-grid').forEach(row => {
    // wrap the row so the arrows + edge fades can sit over it
    const wrap = document.createElement('div');
    wrap.className = 'menu-row';
    row.parentNode.insertBefore(wrap, row);
    wrap.appendChild(row);

    const makeArrow = dir => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'menu-arrow menu-arrow--' + dir;
      b.setAttribute('aria-label', dir === 'prev' ? 'Предыдущие блюда' : 'Следующие блюда');
      b.innerHTML = dir === 'prev'
        ? '<svg viewBox="0 0 24 24" fill="none"><path d="M15 5l-7 7 7 7" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="none"><path d="M9 5l7 7-7 7" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>';
      return b;
    };
    const prev = makeArrow('prev'), next = makeArrow('next');
    wrap.append(prev, next);

    const pageStep = () => Math.max(240, row.clientWidth * 0.85);
    prev.addEventListener('click', () => row.scrollBy({ left: -pageStep(), behavior: 'smooth' }));
    next.addEventListener('click', () => row.scrollBy({ left: pageStep(), behavior: 'smooth' }));

    const update = () => {
      const max = row.scrollWidth - row.clientWidth - 4;
      const atStart = row.scrollLeft <= 4;
      const atEnd = row.scrollLeft >= max;
      prev.classList.toggle('is-hidden', atStart);
      next.classList.toggle('is-hidden', atEnd || max <= 0);
      wrap.classList.toggle('can-prev', !atStart);
      wrap.classList.toggle('can-next', !atEnd && max > 0);
    };
    row.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update, { passive: true });
    update();

    // drag-to-scroll on desktop (phones use native momentum swipe).
    // ВАЖНО: захватываем указатель (setPointerCapture) ТОЛЬКО после реального
    // движения. Если захватить на pointerdown, по спецификации Pointer Events
    // обычный клик перенаправляется на саму строку, и карточка не открывается.
    let down = false, startX = 0, startScroll = 0, moved = 0, captured = false;
    row.addEventListener('pointerdown', e => {
      if (e.pointerType === 'touch' || e.button !== 0) return;
      down = true; moved = 0; captured = false; startX = e.clientX; startScroll = row.scrollLeft;
    });
    row.addEventListener('pointermove', e => {
      if (!down) return;
      const dx = e.clientX - startX;
      moved = Math.abs(dx);
      if (!captured && moved > 6) {          // началось настоящее перетаскивание
        captured = true;
        row.classList.add('is-dragging');
        try { row.setPointerCapture(e.pointerId); } catch (_) {}
      }
      if (captured) { row.scrollLeft = startScroll - dx; if (e.cancelable) e.preventDefault(); }
    });
    const release = () => { if (down) { down = false; captured = false; row.classList.remove('is-dragging'); } };
    row.addEventListener('pointerup', release);
    row.addEventListener('pointercancel', release);
    // не давать нативному перетаскиванию картинки/текста перехватывать скролл-драг
    row.addEventListener('dragstart', e => { if (down) e.preventDefault(); });
    // если реально тащили — гасим клик по карточке, чтобы не открыть блюдо
    row.addEventListener('click', e => { if (moved > 6) { e.preventDefault(); e.stopPropagation(); } }, true);
  });
});

function showToast(msg) {
  let toastEl = document.querySelector('.toast');
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.className = 'toast';
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  setTimeout(() => toastEl.classList.remove('show'), 4000);
}

function formatPrices(root) {
  (root || document).querySelectorAll('.price, .dish-detail__price, .dish-modal__price').forEach(el => {
    if (el.dataset.fmt) return;
    let h = el.innerHTML;
    h = h.replace(/(\d)\s(\d{3})(?!\d)/g, '$1 $2');            // 4 000 → 4 000 (узкий nbsp, без переноса)
    h = h.replace(/\s*֏/g, ' <span class="cur">֏</span>');      // знак драма — мельче и подчинённый
    el.innerHTML = h;
    el.dataset.fmt = '1';
  });
}
