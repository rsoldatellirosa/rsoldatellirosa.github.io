(function () {
  const root = document.getElementById('portfolio-duas-paginas');
  if (!root) return;
  const views = Array.from(root.querySelectorAll('[data-page]'));
  let language = 'pt';
  let theme = 'dark';
  let currentPage = views.find(view => !view.hidden).dataset.page;
  // Existing links to the original homepage sections keep their destination.
  function redirectOriginalSection() {
    if (views.length !== 1 || currentPage !== 'index' || !window.location) return false;
    const originalSections = ['sobre','experiencia','competencias','projetos','anteriores','formacao','contato'];
    const section = window.location.hash.slice(1);
    if (!originalSections.includes(section)) return false;
    window.location.replace('portfolio.html' + window.location.search + '#' + section);
    return true;
  }
  if (redirectOriginalSection()) return;
  window.addEventListener('hashchange', redirectOriginalSection);

  function scrollToTarget(target) {
    const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    target.scrollIntoView({ behavior:reduceMotion ? 'instant' : 'smooth', block:'start' });
  }
  function applyPreferences() {
    root.querySelectorAll('.lang-pt').forEach(el => { el.hidden = language === 'en'; });
    root.querySelectorAll('.lang-en').forEach(el => { el.hidden = language !== 'en'; });
    root.querySelectorAll('[data-language]').forEach(button => {
      button.textContent = language === 'en' ? 'PT' : 'EN';
      button.setAttribute('aria-label', language === 'en' ? 'Ver em português' : 'View in English');
    });
    root.querySelectorAll('[data-theme]').forEach(el => {
      el.setAttribute('data-theme', theme);
      el.lang = language === 'en' ? 'en' : 'pt-BR';
    });
    root.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.setAttribute('aria-label', language === 'en' ? (theme === 'dark' ? 'Use light theme' : 'Use dark theme') : (theme === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'));
      const moon = button.querySelector('.ico-moon');
      const sun = button.querySelector('.ico-sun');
      if (moon && sun) {
        moon.hidden = theme === 'dark';
        sun.hidden = theme !== 'dark';
      } else button.textContent = theme === 'dark' ? '☀' : '☾';
    });
    root.querySelectorAll('[data-return-navigation]').forEach(nav => {
      nav.setAttribute('aria-label', language === 'en' ? 'Return navigation' : 'Navegação de retorno');
    });
  }
  function remember() {
    if (views.length === 1) {
      try { window.localStorage.setItem('rodrigo-portfolio-preferences', JSON.stringify({ language, theme })); } catch (_) {}
    }
    if (window.openai && window.openai.setWidgetState) {
      window.openai.setWidgetState({ modelContent:{ page:currentPage, language, theme }, privateContent:null }).catch(() => {});
    }
  }
  function showPage(page, anchor, scroll) {
    const view = views.find(item => item.dataset.page === page);
    if (!view) return false;
    views.forEach(item => { item.hidden = item !== view; });
    currentPage = page;
    if (scroll) {
      const target = anchor ? view.querySelector('#' + anchor) : view;
      scrollToTarget(target || view);
    }
    return true;
  }
  root.querySelectorAll('[data-language]').forEach(button => button.addEventListener('click', () => {
    language = language === 'pt' ? 'en' : 'pt'; applyPreferences(); remember();
  }));
  root.querySelectorAll('[data-theme-toggle]').forEach(button => button.addEventListener('click', () => {
    theme = theme === 'dark' ? 'light' : 'dark'; applyPreferences(); remember();
  }));
  root.querySelectorAll('a[href]').forEach(link => link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button) return;
    // Standalone pages keep native anchors, focus, URLs, history and modified clicks.
    // CSS provides smooth scrolling and progressive cross-document transitions.
    if (views.length === 1) return;
    const href = link.getAttribute('href');
    if (href.startsWith('#')) {
      const target = link.closest('[data-page]').querySelector(href);
      if (target) { event.preventDefault(); scrollToTarget(target); }
      return;
    }
    const match = /^(index|portfolio|stack)\.html(?:#([\w-]+))?$/.exec(href);
    if (!match) return;
    if (showPage(match[1], match[2], true)) { event.preventDefault(); remember(); }
  }));
  function restore(state) {
    if (!state) return;
    const saved = state.modelContent || state;
    if (saved.language === 'pt' || saved.language === 'en') language = saved.language;
    if (saved.theme === 'light' || saved.theme === 'dark') theme = saved.theme;
    if (saved.page) showPage(saved.page, null, false);
    applyPreferences();
  }
  applyPreferences();
  if (views.length === 1) {
    try { restore(JSON.parse(window.localStorage.getItem('rodrigo-portfolio-preferences'))); } catch (_) {}
  }
  if (window.openai) restore(window.openai.widgetState);
  window.addEventListener('openai:set_globals', event => {
    if (event.detail && event.detail.globals) restore(event.detail.globals.widgetState);
  });
})();
