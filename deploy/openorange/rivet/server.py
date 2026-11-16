import hmac
import json
import os
import re
import sys
import socket
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIMIT = 1024 * 1024
TIMEOUT = 4
FIELDS = {
    'health': ('status', 'version', 'architecture', 'runtime'),
    'namespaces': ('name', 'status', 'create_ts', 'archived_ts'),
    'pools': ('name',),
    'nodes': ('key', 'namespace', 'pool', 'connected', 'stopping', 'create_ts', 'last_ping_ts', 'datacenter', 'version'),
    'actors': ('actor_id', 'name', 'namespace', 'pool', 'key', 'create_ts', 'connectable_ts', 'destroy_ts', 'pending_allocation_ts', 'reschedule_ts', 'sleep_ts', 'start_ts', 'lifecycle_phase', 'lifecycle_epoch'),
}
VALUE = re.compile(r'^[A-Za-z0-9_.:@-]{1,200}$')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

OPENER = urllib.request.build_opener(NoRedirect())

REQUIRED = {'health': ('status', 'version'), 'namespaces': ('name',), 'pools': ('name',), 'nodes': ('key', 'connected'), 'actors': ('actor_id', 'name')}
BOOLEAN = {'connected', 'stopping'}
INTEGER = {'create_ts', 'archived_ts', 'last_ping_ts', 'version', 'connectable_ts', 'destroy_ts', 'pending_allocation_ts', 'reschedule_ts', 'sleep_ts', 'start_ts', 'lifecycle_epoch'}
MAX_SAFE = 9007199254740991

def safe_string(value, secrets):
    if not isinstance(value, str) or len(value) > 2048 or any(secret in value for secret in secrets):
        raise ValueError('invalid string')
    return value

def project(row, kind, secrets):
    if not isinstance(row, dict) or any(k not in row or row[k] is None for k in REQUIRED[kind]):
        raise ValueError('invalid row')
    result = {}
    for key in FIELDS[kind]:
        if key not in row: continue
        value = row[key]
        if value is None:
            result[key] = None
        elif key in BOOLEAN:
            if type(value) is not bool: raise ValueError('invalid boolean')
            result[key] = value
        elif key in INTEGER and not (kind == 'health' and key == 'version'):
            if type(value) is not int: raise ValueError('invalid integer')
            if key == 'lifecycle_epoch' and not 0 <= value <= 4294967295: raise ValueError('invalid actor epoch')
            result[key] = value if abs(value) <= MAX_SAFE else safe_string(str(value), secrets)
        else:
            result[key] = safe_string(value, secrets)
            if key in REQUIRED[kind] and not value: raise ValueError('empty required field')
    return result

def config(path):
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict) or set(data) != {'engine_origin', 'engine_token', 'gateway_secret', 'operators'}:
        raise ValueError('invalid config')
    if not isinstance(data['engine_origin'], str) or len(data['engine_origin']) > 2048:
        raise ValueError('invalid origin')
    origin = urllib.parse.urlsplit(data['engine_origin'])
    if origin.scheme not in ('http', 'https') or not origin.hostname or origin.username or origin.password or origin.path not in ('', '/') or origin.query or origin.fragment or origin.port is None:
        raise ValueError('invalid origin')
    for key in ('engine_token', 'gateway_secret'):
        if not isinstance(data[key], str) or not 1 <= len(data[key]) <= 1024 or any(ord(c) < 33 or ord(c) > 126 for c in data[key]):
            raise ValueError('invalid secret')
    if not isinstance(data['operators'], list) or not data['operators'] or len(data['operators']) > 100 or any(not isinstance(x, str) or not 1 <= len(x) <= 256 or any(ord(c) < 32 or ord(c) > 126 for c in x) for x in data['operators']):
        raise ValueError('invalid operators')
    return data

