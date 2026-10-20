// Execute controls against generated HTML. Checks DOM logic, not browser layout
// or external-site availability. Run npm ci to install the development parser.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { parse } = require('node-html-parser');
const script = fs.readFileSync(path.join(__dirname, '../src/portfolio-duas-paginas.js'), 'utf8');
const previewName = '..';

function load(file, storage = new Map(), state, options = {}) {
  const tree = parse(options.html || fs.readFileSync(file, 'utf8'));
  const root = tree.querySelector('#portfolio-duas-paginas');
  const listeners = new WeakMap();
  const events = {}, scrolls = [], scrollOptions = [], saved = [];
  for (const element of [root, ...root.querySelectorAll('*')]) {
    Object.defineProperties(element, {
      hidden: { get() { return this.hasAttribute('hidden'); }, set(value) { value ? this.setAttribute('hidden', '') : this.removeAttribute('hidden'); } },
      dataset: { get() { return { page: this.getAttribute('data-page') }; } },
      lang: { get() { return this.getAttribute('lang'); }, set(value) { this.setAttribute('lang', value); } },
      textContent: { get() { return this.text; }, set(value) { this.set_content(String(value)); } }
    });
    element.addEventListener = function (type, callback) {
      const handlers = listeners.get(this) || {};
      (handlers[type] ||= []).push(callback);
      listeners.set(this, handlers);
    };
    element.scrollIntoView = function (options) { scrolls.push(this); scrollOptions.push(options); };
    element.closest = function (selector) {
      assert.equal(selector, '[data-page]');
      for (let parent = this; parent; parent = parent.parentNode) {
        if (parent.hasAttribute && parent.hasAttribute('data-page')) return parent;
      }
      return null;
    };
  }
  vm.runInNewContext(script, {
    document: { getElementById: id => tree.querySelector('#' + id) },
    window: {
      location: options.location,
      matchMedia: query => ({ matches:query === '(prefers-reduced-motion: reduce)' && !!options.reducedMotion }),
      addEventListener: (type, callback) => { events[type] = callback; },
      localStorage: { getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value) },
      openai: { widgetState: state, setWidgetState: value => { saved.push(value); return Promise.resolve(); } }
    }
  });
  function click(element, overrides = {}) {
    assert(element, 'Control must exist in generated HTML');
    const callbacks = (listeners.get(element) || {}).click;
    assert(callbacks && callbacks.length, 'Missing handler: ' + element.toString().slice(0, 150));
    let prevented = false;
    callbacks.forEach(callback => callback({ button: 0, preventDefault() { prevented = true; }, ...overrides }));
    return prevented;
  }
  return { root, click, scrolls, scrollOptions, events, saved };
}

function checkPreferences(app, language, theme) {
  const { root } = app;
  for (const element of root.querySelectorAll('.lang-pt')) assert.equal(element.hidden, language === 'en');
  for (const element of root.querySelectorAll('.lang-en')) assert.equal(element.hidden, language !== 'en');
  for (const button of root.querySelectorAll('[data-language]')) assert.equal(button.textContent, language === 'en' ? 'PT' : 'EN');
  for (const element of root.querySelectorAll('[data-theme]')) {
    assert.equal(element.getAttribute('data-theme'), theme);
    assert.equal(element.lang, language === 'en' ? 'en' : 'pt-BR');
  }
  for (const button of root.querySelectorAll('[data-theme-toggle]')) {
    assert(button.getAttribute('aria-label'));
    const moon = button.querySelector('.ico-moon'), sun = button.querySelector('.ico-sun');
    if (moon && sun) {
      assert.equal(moon.hidden, theme === 'dark');
      assert.equal(sun.hidden, theme !== 'dark');
    }
  }
  for (const nav of root.querySelectorAll('[data-return-navigation]')) {
    assert.equal(nav.getAttribute('aria-label'), language === 'en' ? 'Return navigation' : 'Navegação de retorno');
  }
}

