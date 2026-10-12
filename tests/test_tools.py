import csv
import importlib.util
import json
import tempfile
import threading
import unittest
from argparse import Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/listmonk-mail/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contacts = load('prepare_contacts')
api = load('listmonk_api')


class ContactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'source.csv'
        self.destination = Path(self.temp.name) / 'result.csv'

    def write(self, text):
        self.source.write_text(text, encoding='utf-8-sig')

    def test_chinese_headers_dedup_and_unicode_roundtrip(self):
        self.write('邮箱,姓名\n person@example.com ,张三\nPERSON@example.com,重复\nother@example.com,李四\n')
        result = contacts.prepare(self.source, self.destination)
        self.assertEqual((result['contacts'], result['duplicates_removed']), (2, 1))
        with self.destination.open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]['name'], '张三')
        self.assertEqual(json.loads(rows[0]['attributes']), {})

    def test_invalid_row_does_not_leave_partial_output(self):
        self.write('email,name\na@example.com,A\ninvalid,B\n')
        with self.assertRaisesRegex(ValueError, 'Line 3'):
            contacts.prepare(self.source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_unknown_columns_are_not_silently_lost(self):
        self.write('email,company\na@example.com,Example\n')
        with self.assertRaises(ValueError):
            contacts.prepare(self.source, self.destination)

    def test_existing_output_is_preserved(self):
        self.write('email\na@example.com\n')
        self.destination.write_text('keep', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            contacts.prepare(self.source, self.destination)
        self.assertEqual(self.destination.read_text(), 'keep')

    def test_attributes_require_object(self):
        self.write('email,attributes\na@example.com,[]\n')
        with self.assertRaises(ValueError):
            contacts.prepare(self.source, self.destination)


class APIHandler(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *args):
        pass

    def respond(self, payload):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        self.requests.append(('GET', self.path, self.headers.get('Authorization')))
        if self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/credential-leak')
            self.end_headers()
        else:
            self.respond({'data': {'results': [], 'total': 0}})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.requests.append(('POST', self.path, body))
        self.respond({'data': {'id': 123, 'status': 'draft', **body}})


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), APIHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        APIHandler.requests.clear()
        self.client = api.Client(self.url, 'synthetic-user', 'synthetic-token')

    def test_health_does_not_send_authentication(self):
        result = api.execute(self.client, Namespace(command='health'))
        self.assertFalse(result['api_authenticated'])
        self.assertIsNone(APIHandler.requests[-1][2])

    def test_lists_uses_authenticated_api_and_page(self):
        api.execute(self.client, Namespace(command='lists', page=2))
        self.assertEqual(APIHandler.requests[-1][1], '/api/lists?page=2&per_page=100')
        self.assertTrue(APIHandler.requests[-1][2].startswith('Basic '))

    def test_redirect_does_not_forward_credentials(self):
        with self.assertRaisesRegex(ValueError, 'HTTP 302'):
            self.client.request('GET', '/redirect')
        self.assertEqual(len(APIHandler.requests), 1)

    def test_remote_http_and_embedded_credentials_rejected(self):
        for url in ('http://example.com', 'https://user:secret@example.com', 'file:///tmp/a'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                api.validate_url(url)

    def test_draft_creation_keeps_draft_and_unicode(self):
        payload = {'name': '测试', 'subject': '通知', 'from_email': 'a@example.com',
                   'lists': [1], 'template_id': 1, 'body': '<p>您好</p>'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'draft.json'
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            result = api.execute(self.client, Namespace(command='create-draft', file=str(path)))
        method, endpoint, sent = APIHandler.requests[-1]
        self.assertEqual((method, endpoint), ('POST', '/api/campaigns'))
        self.assertEqual(result['data']['status'], 'draft')
        self.assertEqual(sent['body'], payload['body'])
        self.assertNotIn('send_at', sent)
        self.assertNotIn('status', sent)

    def test_scheduling_and_send_fields_rejected_before_network(self):
        for key in ('send_at', 'status', 'subscribers'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                api.draft_payload({key: 'running'})
        self.assertEqual(APIHandler.requests, [])


if __name__ == '__main__':
    unittest.main()
