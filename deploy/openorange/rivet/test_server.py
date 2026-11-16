import http.client
import importlib.util
import json
import socket
import threading
import tempfile
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

spec = importlib.util.spec_from_file_location('explorer', Path(__file__).with_name('server.py'))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class Engine(BaseHTTPRequestHandler):
    mode = 'normal'
    paths = []
    def log_message(self, *args): pass
    def do_GET(self):
        self.paths.append(self.path)
        if self.mode == 'timeout': time.sleep(.2)
        if self.mode == '404': self.send_response(404); self.end_headers(); self.wfile.write(b'secret upstream'); return
        if self.mode == 'redirect': self.send_response(302); self.send_header('Location', '/evil'); self.end_headers(); return
        body = {'/health': {'status': 'ok', 'version': '3.1.1', 'secret': 'engine-secret'}, '/namespaces': {'namespaces': [{'name': '<script>alert(1)</script>', 'status': 'active', 'secret': 'engine-secret'}], 'pagination': {'cursor': None}}, '/pools?namespace=stats-prod': {'pools': [{'name': 'default', 'metadata': {'token': 'engine-secret'}}], 'pagination': {'cursor': None}}, '/pools/default/nodes?namespace=stats-prod': {'nodes': [{'key': 'node', 'connected': True, 'secret': 'engine-secret'}], 'pagination': {'cursor': None}}, '/actors/names?namespace=stats-prod': {'names': {'actor': {'metadata': {'token': 'engine-secret'}}}}, '/actors?namespace=stats-prod&name=actor': {'actors': [{'actor_id': 'id', 'name': 'actor', 'secret': 'engine-secret'}], 'pagination': {'cursor': 'more'}}}.get(self.path, {})
        if self.mode == 'empty': body = {}
        if self.mode == 'pagination-null': body['pagination'] = None
        if self.mode == 'pagination-list': body['pagination'] = []
        if self.mode == 'secret-engine': body['version'] = 'prefix engine-secret suffix'
        if self.mode == 'secret-gateway': body['version'] = 'gateway-secret'
        if self.mode == 'nonfinite': body['version'] = float('nan')
        if self.mode == 'long': body['version'] = 'x' * 2049
        if self.mode == 'wide-int': body['namespaces'][0]['create_ts'] = 9007199254740992
        raw = b'bad json' if self.mode == 'bad' else b' ' * (app.LIMIT + 1) if self.mode == 'large' else json.dumps(body).encode()
        try:
            self.send_response(200); self.end_headers(); self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError): pass

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ThreadingHTTPServer(('127.0.0.1', 0), Engine)
        cls.server = app.Server(('127.0.0.1', 0), {'engine_origin': 'http://127.0.0.1:' + str(cls.engine.server_port), 'engine_token': 'engine-secret', 'gateway_secret': 'gateway-secret', 'operators': ['alice']})
        for server in (cls.engine, cls.server): threading.Thread(target=server.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        for server in (cls.engine, cls.server): server.shutdown(); server.server_close()
    def setUp(self): Engine.mode = 'normal'; Engine.paths.clear()
    def request(self, path, method='GET', headers=None):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        c.request(method, path, headers=headers if headers is not None else {'Rivet-Gateway-Secret': 'gateway-secret', 'Stats-Tailnet-Identity': 'alice'})
        r = c.getresponse(); data = r.read(); c.close(); return r.status, data
    def test_authorization(self):
        for headers in ({}, {'Rivet-Gateway-Secret':'wrong','Stats-Tailnet-Identity':'alice'}, {'Rivet-Gateway-Secret':'gateway-secret','Stats-Tailnet-Identity':'bob'}):
            self.assertEqual(self.request('/rivet/', headers=headers)[0], 403)
        self.assertEqual(Engine.paths, [])
    def test_duplicate_headers_and_static_auth(self):
        for path in ('/rivet', '/rivet/', '/rivet/index.html', '/rivet/app.js', '/rivet/style.css'):
            self.assertEqual(self.request(path, headers={})[0], 403)
            self.assertEqual(self.request(path)[0], 200)
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        c.putrequest('GET', '/rivet/')
        c.putheader('Rivet-Gateway-Secret', 'gateway-secret')
        c.putheader('Rivet-Gateway-Secret', 'gateway-secret')
        c.putheader('Stats-Tailnet-Identity', 'alice')
        c.endheaders(); self.assertEqual(c.getresponse().status, 403); c.close()
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        c.putrequest('GET', '/rivet/')
        c.putheader('Rivet-Gateway-Secret', 'gateway-secret')
        c.putheader('Stats-Tailnet-Identity', 'alice')
        c.putheader('Stats-Tailnet-Identity', 'alice')
        c.endheaders(); self.assertEqual(c.getresponse().status, 403); c.close()
        self.assertEqual(self.request('/rivetfoo')[0], 404)
    def test_config(self):
        good = {'engine_origin':'http://127.0.0.1:6420', 'engine_token':'token', 'gateway_secret':'secret', 'operators':['alice']}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            for value in ([], None, {}, dict(good, extra=True), dict(good, engine_origin='http://example.com/path'), dict(good, engine_token=''), dict(good, operators=[]), dict(good, operators='alice')):
                path.write_text(json.dumps(value))
                with self.assertRaises((ValueError, TypeError, KeyError)): app.config(path)
            path.write_text(json.dumps(good)); self.assertEqual(app.config(path), good)
    def test_invalid_responses(self):
        for mode in ('empty', 'secret-engine', 'secret-gateway', 'nonfinite', 'long'):
            Engine.mode = mode; status, body = self.request('/rivet/api/health')
            self.assertEqual(status, 502); self.assertNotIn(b'engine-secret', body); self.assertNotIn(b'gateway-secret', body)
        for mode in ('pagination-null', 'pagination-list'):
            Engine.mode = mode; self.assertEqual(self.request('/rivet/api/namespaces')[0], 502)
        Engine.mode = 'wide-int'; status, body = self.request('/rivet/api/namespaces')
        self.assertEqual(status, 200); self.assertEqual(json.loads(body)['namespaces'][0]['create_ts'], '9007199254740992')
    def test_connection_limit(self):
        sockets = []
        try:
            for _ in range(16):
                sock = socket.create_connection(('127.0.0.1', self.server.server_port), timeout=2)
                sock.sendall(b'GET /rivet/ HTTP/1.1\r\n')
                sockets.append(sock)
            deadline = time.monotonic() + 2
            while self.server.slots._value and time.monotonic() < deadline: time.sleep(.01)
            self.assertEqual(self.server.slots._value, 0)
            extra = socket.create_connection(('127.0.0.1', self.server.server_port), timeout=2)
            try:
                extra.sendall(b'GET /rivet/ HTTP/1.1\r\n')
                try: self.assertEqual(extra.recv(1), b'')
                except ConnectionResetError: pass
            finally: extra.close()
        finally:
            for sock in sockets: sock.close()
    def test_methods_and_routes(self):
        for method in ('POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'):
            self.assertEqual(self.request('/rivet/api/health', method)[0], 405)
        for path in ('/rivet/api/config', '/rivet/api/actors?namespace=stats-prod', '/rivet/api/nodes?namespace=stats-prod&pool=..%2Fhealth', '/rivet/api/pools?namespace=stats-prod&namespace=x', '/rivet/api/health?x=1'):
            self.assertIn(self.request(path)[0], (400, 404))
        self.assertEqual(Engine.paths, [])
    def test_projection_and_injection(self):
        for path in ('health', 'namespaces', 'pools?namespace=stats-prod', 'nodes?namespace=stats-prod&pool=default', 'names?namespace=stats-prod', 'actors?namespace=stats-prod&name=actor'):
            status, body = self.request('/rivet/api/' + path)
            self.assertEqual(status, 200); self.assertNotIn(b'engine-secret', body); self.assertNotIn(b'metadata', body)
        self.assertTrue(json.loads(body)['truncated'])
        status, html = self.request('/rivet/')
        self.assertEqual(status, 200); self.assertNotIn(b'<script>alert', html)
        self.assertIn(b'textContent', self.request('/rivet/app.js')[1])
    def test_lifecycle_projection_preserves_positive_and_unknown_values(self):
        base = {'actor_id': 'id', 'name': 'actor', 'sleep_ts': None, 'start_ts': None, 'connectable_ts': None}
        for phase, epoch in [('sleeping', 7), ('running', 7), ('migrating_from_v2', None), (None, None)]:
            row = dict(base, lifecycle_phase=phase, lifecycle_epoch=epoch)
            self.assertEqual(app.project(row, 'actors', ['engine-secret', 'gateway-secret']), row)
        self.assertEqual(app.project(base, 'actors', []), base)
        for epoch in (True, -1, 4294967296, '7'):
            with self.assertRaises(ValueError): app.project(dict(base, lifecycle_epoch=epoch), 'actors', [])
        with self.assertRaises(ValueError): app.project(dict(base, lifecycle_phase='engine-secret'), 'actors', ['engine-secret'])
    def test_upstream_failures(self):
        for mode, status in [('404', 404), ('bad', 502), ('large', 502), ('redirect', 502)]:
            Engine.mode = mode; code, body = self.request('/rivet/api/health'); self.assertEqual(code, status); self.assertNotIn(b'secret', body)
            if mode == 'redirect': self.assertNotIn('/evil', Engine.paths)
        Engine.mode = 'timeout'; old = app.TIMEOUT; app.TIMEOUT = .03
        try: self.assertEqual(self.request('/rivet/api/health')[0], 502)
        finally: app.TIMEOUT = old

if __name__ == '__main__': unittest.main()
