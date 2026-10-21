from pathlib import Path
from html.parser import HTMLParser
import base64
import hashlib
import json
import re
import shutil
import sys

folder = Path(__file__).resolve().parents[1]/'src'
original_folder = folder/'original'
original_hashes = {name: hashlib.sha256((original_folder/name).read_bytes()).hexdigest() for name in ('index.html','stack.html','foto.jpg')}
baseline = (folder/'portfolio-fiel/index.html').read_text(encoding='utf-8')
stack_baseline = (folder/'portfolio-fiel/stack.html').read_text(encoding='utf-8')
original = (original_folder/'index.html').read_text(encoding='utf-8')
original_stack = (original_folder/'stack.html').read_text(encoding='utf-8')
favicon = '<link rel="icon" href="favicon.ico?v=rs1" sizes="16x16 32x32 48x48 64x64"><link rel="icon" type="image/png" sizes="256x256" href="assets/favicon-rs.png">'
for favicon_asset in ('favicon.ico', 'assets/favicon-rs.png'):
    assert (folder.parent/favicon_asset).is_file(), 'Missing RS favicon: '+favicon_asset
reference = True
template_name = 'portfolio-cinematico-template.html' if reference else 'portfolio-entrada-template.html'
css_name = 'portfolio-cinematico.css' if reference else 'portfolio-entrada.css'
output_name = 'portfolio-landing-referencia' if reference else 'portfolio-duas-paginas'

def document_parts(document):
    css = re.search(r'<style>(.*?)</style>',document,re.S).group(1)
    css = re.sub(r'html,body\{[^}]*\}', '', css)
    body = re.search(r'<body>(.*?)</body>',document,re.S).group(1)
    body = re.sub(r'<script>.*?</script>', '', body, flags=re.S)
    return css, body

detail_css, detail = document_parts(baseline)
stack_css, stack = document_parts(stack_baseline)
stack_css = stack_css.replace('#portfolio-fiel', '#portfolio-stack')
stack = stack.replace('id="portfolio-fiel"', 'id="portfolio-stack"').replace('id="langbtn"', 'id="stack-langbtn"').replace('id="themebtn"', 'id="stack-themebtn"')
stack = stack.replace('href="index.html', 'href="portfolio.html')

# Add navigation and stable deep links without removing or rewriting original copy.
home_link = '<a href="index.html" class="duplo-home"><span class="lang-pt">← Início</span><span class="lang-en" hidden>← Home</span></a>'
detail = detail.replace('<nav>', '<nav>' + home_link, 1)
detail = detail.replace('<a class="aulia-feature"', '<a id="aulia" class="aulia-feature"', 1)
jobs = list(re.finditer('<article class="job">', detail))
assert len(jobs) == 2
detail = detail[:jobs[1].start()] + detail[jobs[1].start():].replace('<article class="job">','<article id="ensino" class="job">',1)

headline = re.search(r'<div class="headline">(.*?)</div>', detail, re.S).group(1)
portrait = re.search(r'<img class="foto"[^>]*>',detail).group(0).replace('class="foto"','class="entrada-photo"').replace(' width="132" height="132"','')
stack_markup = re.search(r'(<p class="stacklead">.*?)</header>',detail,re.S).group(1)
feature = re.search(r'<a id="aulia" class="aulia-feature".*?</a>', detail,re.S).group(0)
logo = re.search(r'<svg class="af-logo".*?</svg>',feature,re.S).group(0)
aulia_description = re.search(r'<p class="af-desc">(.*?)</p>', feature,re.S).group(1)
teaching = re.search(r'<article id="ensino".*?</article>',detail,re.S).group(0)
teaching_description = re.search(r'<p>(.*?)</p>',teaching,re.S).group(1)
landing = (folder/template_name).read_text(encoding='utf-8')
replacements = {'HEADLINE':headline,'PORTRAIT':portrait,'STACK':stack_markup,'LOGO':logo}
hapolo_logo_source = folder/'hapolo-logo.png'
hapolo_logo_uri = 'data:image/png;base64,' + base64.b64encode(hapolo_logo_source.read_bytes()).decode() if reference else None
if reference:
    replacements['HAPOLO_LOGO'] = hapolo_logo_uri
