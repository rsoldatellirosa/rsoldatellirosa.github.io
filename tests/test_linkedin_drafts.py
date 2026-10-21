"""Offline tests for draft generation, validation and durable deduplication."""
import base64
import json
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import generate_linkedin_drafts as drafts
from portfolio_cases import load_cases, case_text


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.case = load_cases(ROOT)[0]

    def test_catalog_points_to_the_published_case_and_repository(self):
        for case in load_cases(ROOT):
            markup = (ROOT / case['case_source']).read_text(encoding='utf-8')
            project = (ROOT / case['project_source']).read_text(encoding='utf-8')
            self.assertIn('id="' + case['id'] + '"', markup)
            self.assertIn('https://github.com/' + case['repository'], project)

    def test_extracts_portuguese_only_and_keeps_the_result(self):
        text = case_text(ROOT, self.case)
        self.assertIn('113,43', text)
        self.assertNotIn('I investigated', text)
        self.assertNotIn('Ver diagnóstico', text)
        self.assertNotIn('<strong>', text)

    def test_base_draft_needs_neither_key_nor_network(self):
        with patch.object(drafts, 'request_json', side_effect=AssertionError('No network')):
            post, info = drafts.draft_case(ROOT, self.case)
        self.assertIn('113,43', post)
        self.assertIn('portfolio.html#' + self.case['id'], post)
        self.assertIn('https://github.com/' + self.case['repository'], post)
        self.assertLess(len(post), 2800)
        self.assertIn('sem IA', info['mode'])

    def test_processed_case_is_not_generated_again(self):
        self.assertEqual(drafts.pending_cases([self.case], {self.case['id']: {}}), [])
        self.assertEqual(drafts.pending_cases([self.case], {self.case['id']: {}}, force=True), [self.case])

    def test_new_case_is_selected_without_reprocessing_existing_case(self):
        new = dict(self.case, id='novo-caso')
        self.assertEqual(drafts.pending_cases([self.case, new], {self.case['id']: {}}), [new])

    def test_unknown_case_is_rejected(self):
        with self.assertRaises(ValueError):
            drafts.pending_cases([self.case], {}, selected='nao-existe')

    def test_source_paths_cannot_escape_src(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'src').mkdir()
            bad = dict(self.case, case_source='../outside.html')
            (root / 'src/portfolio-cases.json').write_text(json.dumps([bad]))
            with self.assertRaises(ValueError):
                load_cases(root)

    def test_undocumented_numbers_and_em_dash_are_rejected(self):
        text = case_text(ROOT, self.case)
        for addition in [' Economia anual de 1361,16 dólares.', ' — Resultado garantido.']:
            with self.assertRaises(ValueError):
                drafts.validate_post(text + addition, text)

    def test_model_cannot_inject_links_or_ips(self):
        text = case_text(ROOT, self.case)
        for addition in [' https://example.invalid', ' 10.1.2.3']:
            with self.assertRaises(ValueError):
                drafts.validate_post(text + addition, text)

    def test_ai_failure_falls_back_to_approved_text(self):
        def unavailable(*args, **kwargs):
            raise RuntimeError('simulado')
        post, info = drafts.draft_case(ROOT, self.case, 'chave-ficticia', fetch=unavailable)
        self.assertIn('113,43', post)
        self.assertIn('não concluiu', info['warning'])
        self.assertIn('sem IA', info['mode'])

    def test_ai_response_is_validated(self):
        source = case_text(ROOT, self.case)
        response = {'status': 'completed', 'output': [{'content': [
            {'type': 'output_text', 'text': json.dumps({'post': source})}]}]}
        with patch.object(drafts, 'ROOT', ROOT), patch.object(drafts, 'request_json', return_value=response) as api:
            self.assertEqual(drafts.rewrite_with_ai(source, 'contexto', self.case['title'], 'chave-ficticia'), source)
            payload = api.call_args.kwargs['data']
            self.assertFalse(payload['store'])
            self.assertEqual(payload['text']['format']['type'], 'json_schema')
            self.assertNotIn('tools', payload)

    def test_incomplete_model_response_is_rejected(self):
        with patch.object(drafts, 'request_json', return_value={'status': 'incomplete'}):
            with self.assertRaises(ValueError):
                drafts.rewrite_with_ai('texto', 'contexto', 'titulo', 'chave-ficticia')

    def test_files_are_written_only_in_the_selected_output_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'drafts'
            records = drafts.write_drafts(ROOT, [self.case], out)
            self.assertEqual(set(records), {self.case['id']})
            self.assertTrue((out / (self.case['id'] + '.txt')).is_file())
            self.assertIn('Nenhum texto foi publicado', (out / 'LEIA-ME.txt').read_text(encoding='utf-8'))


class StateTests(unittest.TestCase):
    def test_missing_state_is_empty_but_api_errors_are_not(self):
        state = drafts.GitHubState('rsoldatellirosa/rsoldatellirosa.github.io', 'token-ficticio')
        for code in [404, 403, 500]:
            with patch.object(drafts, 'request_json', side_effect=HTTPError('https://api.github.com', code, '', {}, None)):
                if code == 404:
                    self.assertEqual(state.read(), {})
                else:
                    with self.assertRaises(HTTPError):
                        state.read()

    def test_state_updates_merge_records_and_use_expected_sha(self):
        state = drafts.GitHubState('rsoldatellirosa/rsoldatellirosa.github.io', 'token-ficticio')
        existing = {'old-case': {'run_url': 'old-run'}}
        encoded = base64.b64encode(json.dumps(existing).encode()).decode()
        with patch.object(drafts, 'request_json', side_effect=[{}, {'sha': 'blob-sha', 'content': encoded}, {}]) as api:
            state.save({'new-case': {'run_url': 'new-run'}}, 'a' * 40)
            payload = api.call_args.kwargs['data']
            saved = json.loads(base64.b64decode(payload['content']))
            self.assertEqual(set(saved), {'old-case', 'new-case'})
            self.assertEqual(payload['sha'], 'blob-sha')
            self.assertEqual(payload['branch'], 'codex/linkedin-state')

    def test_state_is_not_silently_reset_when_read_fails(self):
        state = drafts.GitHubState('rsoldatellirosa/rsoldatellirosa.github.io', 'token-ficticio')
        with patch.object(drafts, 'request_json', side_effect=[{}, HTTPError('https://api.github.com', 403, '', {}, None)]) as api:
            with self.assertRaises(HTTPError):
                state.save({'new-case': {}}, 'a' * 40)
            self.assertEqual(api.call_count, 2)


class DiagnosticTests(unittest.TestCase):
    def test_only_status_and_allowlisted_api_code_are_exposed(self):
        body = io.BytesIO(json.dumps({'error': {'code': 'insufficient_quota',
                          'message': 'SENSITIVE_RESPONSE_MUST_NOT_APPEAR'}}).encode())
        error = HTTPError('https://api.openai.com', 429, '', {}, body)
        self.assertEqual(drafts.safe_error_reason(error), 'HTTP 429 / insufficient_quota')

    def test_arbitrary_exception_text_is_not_exposed(self):
        self.assertEqual(drafts.safe_error_reason(ValueError('SENSITIVE_RESPONSE_MUST_NOT_APPEAR')), 'ValueError')

    def test_unknown_api_code_is_not_exposed(self):
        error = HTTPError('https://api.openai.com', 400, '', {},
                          io.BytesIO(b'{"error":{"code":"SENSITIVE_RESPONSE_MUST_NOT_APPEAR"}}'))
        self.assertEqual(drafts.safe_error_reason(error), 'HTTP 400')


if __name__ == '__main__':
    unittest.main()
