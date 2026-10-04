"""Your first Python exercise: check one HTTP endpoint with no dependencies."""
import argparse
import time
import urllib.error
import urllib.request


def check_url(url, timeout=3):
    """Return status, health, latency and a short explanation."""
    started = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status = response.status
        detail = f'HTTP {status}'
    except urllib.error.HTTPError as error:
        status = error.code
        detail = f'HTTP {status}'
    except (urllib.error.URLError, OSError, TimeoutError) as error:
        status = None
        detail = str(error)
    elapsed_ms = (time.monotonic() - started) * 1000
    return {'status': status, 'healthy': status == 200,
            'latency_ms': round(elapsed_ms, 1), 'detail': detail}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', nargs='?', default='http://127.0.0.1:8080/healthz')
    args = parser.parse_args()

    if not args.url.startswith(('http://', 'https://')):
        parser.error('Use an HTTP or HTTPS endpoint you own or may check.')

    result = check_url(args.url)

    if result['healthy']:
        print('The service is ready.')
    else:
        print('Investigate this service.')

    print(f'Healthy: {result["healthy"]}')
    print(f'Response time: {result["latency_ms"]} ms')
    print(f'Result: {result["detail"]}')