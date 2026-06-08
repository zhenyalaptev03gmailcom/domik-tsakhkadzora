/**
 * Menu page: scroll reveal, active tabs, restore scroll after dish page.
 */
const SCROLL_Y_KEY = 'domik-menu-scroll-y';
const SCROLL_RESTORE_KEY = 'domik-menu-scroll-restore';
const SCROLL_CAT_KEY = 'domik-menu-scroll-cat';

function saveMenuScroll(link) {
  try {
    sessionStorage.setItem(SCROLL_Y_KEY, String(window.scrollY));
    sessionStorage.setItem(SCROLL_RESTORE_KEY, '1');
    const cat = link.closest('.menu-category');
    if (cat?.id) sessionStorage.setItem(SCROLL_CAT_KEY, cat.id);
  } catch (_) {}
}

function restoreMenuScroll(setActiveTab) {
  if (sessionStorage.getItem(SCROLL_RESTORE_KEY) !== '1') return;
  const y = parseInt(sessionStorage.getItem(SCROLL_Y_KEY) || '0', 10);
  const catId = sessionStorage.getItem(SCROLL_CAT_KEY);
  sessionStorage.removeItem(SCROLL_RESTORE_KEY);

  const run = () => {
    if (catId) {
      const section = document.getElementById(catId);
      if (section) {
        section.classList.add('is-visible');
        if (setActiveTab) setActiveTab(catId);
      }
    }
    window.scrollTo(0, Number.isFinite(y) ? y : 0);
  };

  if (document.readyState === 'complete') {
    requestAnimationFrame(() => requestAnimationFrame(run));
  } else {
    window.addEventListener('load', () => requestAnimationFrame(run), { once: true });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('a.menu-card--link').forEach((link) => {
    link.addEventListener('click', () => saveMenuScroll(link));
  });

  const categories = document.querySelectorAll('.menu-category');
  const tabs = document.querySelectorAll('.menu-tab');
  if (!categories.length) return;

  const setActiveTab = (id) => {
    tabs.forEach((tab) => {
      tab.classList.toggle('is-active', tab.getAttribute('href') === `#${id}`);
    });
  };

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (reduced) {
    categories.forEach((c) => c.classList.add('is-visible'));
    restoreMenuScroll(setActiveTab);
    return;
  }

  const reveal = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          reveal.unobserve(entry.target);
        }
      });
    },
    { root: null, rootMargin: '0px 0px -8% 0px', threshold: 0.12 }
  );

  categories.forEach((cat) => reveal.observe(cat));

  const spy = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
      if (visible[0]) {
        setActiveTab(visible[0].target.id);
      }
    },
    { rootMargin: '-40% 0px -45% 0px', threshold: [0, 0.15, 0.35] }
  );

  categories.forEach((cat) => spy.observe(cat));
  if (tabs[0]) setActiveTab(tabs[0].getAttribute('href').slice(1));

  tabs.forEach((tab) => {
    tab.addEventListener('click', (e) => {
      const id = tab.getAttribute('href');
      if (!id?.startsWith('#')) return;
      const el = document.querySelector(id);
      if (!el) return;
      e.preventDefault();
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setActiveTab(id.slice(1));
    });
  });

  restoreMenuScroll(setActiveTab);
});