if not reference:
    replacements.update({'AULIA_DESCRIPTION':aulia_description,'TEACHING_DESCRIPTION':teaching_description})
for key, value in replacements.items():
    assert landing.count('{{'+key+'}}') == 1
    landing = landing.replace('{{'+key+'}}',value)
assert '{{' not in landing

def mark_controls(markup):
    return re.sub(r'(<button[^>]*id="(?:stack-)?)(langbtn|themebtn)(")',lambda match:match.group(0) + (' data-language' if match[2]=='langbtn' else ' data-theme-toggle'),markup)

detail, stack = mark_controls(detail), mark_controls(stack)
landing_css = (folder/css_name).read_text(encoding='utf-8')
script = (folder/'portfolio-duas-paginas.js').read_text(encoding='utf-8')
navigation_css = (folder/'portfolio-navegacao.css').read_text(encoding='utf-8')
page_roots = {'index':'portfolio-entrada','portfolio':'portfolio-fiel','stack':'portfolio-stack'}

def add_return_navigation(name, markup):
    # Add controls separately so all original text continues to be compared below.
    arrow = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 19V5m-6 6 6-6 6 6"/></svg>'
    home_arrow = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M19 12H5m6-6-6 6 6 6"/></svg>'
    home = '' if name == 'index' else '<a href="index.html">'+home_arrow+'<span class="lang-pt">Voltar ao início</span><span class="lang-en" hidden>Back to home</span></a>'
    top_pt, top_en = ('Voltar ao início','Back to top') if name == 'index' else ('Voltar ao topo','Back to top')
    navigation = '<nav class="portfolio-return" data-return-navigation aria-label="Navegação de retorno">'+home+'<a class="portfolio-return-top" href="#'+page_roots[name]+'">'+arrow+'<span class="portfolio-return-label"><span class="lang-pt">'+top_pt+'</span><span class="lang-en" hidden>'+top_en+'</span></span></a></nav>'
    before, closing, after = markup.rpartition('</div>')
    assert closing and not after.strip(), 'Expected one outer page root'
    content_id = name+'-conteudo'
    if name == 'index':
        assert before.count('<main>') == 1
        before = before.replace('<main>', '<main id="'+content_id+'" tabindex="-1">', 1)
    else:
        before, changes = re.subn(r'<div class="wrap">(\s*<header class="(?:hero|head)">)', '<main class="wrap" id="'+content_id+'" tabindex="-1">'+r'\1', before, count=1)
        assert changes == 1
        wrap_content, wrap_end, trailing = before.rpartition('</div>')
        assert wrap_end and not trailing.strip(), 'Expected main content wrapper'
        before = wrap_content + '</main>' + trailing
        before = before.replace('<h4>', '<h3>').replace('</h4>', '</h3>')
    result = before + navigation + closing + after
    result = result.replace('id="'+page_roots[name]+'"', 'id="'+page_roots[name]+'" tabindex="-1"', 1)
    skip = '<a class="portfolio-skip" href="#'+content_id+'"><span class="lang-pt">Pular para o conteúdo</span><span class="lang-en" hidden>Skip to content</span></a>'
    result, changes = re.subn(r'(<div id="'+page_roots[name]+'"[^>]*>)', lambda match:match[0]+skip, result, count=1)
    assert changes == 1
    if name == 'index':
        result = result.replace('href="index.html"', 'href="#'+page_roots[name]+'"')
    return result

# New cases are additive; the original detail text is still verified below.
bandwidth_case = (folder/'portfolio-bandwidth-case.html').read_text(encoding='utf-8').strip()
bandwidth_project = (folder/'portfolio-bandwidth-project.html').read_text(encoding='utf-8').strip()
case_anchor = '<div class="probs-title"><span class="lang-pt">Problemas que resolvi</span><span class="lang-en" hidden>Problems I solved</span></div>'
assert detail.count(case_anchor) == 2
detail_with_cases = detail.replace(case_anchor, case_anchor+'\n'+bandwidth_case, 1)
assert detail_with_cases.count('<div class="repos">') == 1
detail_with_cases = detail_with_cases.replace('<div class="repos">', '<div class="repos">\n'+bandwidth_project, 1)
assert detail_with_cases.replace('\n'+bandwidth_case, '', 1).replace('\n'+bandwidth_project, '', 1) == detail
views = {name:add_return_navigation(name,markup) for name,markup in {'index':landing,'portfolio':detail_with_cases,'stack':stack}.items()}
sharing_heads = json.loads((folder/'page-sharing-heads.json').read_text(encoding='utf-8'))
styles = {'index':landing_css,'portfolio':detail_css,'stack':stack_css}
styles = {name:css.replace('.skillgroup h4', '.skillgroup :is(h3,h4)')+'\n'+navigation_css for name,css in styles.items()}