// Exercise the shared multi-view fallback with current standalone markup,
// without rewriting the older inline conversation artifact.
const combined = '<div id="portfolio-duas-paginas">' + ['index','portfolio','stack'].map(name => {
  const page = parse(fs.readFileSync(path.join(__dirname, previewName, name + '.html'), 'utf8')).querySelector('[data-page]');
  if (name !== 'index') page.setAttribute('hidden','');
  return page.toString();
}).join('') + '</div>';
const app = load(null, new Map(), undefined, { html:combined });
const { root, click } = app;
const pages = root.querySelectorAll('[data-page]');
const links = root.querySelectorAll('a[href]');
const buttons = root.querySelectorAll('button');
assert.equal(pages.length, 3);
assert.equal(buttons.length, 6);
checkPreferences(app, 'pt', 'dark');
for (const button of root.querySelectorAll('[data-language]')) {
  click(button); checkPreferences(app, 'en', 'dark');
  click(button); checkPreferences(app, 'pt', 'dark');
}
for (const button of root.querySelectorAll('[data-theme-toggle]')) {
  click(button); checkPreferences(app, 'pt', 'light');
  click(button); checkPreferences(app, 'pt', 'dark');
}
function visiblePage() {
  const visible = pages.filter(page => !page.hidden);
  assert.equal(visible.length, 1);
  return visible[0];
}
function selectPage(name) {
  click(links.find(link => link.getAttribute('href') === name + '.html'));
  assert.equal(visiblePage().dataset.page, name);
}
let localLinks = 0, externalLinks = 0;
for (const link of links) {
  const href = link.getAttribute('href'), source = link.closest('[data-page]');
  selectPage(source.dataset.page);
  const local = /^(index|portfolio|stack)\.html(?:#([\w-]+))?$/.exec(href);
  if (local || href.startsWith('#')) {
    assert(click(link), 'Local navigation must be handled: ' + href);
    const targetPage = local ? local[1] : source.dataset.page;
    const anchor = local ? local[2] : href.slice(1);
    assert.equal(visiblePage().dataset.page, targetPage, href);
    const target = anchor ? visiblePage().querySelector('#' + anchor) : visiblePage();
    assert(target, href);
    assert.equal(app.scrolls.at(-1), target, 'Wrong scroll destination: ' + href);
    assert.equal(app.scrollOptions.at(-1).behavior, 'smooth');
    localLinks++;
  } else {
    const url = new URL(href);
    assert(['https:', 'mailto:'].includes(url.protocol), href);
    if (url.protocol === 'https:') {
      assert(url.hostname, href);
      assert.equal(link.getAttribute('target'), '_blank');
      assert(link.getAttribute('rel').split(/\s+/).includes('noopener'));
    } else assert.equal(url.pathname, 'rsoldatellirosa@gmail.com');
    assert.equal(click(link), false, 'External links retain native navigation: ' + href);
    externalLinks++;
  }
}
selectPage('index');
assert.equal(click(links.find(link => link.getAttribute('href') === 'portfolio.html'), { ctrlKey: true }), false);
assert.equal(visiblePage().dataset.page, 'index');
const teaching = root.querySelector('#entrada-ensino'), product = root.querySelector('#entrada-aulia');
assert(teaching.parentNode.childNodes.indexOf(teaching) < product.parentNode.childNodes.indexOf(product));
app.events['openai:set_globals']({ detail: { globals: { widgetState: { modelContent: { page: 'portfolio', language: 'en', theme: 'light' } } } } });
assert.equal(visiblePage().dataset.page, 'portfolio');
checkPreferences(app, 'en', 'light');
selectPage('stack');
checkPreferences(app, 'en', 'light');
assert.equal(app.saved.at(-1).modelContent.page, 'stack');

const storage = new Map();
let standalone = load(path.join(__dirname, previewName, 'index.html'), storage);
standalone.click(standalone.root.querySelector('[data-language]'));
standalone.click(standalone.root.querySelector('[data-theme-toggle]'));
for (const page of ['portfolio', 'stack', 'index']) {
  standalone = load(path.join(__dirname, previewName, page + '.html'), storage);
  checkPreferences(standalone, 'en', 'light');
  for (const link of standalone.root.querySelectorAll('a[href]')) {
    const href = link.getAttribute('href');
    const destination = /^(index|portfolio|stack)\.html/.exec(href);
    if (destination || href.startsWith('#')) assert.equal(standalone.click(link), false, 'Standalone pages keep native anchors, focus and browser history');
  }
  const returns = standalone.root.querySelector('[data-return-navigation]');
  const skip = standalone.root.querySelector('.portfolio-skip');
  assert.equal(standalone.root.querySelector('a,button'), skip, 'Skip link must be the first keyboard action');
  const main = standalone.root.querySelector(skip.getAttribute('href'));
  assert(main && main.tagName === 'MAIN' && main.getAttribute('tabindex') === '-1');
  assert.equal(standalone.root.querySelectorAll('main').length, 1);
  const top = returns.querySelector('a[href^="#"]');
  assert(top, 'A return-to-top action must be present at the end');
  const target = standalone.root.querySelector(top.getAttribute('href'));
  assert(target && target.getAttribute('tabindex') === '-1', 'Top destination must accept native anchor focus');
  const home = returns.querySelector('a[href="index.html"]');
  assert.equal(!!home, page !== 'index', 'Detailed pages also provide a separate return to the landing page');
  for (const icon of returns.querySelectorAll('svg')) assert.equal(icon.getAttribute('aria-hidden'), 'true');
}
const reduced = load(null, new Map(), undefined, { html:combined, reducedMotion:true });
reduced.click(reduced.root.querySelector('a[href="#entrada-ensino"]'));
assert.equal(reduced.scrollOptions.at(-1).behavior, 'instant', 'Reduced motion skips animated scroll in the embedded fallback');
const navigationCss = fs.readFileSync(path.join(__dirname,'../src/portfolio-navegacao.css'),'utf8');
assert(navigationCss.includes('html { scroll-behavior:smooth; }'));
assert(navigationCss.includes('html { scroll-behavior:auto; }'));
assert(navigationCss.includes('@view-transition { navigation:auto; }'));
assert(navigationCss.includes('animation:none!important'));
assert(navigationCss.includes('position:sticky'));
assert(navigationCss.includes('scroll-margin-top:160px'));
assert(navigationCss.includes('min-height:44px'));
assert(navigationCss.includes('a:focus-visible'));
console.log('PASS: generated HTML; ' + buttons.length + ' buttons, ' + localLinks + ' local links, ' + externalLinks + ' external/mail links.');
console.log('PASS: PT/EN, themes, page/section destinations, return links, restored state and standalone preferences.');
console.log('PASS: footer return destinations, native standalone navigation, smooth/reduced scrolling, focus targets and navigation motion styles.');
const exportedLanding = parse(fs.readFileSync(path.join(__dirname, previewName, 'index.html'), 'utf8'));
const iconTiles = exportedLanding.querySelectorAll('.entrada-fact-icon');
assert.equal(iconTiles.length, 6);
const expectedIcons = ['book-open', 'list-checks', 'users-round', 'calendar-days', 'code-xml', 'clipboard-check'];
iconTiles.forEach((tile, index) => {
  const svg = tile.querySelector('svg');
  assert(svg, 'Empty feature icon tile');
  assert.equal(svg.getAttribute('data-icon'), expectedIcons[index]);
  assert.equal(svg.getAttribute('stroke'), 'currentColor');
  assert.equal(svg.getAttribute('aria-hidden'), 'true');
  assert(svg.querySelectorAll('path,rect,circle,line,polyline,polygon').length > 0, 'Empty SVG geometry');
});
assert.equal(exportedLanding.querySelectorAll('i[data-lucide]').length, 0, 'Standalone HTML must not depend on host icon initialization');
assert(exportedLanding.querySelector('.entrada-location svg[data-icon="map-pin"]'));
console.log('PASS: six nonempty, theme-aware static feature icons and location marker; no unresolved icon placeholders.');

const incoming = [];
for (const section of ['sobre','experiencia','competencias','projetos','anteriores','formacao','contato']) {
  load(path.join(__dirname, previewName, 'index.html'), new Map(), undefined, {
    location: { hash:'#' + section, search:'?ref=linkedin', replace:url => incoming.push(url) }
  });
  assert.equal(incoming.at(-1), 'portfolio.html?ref=linkedin#' + section);
}
const preservedIncoming = incoming.length;
for (const hash of ['', '#entrada-ensino', '#entrada-aulia', '#entrada-contato', '#portfolio-entrada']) {
  load(path.join(__dirname, previewName, 'index.html'), new Map(), undefined, {
    location: { hash, search:'', replace:url => incoming.push(url) }
  });
}
assert.equal(incoming.length, preservedIncoming, 'Landing links and the homepage keep their original URL');
load(path.join(__dirname, previewName, 'portfolio.html'), new Map(), undefined, {
  location: { hash:'#experiencia', search:'', replace:url => incoming.push(url) }
});
assert.equal(incoming.length, preservedIncoming, 'The full portfolio must not redirect to itself');
console.log('PASS: old homepage section links preserve their destination and referral parameters; no redirect loop.');
