# Your first session: run, break, recover, explain

This is CloudOps Observatory v0.4, an AI-assisted local portfolio prototype. Start with the automatic demo and your first Python exercise in docs/PYTHON_LESSON_01.md. Your task is to run it, change it, and understand its behavior.

For the quickest start, open PowerShell in the extracted folder, run
`py -3 app.py --demo`, and open http://127.0.0.1:8080. Watch for 30 seconds.
The demo first becomes healthy, then fails, then recovers automatically.
Its history is saved separately in demo.db. The manual configuration walkthrough
below still works with `py -3 app.py`.

## 1. Extract on Windows

Download the ZIP, right-click it, choose Extract All, and put the cloudops-portfolio folder inside C:\Projects. Open PowerShell and run:

```powershell
cd C:\Projects\cloudops-portfolio
py -3 --version
py -3 -m unittest -v
py -3 app.py
```

Python 3.12 or newer is recommended. If the py launcher is unavailable but Python is installed, use python instead. This version has no third-party Python dependencies.

## 2. See the dashboard

Open http://127.0.0.1:8080 in your browser. Leave PowerShell running. Wait about 30 seconds. You should see one healthy service, one failing simulation, and one open incident. Open http://127.0.0.1:8080/api/status to see the JSON response.

## 3. Recover the failed service

Press Ctrl+C in PowerShell. Open services.json in an editor. For Outage simulation, change only the URL from http://127.0.0.1:8080/demo/fail to http://127.0.0.1:8080/healthz. Keep its name unchanged. Run py -3 app.py again. After two successful monitoring cycles, the original incident should show Resolved. History remains in observatory.db.

## 4. Make your own first change

Change the interval_seconds setting from 15 to 5, restart, and observe the shorter time to detect a new simulated outage. Explain the tradeoff: quicker detection creates more requests and more stored check records. Then change failure_threshold from 2 to 3 and observe how an incident opens later while failed samples appear immediately.

## 5. Explain these ideas before your interview

- What is the difference between a failed check and an open incident?
- Why wait for consecutive failures before declaring an incident?
- Why does SQLite preserve history after a restart?
- Why run HTTP probes concurrently?
- Why is sample availability different from time-based uptime?

See docs/INTERVIEW_GUIDE.md for implementation explanations. Describe AI assistance and your own changes accurately.

## Next milestones

After you run and explain this version: build/run Docker, publish a GitHub repository and verify CI, demonstrate Minikube deployment, then design a cost-controlled cloud deployment. The Docker image, non-root container, health endpoint, and persistent volume were validated locally on Windows 11, and GitHub Actions tests passed. Kubernetes has not yet been executed. No paid cloud services have been created.
