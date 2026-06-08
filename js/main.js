document.addEventListener('DOMContentLoaded', () => {
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
    burger.addEventListener('click', () => nav.classList.toggle('open'));
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => nav.classList.remove('open')));
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

    // drag-to-scroll on desktop (phones use native momentum swipe)
    let down = false, startX = 0, startScroll = 0, moved = 0;
    row.addEventListener('pointerdown', e => {
      if (e.pointerType === 'touch') return;
      down = true; moved = 0; startX = e.clientX; startScroll = row.scrollLeft;
      row.classList.add('is-dragging');
      try { row.setPointerCapture(e.pointerId); } catch (_) {}
      e.preventDefault();
    });
    row.addEventListener('pointermove', e => {
      if (!down) return;
      const dx = e.clientX - startX; moved += Math.abs(dx);
      row.scrollLeft = startScroll - dx;
    });
    const release = () => { if (down) { down = false; row.classList.remove('is-dragging'); } };
    row.addEventListener('pointerup', release);
    row.addEventListener('pointercancel', release);
    // if the pointer actually dragged, swallow the card click so it doesn't open the dish
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