def wrap_view(name,markup,hidden=False):
    return '<div data-page="'+name+'"'+(' hidden' if hidden else '')+'>'+markup+'</div>'

inline_css = '\n'.join(css.replace('.skillgroup h4', '.skillgroup :is(h3,h4)') for css in (detail_css,stack_css,landing_css))+'\n'+navigation_css
inline = '<style>'+inline_css+'</style>\n<div id="portfolio-duas-paginas">'+''.join(wrap_view(name,markup,name!='index') for name,markup in views.items())+'</div>\n<script>'+script+'</script>\n'
output_folder = folder.parent
output_folder.mkdir(exist_ok=True)
icon_catalog = json.loads((folder/'portfolio-icons.json').read_text(encoding='utf-8')) if reference else None
if icon_catalog:
    (output_folder/'assets').mkdir(exist_ok=True)
    (output_folder/'assets/LUCIDE-LICENSE.txt').write_text(icon_catalog['license'],encoding='utf-8')
if reference:
    shutil.copyfile(hapolo_logo_source, output_folder/'assets/hapolo-logo.png')
portrait_source = folder/'portfolio-retrato.jpg'
portrait_asset = 'assets/retrato-rodrigo-4000.jpg'
use_high_resolution_portrait = reference and portrait_source.is_file()
if use_high_resolution_portrait:
    (output_folder/'assets').mkdir(exist_ok=True)
    shutil.copyfile(portrait_source, output_folder/portrait_asset)

def standalone_portrait(match):
    tag = re.sub(r'\s(?:width|height)="[^"]*"', '', match.group(0))
    tag = re.sub(r'src="[^"]*"', 'src="'+portrait_asset+'"', tag)
    return tag[:-1] + ' width="4000" height="6000" decoding="async" fetchpriority="high">'

for name,markup in views.items():
    page_css = styles[name]
    if reference:
        markup = markup.replace('src="'+hapolo_logo_uri+'"', 'src="assets/hapolo-logo.png"')
    if icon_catalog:
        markup = re.sub(r'<i data-lucide="([a-z-]+)"[^>]*></i>', lambda match:icon_catalog['icons'][match[1]], markup)
        assert 'data-lucide=' not in markup, 'Unrendered standalone icon'
        if name == 'index':
            assert len(re.findall(r'<span class="entrada-fact-icon"[^>]*><svg ',markup)) == 6
    if use_high_resolution_portrait:
        markup = re.sub(r'<img class="(?:foto|entrada-photo)"[^>]*>', standalone_portrait, markup)
        if name == 'portfolio':
            page_css += '\n#portfolio-fiel .foto{object-position:50% 8%}'
    page = '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rodrigo Soldatelli da Rosa'+(' | Portfólio completo' if name=='portfolio' else ' | Stack' if name=='stack' else ' | Infraestrutura &amp; DevOps')+'</title>'+sharing_heads[name]+favicon+'<style>'+page_css+'\nhtml,body{margin:0;background:#111319}\n#portfolio-duas-paginas [hidden]{display:none!important}</style></head><body><div id="portfolio-duas-paginas">'+wrap_view(name,markup)+'</div><script>'+script+'</script></body></html>'
    assert page.count(favicon) == 1, 'RS favicon must be included once'
    (output_folder/(name+'.html')).write_text(page,encoding='utf-8')

class Inspect(HTMLParser):
    def __init__(self):
        super().__init__(); self.text=[]; self.ids=[]; self.links=[]; self.suppressed=0
    def handle_starttag(self,tag,attrs):
        attributes=dict(attrs)
        if tag in ('style','script'): self.suppressed+=1
        if 'id' in attributes: self.ids.append(attributes['id'])
        if tag=='a': self.links.append(attributes.get('href',''))
    def handle_endtag(self,tag):
        if tag in ('style','script'): self.suppressed-=1
    def handle_data(self,data):
        if not self.suppressed and data.strip(): self.text.append(' '.join(data.split()))

