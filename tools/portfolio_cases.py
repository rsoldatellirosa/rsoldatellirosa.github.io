"""Shared catalog for additive portfolio cases and LinkedIn draft generation."""
import json
from html.parser import HTMLParser
from pathlib import Path
import re


def load_cases(root):
    root = Path(root).resolve()
    cases = json.loads((root / 'src/portfolio-cases.json').read_text(encoding='utf-8'))
    seen = set()
    for case in cases:
        ident = case['id']
        if not re.fullmatch(r'[a-z][a-z0-9-]{2,79}', ident) or ident in seen:
            raise ValueError('Invalid or duplicate case ID')
        seen.add(ident)
        if not re.fullmatch(r'rsoldatellirosa/[A-Za-z0-9_.-]+', case['repository']):
            raise ValueError('Repository must belong to rsoldatellirosa')
        for key in ('case_source', 'project_source'):
            path = (root / case[key]).resolve()
            if not path.is_relative_to(root / 'src') or path.suffix != '.html' or not path.is_file():
                raise ValueError('Case sources must be HTML files inside src/')
        if not case['title'].strip():
            raise ValueError('Case title is required')
    return cases


class PortugueseText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.levels = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        inherited = self.levels[-1] if self.levels else False
        active = inherited or 'lang-pt' in attrs.get('class', '').split()
        if tag not in ('br', 'img', 'hr', 'input', 'meta', 'link'):
            self.levels.append(active)

    def handle_endtag(self, tag):
        if self.levels:
            self.levels.pop()
        self.parts.append(' ')

    def handle_data(self, data):
        if self.levels and self.levels[-1]:
            self.parts.append(data)


def case_text(root, case):
    html = (Path(root) / case['case_source']).read_text(encoding='utf-8')
    # The draft uses the published case paragraph, not navigation labels or English.
    paragraph = re.search(r'<p>(.*?)</p>', html, re.S)
    if not paragraph:
        raise ValueError('Case paragraph not found')
    parser = PortugueseText()
    parser.feed(paragraph[1])
    text = ' '.join(''.join(parser.parts).split())
    text = re.sub(r'\s*Ver diagnóstico e código no GitHub\s*↗\s*$', '', text)
    if not text:
        raise ValueError('Portuguese case text not found')
    return text
