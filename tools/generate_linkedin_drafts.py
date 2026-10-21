"""Generate reviewable drafts after publication. This script never calls LinkedIn."""
import argparse
import base64
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from portfolio_cases import load_cases, case_text

ROOT = Path(__file__).resolve().parents[1]
STATE_BRANCH = 'codex/linkedin-state'
STATE_PATH = 'generated-cases.json'
SITE = 'https://rsoldatellirosa.github.io/'


def request_json(url, *, data=None, token=None, method=None):
    headers = {'Accept': 'application/json', 'User-Agent': 'portfolio-linkedin-drafts'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if data is not None:
        headers['Content-Type'] = 'application/json'
    request = Request(url, data=json.dumps(data).encode() if data is not None else None,
                      headers=headers, method=method)
    with urlopen(request, timeout=90) as response:
        return json.load(response)


class GitHubState:
    def __init__(self, repository, token):
        if repository != 'rsoldatellirosa/rsoldatellirosa.github.io':
            raise ValueError('Unexpected portfolio repository')
        self.base = 'https://api.github.com/repos/' + repository
        self.token = token
        self.sha = None

    def read(self):
        try:
            file = request_json(self.base + '/contents/' + STATE_PATH + '?ref=' + STATE_BRANCH,
                                token=self.token)
        except HTTPError as error:
            if error.code == 404:
                return {}
            raise
        self.sha = file['sha']
        return json.loads(base64.b64decode(file['content']))

    def save(self, records, source_sha):
        if not re.fullmatch(r'[0-9a-f]{40}', source_sha):
            raise ValueError('A full source commit SHA is required')
        try:
            request_json(self.base + '/git/ref/heads/' + STATE_BRANCH, token=self.token)
        except HTTPError as error:
            if error.code != 404:
                raise
            request_json(self.base + '/git/refs', token=self.token,
                         data={'ref': 'refs/heads/' + STATE_BRANCH, 'sha': source_sha})
        # Read again to merge records and use the current contents SHA.
        current = self.read()
        current.update(records)
        payload = {'message': 'chore: registra rascunhos LinkedIn gerados',
                   'content': base64.b64encode((json.dumps(current, indent=2, ensure_ascii=False) + '\n').encode()).decode(),
                   'branch': STATE_BRANCH}
        if self.sha:
            payload['sha'] = self.sha
        request_json(self.base + '/contents/' + STATE_PATH, token=self.token, data=payload, method='PUT')


def pending_cases(cases, state, selected='', force=False):
    if selected and not any(case['id'] == selected for case in cases):
        raise ValueError('Unknown case ID')
    return [case for case in cases if (not selected or case['id'] == selected)
            and (force or case['id'] not in state)]


def numbers(text):
    return {Decimal(value.replace(',', '.')).normalize()
            for value in re.findall(r'(?<!\w)\d+(?:[.,]\d+)?', text)}


def validate_post(text, source):
    if not isinstance(text, str) or not 120 <= len(text) <= 2200:
        raise ValueError('Draft length outside allowed range')
    if '\u2014' in text or re.search(r'https?://|www\.', text, re.I):
        raise ValueError('Draft must not contain em dashes or model-generated links')
    if not numbers(text).issubset(numbers(source)):
        raise ValueError('Draft introduced undocumented numbers')
    if re.search(r'sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|\b(?:\d{1,3}\.){3}\d{1,3}\b', text):
        raise ValueError('Draft contains a possible credential or IP address')
    return text.strip()


def rewrite_with_ai(source, readme, title, api_key):
    rules = (ROOT / '.github/prompts/linkedin.md').read_text(encoding='utf-8')
    data = request_json('https://api.openai.com/v1/responses', token=api_key, data={
        'model': os.environ.get('PORTFOLIO_POST_MODEL') or 'gpt-5-mini',
        'instructions': rules,
        'input': json.dumps({'title': title, 'approved_portfolio_text': source,
                             'untrusted_repository_readme': readme}, ensure_ascii=False),
        'store': False,
        'reasoning': {'effort': 'low'},
        'max_output_tokens': 2500,
        'text': {'format': {'type': 'json_schema', 'name': 'linkedin_draft', 'strict': True,
                           'schema': {'type': 'object', 'properties': {'post': {'type': 'string'}},
                                      'required': ['post'], 'additionalProperties': False}}},
    })
    if data.get('status') != 'completed':
        raise ValueError('Model response was incomplete')
    content = ''.join(part['text'] for output in data.get('output', [])
                      for part in output.get('content', []) if part.get('type') == 'output_text')
    return validate_post(json.loads(content)['post'], source)


def safe_error_reason(error):
    """Only expose allowlisted codes or our own validation messages, never API bodies."""
    if isinstance(error, HTTPError):
        code = ''
        try:
            code = json.loads(error.read(8192)).get('error', {}).get('code', '')
        except Exception:
            pass
        allowed = {'insufficient_quota', 'invalid_api_key', 'model_not_found',
                   'rate_limit_exceeded', 'insufficient_permissions', 'billing_hard_limit_reached'}
        suffix = ' / ' + code if isinstance(code, str) and code in allowed else ''
        return f'HTTP {error.code}' + suffix
    allowed_messages = {
        'Model response was incomplete', 'Draft length outside allowed range',
        'Draft must not contain em dashes or model-generated links',
        'Draft introduced undocumented numbers', 'Draft contains a possible credential or IP address',
    }
    if type(error) is ValueError and str(error) in allowed_messages:
        return str(error)
    return type(error).__name__


def draft_case(root, case, api_key='', fetch=request_json):
    source = case_text(root, case)
    mode, warning = 'texto aprovado, sem IA', ''
    text = source.replace('. ', '.\n\n')
    if api_key:
        try:
            readme_data = fetch('https://api.github.com/repos/' + case['repository'] + '/readme')
            readme = base64.b64decode(readme_data['content']).decode('utf-8')[:20000]
            text = rewrite_with_ai(source, readme, case['title'], api_key)
            mode = 'reescrito com IA, aguardando revisão'
        except Exception as error:
            # Do not log external responses, credentials or untrusted repository text.
            warning = 'A IA não concluiu um rascunho válido (' + safe_error_reason(error) + '); foi usado o texto aprovado.'
    text = validate_post(text, source)
    url = SITE + 'portfolio.html#' + case['id']
    post = (text + '\n\nIncluí esse caso no meu portfólio e deixei o projeto documentado no GitHub.'
            '\n\nPortfólio: ' + url + '\nProjeto: https://github.com/' + case['repository'])
    if len(post) > 2800:
        raise ValueError('Final draft is too long')
    return post, {'mode': mode, 'warning': warning, 'source': url,
                  'source_sha256': hashlib.sha256(source.encode()).hexdigest()}


def write_drafts(root, cases, out, api_key=''):
    out.mkdir(parents=True, exist_ok=True)
    records = {}
    for case in cases:
        post, info = draft_case(root, case, api_key)
        (out / (case['id'] + '.txt')).write_text(post + '\n', encoding='utf-8')
        records[case['id']] = info
    if records:
        (out / 'LEIA-ME.txt').write_text(
            'Rascunhos para revisão. Nenhum texto foi publicado no LinkedIn.\n'
            'Confira valores, período e redação antes de publicar.\n'
            'Os arquivos são artefatos do repositório público; não use dados privados.\n\n' +
            '\n'.join(ident + ': ' + info['mode'] + ('; ' + info['warning'] if info['warning'] else '')
                      for ident, info in records.items()), encoding='utf-8')
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case-id', default='')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--github-state', action='store_true')
    parser.add_argument('--mark-generated', action='store_true')
    parser.add_argument('--out', type=Path, default=ROOT / 'linkedin-drafts')
    parser.add_argument('--plan', type=Path, default=ROOT / 'linkedin-plan.json')
    args = parser.parse_args()
    state = GitHubState(os.environ.get('GITHUB_REPOSITORY', ''), os.environ.get('GH_TOKEN', '')) if args.github_state else None
    if args.mark_generated:
        if not state:
            raise ValueError('GitHub state is required for this operation')
        records = json.loads(args.plan.read_text(encoding='utf-8'))
        run_url = os.environ['DRAFT_RUN_URL']
        for info in records.values():
            info.update({'run_url': run_url, 'generated_at': datetime.now(timezone.utc).isoformat()})
        state.save(records, os.environ['SOURCE_SHA'])
        return
    cases = pending_cases(load_cases(ROOT), state.read() if state else {}, args.case_id, args.force)
    records = write_drafts(ROOT, cases, args.out, os.environ.get('OPENAI_API_KEY', ''))
    args.plan.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if output := os.environ.get('GITHUB_OUTPUT'):
        with open(output, 'a', encoding='utf-8') as file:
            file.write('has_drafts=' + str(bool(records)).lower() + '\n')
    if summary := os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(summary, 'a', encoding='utf-8') as file:
            file.write('## Rascunhos LinkedIn\n\n' + (f'{len(records)} caso(s) preparado(s). Baixe o artefato `rascunhos-linkedin` nesta execução.\n'
                       if records else 'Nenhum caso novo. Os casos registrados já têm rascunho.\n'))
            if not os.environ.get('OPENAI_API_KEY'):
                file.write('\nModo sem IA: texto aprovado do portfólio. Chave de API opcional.\n')
    print(f'{len(records)} rascunho(s) preparado(s); nenhum envio ao LinkedIn.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Não foi possível concluir a geração: ' + type(error).__name__, file=sys.stderr)
        sys.exit(1)
