import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from app import Store, handler_for, probe, load_config, check_cycle, DemoScenario
from lesson_01 import check_url


class ObservatoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(str(Path(self.temp.name) / 'test.db'))

    def tearDown(self):
        self.temp.cleanup()

    def test_incident_opens_once_and_resolves(self):
        self.store.record('api', False, 10, 'HTTP 503', timestamp=1)
        self.store.record('api', False, 20, 'HTTP 503', timestamp=2)
        result = self.store.snapshot([{'name': 'api', 'url': 'http://localhost'}])
        self.assertEqual(len(result['incidents']), 1)
        self.assertIsNone(result['incidents'][0]['resolved'])
        self.store.record('api', True, 5, 'HTTP 200', timestamp=3)
        result = self.store.snapshot([{'name': 'api', 'url': 'http://localhost'}])
        self.assertEqual(result['incidents'][0]['resolved'], 3)
        self.assertEqual(result['services'][0]['availability'], 33.33)
        self.store.record('api', False, 10, 'HTTP 503', timestamp=4)
        self.assertEqual(len(self.store.snapshot([])['incidents']), 2)

    def test_sample_window(self):
        for i in range(125):
            self.store.record('api', i >= 5, 2, 'test')
        service = self.store.snapshot([{'name': 'api', 'url': 'http://localhost'}])['services'][0]
        self.assertEqual(service['samples'], 120)
        self.assertEqual(service['availability'], 100)
        self.assertEqual(service['latency_p95_ms'], 2)

    def test_percentile_uses_nearest_rank(self):
        for latency in range(1, 21):
            self.store.record('api', True, latency, 'HTTP 200')
        self.assertEqual(self.store.snapshot([{'name': 'api', 'url': 'http://localhost'}])['services'][0]['latency_p95_ms'], 19)

    def test_metrics(self):
        self.store.record('api', True, 12, 'HTTP 200')
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(self.store, [{'name': 'api', 'url': 'http://localhost'}]))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/metrics') as response:
                metrics = response.read().decode()
            self.assertIn('observatory_service_healthy{service="api"} 1', metrics)
            self.assertIn('observatory_availability_percent{service="api"} 100.0', metrics)
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_http_probe_and_api(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(self.store, []))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            self.assertTrue(probe({'url': base + '/healthz'})[0])
            self.assertFalse(probe({'url': base + '/demo/fail'})[0])
            self.assertTrue(probe({'url': base + '/demo/fail', 'expected_status': 503})[0])
            with urllib.request.urlopen(base + '/api/status') as response:
                self.assertEqual(json.load(response)['services'], [])
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_invalid_config_rejected(self):
        path = Path(self.temp.name) / 'config.json'
        path.write_text(json.dumps({'services': [{'name': 'x', 'url': 'file:///etc/passwd'}]}))
        with self.assertRaises(ValueError):
            load_config(path)

    def test_thresholds_survive_restart_and_reset_on_opposite_result(self):
        def record(healthy):
            self.store.record('api', healthy, 10, 'probe',
                              failure_threshold=2, recovery_threshold=2)
        record(False)
        self.assertEqual(self.store.snapshot([])['incidents'], [])
        record(True)
        record(False)
        self.assertEqual(self.store.snapshot([])['incidents'], [])
        self.store = Store(self.store.path)
        record(False)
        self.assertEqual(len(self.store.snapshot([])['incidents']), 1)
        record(True)
        self.assertIsNone(self.store.snapshot([])['incidents'][0]['resolved'])
        record(True)
        self.assertIsNotNone(self.store.snapshot([])['incidents'][0]['resolved'])

    def test_probes_run_concurrently_and_all_results_are_recorded(self):
        barrier = threading.Barrier(3)
        def fake_probe(service):
            barrier.wait(timeout=3)
            return True, 1, 'HTTP 200'
        services = [{'name': str(i), 'url': 'http://localhost'} for i in range(3)]
        with patch('app.probe', side_effect=fake_probe):
            check_cycle(self.store, services, threading.Event(), max_workers=3)
        snapshot = self.store.snapshot(services)
        self.assertEqual([s['samples'] for s in snapshot['services']], [1, 1, 1])

    def test_invalid_threshold_rejected(self):
        path = Path(self.temp.name) / 'config.json'
        for value in (0, -1, 1.5, True, 21):
            path.write_text(json.dumps({'services': [
                {'name': 'x', 'url': 'http://localhost', 'failure_threshold': value}]}))
            with self.assertRaises(ValueError):
                load_config(path)

    def test_demo_boundary_times(self):
        clock = [100]
        demo = DemoScenario(clock=lambda: clock[0])
        for elapsed, phase in [(0, 'healthy'), (9.9, 'healthy'),
                               (10, 'outage'), (21.9, 'outage'), (22, 'recovered')]:
            clock[0] = 100 + elapsed
            self.assertEqual(demo.snapshot()['phase'], phase)

    def test_demo_http_failure_and_recovery_resolve_original_incident(self):
        clock = [0]
        demo = DemoScenario(clock=lambda: clock[0])
        services = []
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(self.store, services, demo))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        url = f'http://127.0.0.1:{server.server_port}/demo/scenario'
        services.append({'name': 'demo', 'url': url,
                         'failure_threshold': 2, 'recovery_threshold': 2})
        try:
            self.assertTrue(check_url(url)['healthy'])
            for elapsed in [0, 10, 12]:
                clock[0] = elapsed
                check_cycle(self.store, services, threading.Event())
            opened = self.store.snapshot(services)['incidents']
            self.assertEqual(len(opened), 1)
            self.assertIsNone(opened[0]['resolved'])
            self.assertEqual(check_url(url)['status'], 503)
            for elapsed in [22, 24]:
                clock[0] = elapsed
                check_cycle(self.store, services, threading.Event())
            snapshot = self.store.snapshot(services)
            self.assertEqual(snapshot['incidents'][0]['id'], opened[0]['id'])
            self.assertIsNotNone(snapshot['incidents'][0]['resolved'])
            self.assertEqual(snapshot['services'][0]['samples'], 5)
            with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/api/status') as response:
                self.assertEqual(json.load(response)['demo']['phase'], 'recovered')
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_lesson_handles_connection_failure(self):
        with patch('lesson_01.urllib.request.urlopen', side_effect=urllib.error.URLError('offline')):
            result = check_url('http://localhost')
        self.assertFalse(result['healthy'])
        self.assertIsNone(result['status'])
        self.assertIn('offline', result['detail'])


if __name__ == '__main__':
    unittest.main()
