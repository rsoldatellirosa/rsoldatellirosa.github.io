// Materialize only the Lucide icons used by the landing, for standalone HTML.
// The conversation preview retains its host-provided Lucide initialization.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const lucideFolder = path.dirname(require.resolve('lucide/package.json'));
const source = path.join(__dirname, '../src');
const lucide = require(lucideFolder);
const metadata = require(path.join(lucideFolder, 'package.json'));
const template = fs.readFileSync(path.join(source, 'portfolio-cinematico-template.html'), 'utf8');
const names = [...new Set([...template.matchAll(/data-lucide="([a-z-]+)"/g)].map(match => match[1]))];
const escape = value => String(value).replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
function attributes(values) {
  return Object.entries(values).map(([name, value]) => name + '="' + escape(value) + '"').join(' ');
}
const icons = {};
for (const name of names) {
  const key = name.split('-').map(part => part[0].toUpperCase() + part.slice(1)).join('');
  const nodes = (lucide.icons || lucide)[key];
  assert(Array.isArray(nodes) && nodes.length, 'Missing Lucide icon: ' + name);
  const svgAttributes = {
    xmlns: 'http://www.w3.org/2000/svg', width: 24, height: 24, viewBox: '0 0 24 24',
    fill: 'none', stroke: 'currentColor', 'stroke-width': 2,
    'stroke-linecap': 'round', 'stroke-linejoin': 'round',
    'aria-hidden': 'true', focusable: 'false', 'data-icon': name
  };
  icons[name] = '<svg ' + attributes(svgAttributes) + '>' + nodes.map(([tag, values]) => '<' + tag + ' ' + attributes(values) + '/>').join('') + '</svg>';
}
fs.writeFileSync(path.join(source, 'portfolio-icons.json'), JSON.stringify({
  source: 'lucide ' + metadata.version,
  license: fs.readFileSync(path.join(lucideFolder, 'LICENSE'), 'utf8'),
  icons
}, null, 2) + '\n');
console.log('Prepared ' + names.length + ' static Lucide icons: ' + names.join(', '));
