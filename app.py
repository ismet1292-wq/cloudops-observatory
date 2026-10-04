"""CloudOps Observatory: local-first service monitoring portfolio project."""
import argparse
import json
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent


class DemoScenario:
    """A repeatable, local-only outage followed by automatic recovery."""
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.started = clock()

    def snapshot(self):
        elapsed = max(0, self.clock() - self.started)
        phase = 'healthy' if elapsed < 10 else 'outage' if elapsed < 22 else 'recovered'
        return {'phase': phase, 'elapsed_seconds': round(elapsed, 1),
                'outage_starts_at_seconds': 10, 'recovery_starts_at_seconds': 22}


class Store:
    def __init__(self, path):
        self.path = path
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS checks (
                    id INTEGER PRIMARY KEY, service TEXT, timestamp REAL,
                    healthy INTEGER, latency_ms REAL, detail TEXT);
                CREATE INDEX IF NOT EXISTS checks_service ON checks(service, id);
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY, service TEXT, opened REAL,
                    resolved REAL, detail TEXT);
                CREATE UNIQUE INDEX IF NOT EXISTS one_open_incident
                    ON incidents(service) WHERE resolved IS NULL;
                CREATE TABLE IF NOT EXISTS health_state (
                    service TEXT PRIMARY KEY, failures INTEGER NOT NULL,
                    successes INTEGER NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def record(self, service, healthy, latency_ms, detail, timestamp=None,
               failure_threshold=1, recovery_threshold=1):
        timestamp = time.time() if timestamp is None else timestamp
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            state = db.execute('SELECT failures,successes FROM health_state WHERE service=?',
                               (service,)).fetchone() or (0, 0)
            failures = 0 if healthy else state[0] + 1
            successes = state[1] + 1 if healthy else 0
            db.execute('INSERT INTO health_state VALUES(?,?,?) ON CONFLICT(service) DO UPDATE '
                       'SET failures=excluded.failures,successes=excluded.successes',
                       (service, failures, successes))
            db.execute('INSERT INTO checks(service,timestamp,healthy,latency_ms,detail) VALUES(?,?,?,?,?)',
                       (service, timestamp, int(healthy), latency_ms, detail))
            if healthy and successes >= recovery_threshold:
                db.execute('UPDATE incidents SET resolved=? WHERE service=? AND resolved IS NULL',
                           (timestamp, service))
            elif not healthy and failures >= failure_threshold:
                db.execute('INSERT OR IGNORE INTO incidents(service,opened,detail) VALUES(?,?,?)',
                           (service, timestamp, detail))

    def snapshot(self, services):
        result = []
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            for service in services:
                rows = db.execute('SELECT * FROM checks WHERE service=? ORDER BY id DESC LIMIT 120',
                                  (service['name'],)).fetchall()
                result.append({
                    'name': service['name'], 'url': service['url'],
                    'latest': dict(rows[0]) if rows else None,
                    'availability': round(sum(r['healthy'] for r in rows) / len(rows) * 100, 2) if rows else None,
                    'samples': len(rows),
                    'latency_p95_ms': sorted(r['latency_ms'] for r in rows)[max(0, int(len(rows) * .95 + .9999) - 1)] if rows else None,
                    'history': [dict(r) for r in reversed(rows)],
                })
            incidents = [dict(r) for r in db.execute('SELECT * FROM incidents ORDER BY id DESC LIMIT 50')]
        return {'services': result, 'incidents': incidents, 'generated_at': time.time()}


def probe(service):
    start = time.monotonic()
    expected = service.get('expected_status', 200)
    try:
        request = urllib.request.Request(service['url'], headers={'User-Agent': 'CloudOps-Observatory/1.0'})
        with urllib.request.urlopen(request, timeout=service.get('timeout_seconds', 5)) as response:
            status = response.status
        return status == expected, (time.monotonic() - start) * 1000, f'HTTP {status}'
    except urllib.error.HTTPError as error:
        return error.code == expected, (time.monotonic() - start) * 1000, f'HTTP {error.code}'
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return False, (time.monotonic() - start) * 1000, str(error)[:250]


def check_cycle(store, services, stop, max_workers=8):
    """Probe concurrently; serialize database writes in completion order."""
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        pending = {pool.submit(probe, service): service for service in services
                   if not stop.is_set()}
        for future in as_completed(pending):
            if stop.is_set():
                break
            service = pending[future]
            store.record(service['name'], *future.result(),
                         failure_threshold=service.get('failure_threshold', 1),
                         recovery_threshold=service.get('recovery_threshold', 1))


def monitor(store, services, interval, stop):
    while not stop.is_set():
        check_cycle(store, services, stop)
        stop.wait(interval)


def handler_for(store, services, demo=None):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = self.path.split('?')[0]
            if route == '/':
                body = (ROOT / 'dashboard.html').read_bytes()
                content_type = 'text/html; charset=utf-8'
            elif route == '/api/status':
                snapshot = store.snapshot(services)
                snapshot['demo'] = demo.snapshot() if demo else None
                body = json.dumps(snapshot).encode()
                content_type = 'application/json'
            elif route == '/demo/scenario' and demo is not None:
                phase = demo.snapshot()['phase']
                body = json.dumps({'phase': phase}).encode()
                self.send_response(503 if phase == 'outage' else 200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(body)
                return
            elif route == '/healthz':
                body, content_type = b'{"status":"ok"}', 'application/json'
            elif route == '/metrics':
                lines = ['# TYPE observatory_service_healthy gauge',
                         '# TYPE observatory_latency_ms gauge',
                         '# TYPE observatory_availability_percent gauge']
                for service in store.snapshot(services)['services']:
                    if service['latest'] is None:
                        continue
                    label = json.dumps(service['name'], ensure_ascii=True)
                    lines.extend([
                        f'observatory_service_healthy{{service={label}}} {service["latest"]["healthy"]}',
                        f'observatory_latency_ms{{service={label}}} {service["latest"]["latency_ms"]:.3f}',
                        f'observatory_availability_percent{{service={label}}} {service["availability"]}',
                    ])
                body = ('\n'.join(lines) + '\n').encode()
                content_type = 'text/plain; version=0.0.4; charset=utf-8'
            elif route == '/demo/fail':
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'Simulated service outage')
                return
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

    return Handler


def load_config(path):
    config = json.loads(Path(path).read_text())
    names = set()
    for service in config['services']:
        if service['name'] in names:
            raise ValueError('Service names must be unique')
        names.add(service['name'])
        if not service['url'].startswith(('http://', 'https://')):
            raise ValueError('Only HTTP/HTTPS endpoints are supported')
        if not 0 < service.get('timeout_seconds', 5) <= 30:
            raise ValueError('Timeout must be between 0 and 30 seconds')
        for key in ('failure_threshold', 'recovery_threshold'):
            value = service.get(key, 1)
            if type(value) is not int or not 1 <= value <= 20:
                raise ValueError(f'{key} must be an integer between 1 and 20')
    if config.get('interval_seconds', 15) < 1:
        raise ValueError('Interval must be at least one second')
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default=str(ROOT / 'services.json'))
    parser.add_argument('--db', help='SQLite file (demo uses demo.db by default)')
    parser.add_argument('--demo', action='store_true',
                        help='Local 30-second healthy/outage/recovery walkthrough')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    if args.demo and args.host != '127.0.0.1':
        parser.error('--demo must use the default loopback host 127.0.0.1')
    config = {'interval_seconds': 2, 'services': []} if args.demo else load_config(args.config)
    demo = DemoScenario() if args.demo else None
    store = Store(args.db or str(ROOT / ('demo.db' if args.demo else 'observatory.db')))
    stop = threading.Event()
    server = ThreadingHTTPServer((args.host, args.port), handler_for(store, config['services'], demo))
    if args.demo:
        base = f'http://127.0.0.1:{server.server_port}'
        config['services'].extend([
            {'name': 'Observatory API', 'url': base + '/healthz', 'timeout_seconds': 1},
            {'name': 'Demo application', 'url': base + '/demo/scenario',
             'timeout_seconds': 1, 'failure_threshold': 2, 'recovery_threshold': 2},
        ])
    worker = threading.Thread(target=monitor, args=(store, config['services'], config.get('interval_seconds', 15), stop), daemon=True)
    worker.start()
    print(f'CloudOps Observatory: http://{args.host}:{server.server_port}', flush=True)
    if args.demo:
        print('Demo: healthy for 10s, outage until 22s, then recovery. Watch for 30s.\n'
              'History persists in demo.db; Ctrl+C stops the application.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        worker.join(timeout=35)


if __name__ == '__main__':
    main()