class Handler(BaseHTTPRequestHandler):
    server_version = 'RivetExplorer'
    sys_version = ''
    def log_message(self, *args):
        pass

    def send(self, status, body, content_type='application/json; charset=utf-8'):
        self.send_response(status)
        for key, value in {'Content-Type': content_type, 'Content-Length': str(len(body)), 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY', 'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"}.items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def error(self, status, message):
        self.send(status, json.dumps({'error': message}).encode())

    def do_POST(self): self.error(405, 'Method not allowed')
    do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_HEAD = do_POST

    def do_GET(self):
        cfg = self.server.config
        secrets = self.headers.get_all('Rivet-Gateway-Secret', [])
        identities = self.headers.get_all('Stats-Tailnet-Identity', [])
        if len(secrets) != 1 or len(identities) != 1 or not hmac.compare_digest(secrets[0].encode(), cfg['gateway_secret'].encode()) or identities[0] not in cfg['operators']:
            self.error(403, 'Forbidden'); return
        url = urllib.parse.urlsplit(self.path)
        if url.path in ('/rivet', '/rivet/', '/rivet/index.html', '/rivet/app.js', '/rivet/style.css'):
            if url.query:
                self.error(400, 'Invalid query'); return
            name = {'/rivet': 'index.html', '/rivet/': 'index.html'}.get(url.path, url.path.rsplit('/', 1)[-1])
            typ = {'index.html': 'text/html; charset=utf-8', 'app.js': 'text/javascript; charset=utf-8', 'style.css': 'text/css; charset=utf-8'}[name]
            self.send(200, (ROOT / name).read_bytes(), typ); return
        routes = {'/rivet/api/health': ('health', ()), '/rivet/api/namespaces': ('namespaces', ()), '/rivet/api/pools': ('pools', ('namespace',)), '/rivet/api/nodes': ('nodes', ('namespace', 'pool')), '/rivet/api/names': ('names', ('namespace',)), '/rivet/api/actors': ('actors', ('namespace', 'name'))}
        if url.path not in routes:
            self.error(404, 'Not found'); return
        kind, required = routes[url.path]
        try:
            query = urllib.parse.parse_qs(url.query, keep_blank_values=True, strict_parsing=True, max_num_fields=3)
            if set(query) != set(required) or any(len(v) != 1 or not VALUE.fullmatch(v[0]) for v in query.values()): raise ValueError()
            params = {k: v[0] for k, v in query.items()}
        except ValueError:
            self.error(400, 'Invalid query'); return
        try:
            path = {'health': '/health', 'namespaces': '/namespaces', 'pools': '/pools', 'nodes': '/pools/' + urllib.parse.quote(params.get('pool', ''), safe='') + '/nodes', 'names': '/actors/names', 'actors': '/actors'}[kind]
            upstream_params = {k: v for k, v in params.items() if k != 'pool'}
            target = cfg['engine_origin'].rstrip('/') + path + ('?' + urllib.parse.urlencode(upstream_params) if upstream_params else '')
            req = urllib.request.Request(target, headers={'Authorization': 'Bearer ' + cfg['engine_token'], 'Accept': 'application/json'})
            with OPENER.open(req, timeout=TIMEOUT) as response:
                raw = response.read(LIMIT + 1)
                if len(raw) > LIMIT: raise ValueError()
                data = json.loads(raw)
            if not isinstance(data, dict): raise ValueError()
            secrets = (cfg['engine_token'], cfg['gateway_secret'])
            if kind == 'health':
                result = project(data, kind, secrets)
                configured_tag = os.environ.get('RIVET_CONFIGURED_IMAGE_TAG')
                if configured_tag:
                    result['configuredImageTag'] = safe_string(configured_tag, secrets)
            elif kind == 'names':
                names = data['names']
                if not isinstance(names, dict): raise ValueError()
                for name in names: safe_string(name, secrets)
                result = {'names': [x for x in names if VALUE.fullmatch(x)]}
            else:
                rows = data[kind]
                if not isinstance(rows, list): raise ValueError()
                pagination = data.get('pagination')
                if not isinstance(pagination, dict) or 'cursor' not in pagination: raise ValueError('invalid pagination')
                cursor = pagination['cursor']
                if cursor is not None: safe_string(cursor, secrets)
                result = {kind: [project(row, kind, secrets) for row in rows], 'truncated': bool(cursor)}
            encoded = json.dumps(result, allow_nan=False).encode()
            if any(secret.encode() in encoded or json.dumps(secret, ensure_ascii=True)[1:-1].encode() in encoded for secret in secrets): raise ValueError('secret in response')
            self.send(200, encoded)
        except urllib.error.HTTPError as exc:
            status = 404 if exc.code == 404 else 502
            exc.close()
            self.error(status, 'Engine resource unavailable')
        except (ValueError, KeyError, TypeError, OSError, urllib.error.URLError, RecursionError):
            self.error(502, 'Engine response unavailable')

class Server(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, settings):
        self.config = settings
        self.slots = threading.BoundedSemaphore(16)
        super().__init__(address, Handler)

    def handle_error(self, request, address):
        pass

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        def expire():
            try: request.shutdown(socket.SHUT_RDWR)
            except OSError: pass
        request.settimeout(5)
        deadline = threading.Timer(10, expire)
        deadline.daemon = True
        deadline.start()
        try:
            super().process_request_thread(request, address)
        finally:
            deadline.cancel()
            self.slots.release()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8080'))
    if not 1024 <= port <= 65535:
        raise ValueError('invalid port')
    Server(('0.0.0.0', port), config(sys.argv[1])).serve_forever()
