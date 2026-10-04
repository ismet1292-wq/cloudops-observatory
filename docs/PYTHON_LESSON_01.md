# Lesson 1: understand one check before the whole platform

Goal: run a Python script, explain its result, and make your own small change.
The application was built with AI assistance. Your own evidence starts with
running, modifying, testing and explaining it.

## Run the demonstration

Open PowerShell in the extracted project folder:

```powershell
py -3 --version
py -3 -m unittest -v
py -3 app.py --demo
```

Open http://127.0.0.1:8080. Keep that PowerShell window running.
The demonstration starts healthy, returns HTTP 503 from second 10 to second 22,
then recovers. Two consecutive failures open an incident; two consecutive
successes resolve it. The dashboard refreshes every five seconds; wait about
30 seconds to see the complete transition. Leave it running to inspect the history.

## Run your first short script

Open a SECOND PowerShell window in the same folder:

```powershell
py -3 lesson_01.py
py -3 lesson_01.py http://127.0.0.1:8080/demo/fail
```

The first command checks the working API. The second checks a permanently
failing local endpoint. Expect `Healthy: True` and `Healthy: False` respectively.
If the application is stopped, you should get a connection error printed as
an unhealthy result. Response times vary; low latency does not prove health.

## Read lesson_01.py

1. `import` loads standard-library tools. Nothing extra needs installing.
2. `def check_url(...)` defines a reusable function with an input URL and timeout.
3. `time.monotonic()` measures elapsed time without depending on clock adjustments.
4. `with ... urlopen(...)` opens the HTTP response and closes it afterwards.
5. `try/except` handles an HTTP failure or unreachable server without crashing.
6. The returned dictionary names the values: status, health, latency, detail.
7. `argparse` reads the URL supplied in PowerShell.
8. The main guard runs the command-line code only when the file is run directly.

## Your first change

Below `result = check_url(args.url)`, add:

```python
if result['healthy']:
    print('The service is ready.')
else:
    print('Investigate this service.')
```

Python uses indentation to group instructions. Keep four spaces inside each branch.
Run both commands again and explain why they print different messages.

Next exercise: change the function to accept an `expected_status` argument, so
a deliberately expected HTTP 503 can count as success. Compare your solution
with `probe()` in app.py. Do not just change every failure to healthy.

## Explain it in your own words

- What does HTTP 503 tell you?
- What happens when the server never answers?
- Why does a monitoring check need a timeout?
- Why can a fast response still be unhealthy?
- What does this script add compared with manually refreshing a browser?

## What we do next

After you can run and explain this lesson, add a test for your change, run the
Docker container, and publish the repository with passing CI. Cloud deployment
comes after local verification. The supplied Docker/CI/Kubernetes files are
configuration, not proof those environments have been run.