def inspect(markup):
    parser=Inspect(); parser.feed(markup); return parser

# Compare directly with the original files, allowing only the intact Aulia card relocation.
original_body = document_parts(original)[1]
original_feature = re.search(r'<a class="aulia-feature".*?</a>',original_body,re.S).group(0)
detail_feature = re.search(r'<a id="aulia" class="aulia-feature".*?</a>',detail,re.S).group(0)
assert inspect(original_body.replace(original_feature,'')).text == inspect(detail.replace(home_link,'').replace(detail_feature,'')).text, 'Original portfolio copy changed or missing'
assert inspect(original_feature).text == inspect(detail_feature).text, 'Original Aulia copy changed'
assert inspect(document_parts(original_stack)[1]).text == inspect(stack).text, 'Original stack copy changed'
for language in ('pt','en'):
    assert original_body.count('class="lang-'+language+'"') == detail.replace(home_link,'').count('class="lang-'+language+'"')
original_external = [href for href in inspect(original_body).links if href.startswith(('https:','mailto:'))]
detail_external = [href for href in inspect(detail).links if href.startswith(('https:','mailto:'))]
assert sorted(original_external) == sorted(detail_external), 'Original external link changed or missing'

# Preserve the already selected layout as well as the original text.
assert inspect(document_parts(baseline)[1]).text == inspect(detail.replace(home_link,'')).text
assert inspect(document_parts(stack_baseline)[1]).text == inspect(stack).text
assert re.findall(r'<section id="([^"]+)"',detail) == re.findall(r'<section id="([^"]+)"',original)
landing_stack=re.search(r'<div class="stackstrip">(.*?)</header>',document_parts(baseline)[1],re.S).group(1)
assert landing_stack in landing
assert landing_stack.count('<svg')==14
if reference:
    assert landing.index('<section id="entrada-ensino"') < landing.index('<section id="entrada-aulia"')
    assert '\u2014' not in ' '.join(inspect(landing).text), 'Em dash in landing copy'
assert inspect(headline).text == inspect(re.search(r'<div class="headline">(.*?)</div>',original,re.S).group(1)).text
inspection=inspect(inline)
assert len(inspection.ids)==len(set(inspection.ids)), 'Duplicate IDs'
page_ids={name:set(inspect(markup).ids) for name,markup in views.items()}
for name, source in {'index':landing,'portfolio':detail_with_cases,'stack':stack}.items():
    augmented = re.sub(r'<nav class="portfolio-return".*?</nav>', '', views[name], flags=re.S)
    augmented = re.sub(r'<a class="portfolio-skip".*?</a>', '', augmented, flags=re.S)
    assert inspect(augmented).text == inspect(source).text, 'Navigation must not rewrite existing content'
for name,markup in views.items():
    for href in inspect(markup).links:
        if href.startswith('#'): assert href[1:] in page_ids[name], (name,href)
        match=re.fullmatch(r'(index|portfolio|stack)\.html(?:#([\w-]+))?',href)
        if match:
            assert match[1] in views
            if match[2]: assert match[2] in page_ids[match[1]],href
assert len(inline.encode())<1_000_000
for name,old_hash in original_hashes.items(): assert hashlib.sha256((original_folder/name).read_bytes()).hexdigest()==old_hash
assert '<!DOCTYPE' not in inline and '<body' not in inline
assert '\\"' not in inline
print('PASS: full PT/EN portfolio and stack text compared directly with original source files; unchanged.')
print('PASS: 14 original stack icons and original professional headline preserved on landing.')
print('PASS: unique IDs; all local page links and deep links resolve; originals unchanged.')
print('Inline bytes:',len(inline.encode()))
print('Pages:',output_folder)
if icon_catalog:
    print('PASS: six feature icons and the location icon embedded as static SVG; no runtime icon dependency.')
if use_high_resolution_portrait:
    assert hashlib.sha256(portrait_source.read_bytes()).hexdigest() == hashlib.sha256((output_folder/portrait_asset).read_bytes()).hexdigest()
    print('PASS: high-resolution portrait copied without changing the image; used on landing and full portfolio.')
