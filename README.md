# CloudOps Observatory

A cloud operations portfolio project: monitor HTTP services, inspect response latency, and follow persistent incident history from a dashboard.

**Built by Ismet Xani** — DevOps, Cloud & Infrastructure Engineering  
New York, NY | [LinkedIn](https://www.linkedin.com/in/ismet-xani-003201395) | [GitHub](https://github.com/ismet1292-wq)

Economic Engineering graduate and LSU DevOps Engineer Certificate holder building hands-on cloud operations, infrastructure automation, containerization, CI/CD, and observability projects.

![CloudOps Observatory dashboard](docs/dashboard.png)

## Implemented version 0.4

Start with `py -3 app.py --demo` and open http://127.0.0.1:8080.
The demonstration automatically runs healthy → outage → recovery in about
30 seconds. It uses a separate demo.db file and requires no external service.
See [your first Python lesson](docs/PYTHON_LESSON_01.md) and lesson_01.py.

- Configured HTTP/HTTPS endpoint checks with timeout and expected status.
- Bounded concurrent probes (up to eight workers) and configurable consecutive-failure/recovery thresholds, persisted across restarts.
- SQLite check history and deduplicated incidents, automatically resolved on recovery.
- Dashboard with per-service sample availability, latency, and history.
- JSON status API and a health endpoint.
- Prometheus-compatible metrics and a nearest-rank p95 latency value in the status API.
- An intentional HTTP 503 endpoint for demonstrating outages.
- A timed local demonstration with two-failure/two-success incident thresholds.
- A short standalone Python exercise for checking one HTTP endpoint.
- Integration and state-transition tests, Docker packaging, and a GitHub Actions test workflow.
- A validated local Minikube deployment and a GitHub Actions workflow that publishes public GHCR images with latest and immutable commit-SHA tags.

This is a working local prototype, not a production platform. The Docker image, public GHCR release, Minikube deployment, non-root execution, health probes, persistent storage, pod replacement, and GitHub Actions workflows were validated. A temporary Terraform-managed AWS demonstration was verified and cleaned up on October 19, 2026. Notifications, authentication, production infrastructure, load testing, and a production security audit remain unfinished. See docs/DEPLOYMENT_RUNBOOK.md and docs/INTERVIEW_GUIDE.md.

## Start on Windows (PowerShell)

Install Python 3.12 or later if needed. Extract the folder, open PowerShell in it, then:

```powershell
py -3 app.py
```

Open http://127.0.0.1:8080. The API service should become healthy and the outage simulation should show an open incident after two monitoring cycles (roughly 15–30 seconds). Stop with Ctrl+C. If `py` is unavailable, use `python app.py`.

To demonstrate recovery, change the outage simulation URL in `services.json` to `http://127.0.0.1:8080/healthz`, retaining its service name. Restart the app with the same database. Its incident resolves after two successful checks (roughly 15–30 seconds).

```powershell
py -3 -m unittest -v
```

## Docker

```powershell
docker build -t cloudops-observatory .
docker volume create observatory-data
docker run --rm -p 127.0.0.1:8080:8080 -v observatory-data:/data cloudops-observatory
```

### Public container image

The verified image is publicly available from GitHub Container Registry:

```powershell
docker pull ghcr.io/ismet1292-wq/cloudops-observatory:latest
docker run --rm -p 127.0.0.1:8080:8080 ghcr.io/ismet1292-wq/cloudops-observatory:latest
```

Each release also receives an immutable Git commit-SHA tag for traceability.

Configure only endpoints you own or have permission to monitor. Configuration is read at startup. In Docker, localhost refers to this container; adjust URLs when monitoring other services.

## Architecture and decisions

Browser → read-only HTTP API → SQLite. A background worker probes trusted configured services and writes check results and incident transitions. A failed check opens one incident per service; a successful check resolves it. The demo opens an incident after two consecutive failures and resolves it after two consecutive successes. Every probe result still counts toward sample availability.

The initial version uses Python's standard library so installation is simple. SQLite is adequate for one local process. Probes run concurrently with at most eight worker threads; larger service lists are queued. A cycle completes when its probes finish, so its slowest probe still affects the next cycle start. Availability is calculated over the latest 120 checks, not elapsed time. The worker waits the configured interval after each full cycle.

## Planned advanced releases — not implemented

1. Retention, structured logs, and richer Prometheus metrics.
2. PostgreSQL, authenticated administration, separate scheduler/workers, and audit records.
3. Notification delivery with retry queues, incident acknowledgement, and maintenance windows.
4. Production AWS infrastructure, tighter IAM, secret management, and enforced budget controls.
5. Managed cloud deployment, Kubernetes rollback demonstrations, image signing/SBOM generation, and automated release promotion.
6. Load tests, failure-injection experiments, SLO reporting, and an operational runbook.

## Before publishing a live demo

Keep the prototype bound to localhost. Its status API exposes configured endpoint URLs and error details. The standard-library HTTP server is for local demonstration, not public production hosting. Before internet exposure add authentication, a production server/reverse proxy, TLS, SSRF controls (including redirect and DNS handling), credential redaction, rate limits, retention, and operational monitoring. No secrets should be placed in repository configuration.

## Recruiter evidence and interview preparation

Record a short demo showing healthy service → outage → incident → recovery. Include actual test output and a screenshot. Be prepared to explain the incident state machine, timeout handling, sample-based availability, SQLite transactions, Docker networking, and how you would scale the worker.

This first version was created with AI assistance. Review, run, modify, and understand it before describing it on your resume. Claim only features you have verified; do not present planned cloud infrastructure as deployed work.

## Terraform foundation (AWS)

The `terraform/` folder contains a minimal AWS provider configuration for
`us-east-1`, a read-only availability zone data source, and an output for
availability zone names. It defines no AWS resources.

Completed checks:
- `terraform init` downloaded the provider and created the dependency lock file.
- `terraform validate` passed.
- `terraform fmt` completed.

The original read-only foundation remains separate from the deployment roots.

### Automated Terraform checks

GitHub Actions checks formatting, provider initialization with the backend disabled,
configuration validation, host mocked tests, and bootstrap shell syntax across
all three Terraform roots. These checks require no AWS credentials.

### Verified AWS demonstration - October 19, 2026

Terraform deployed the network foundation and a temporary Amazon Linux EC2 host
running the digest-pinned public container. The dashboard was accessed privately
through Systems Manager, with no inbound security-group rules.

Health, metrics, timed outage/recovery, persistence after container replacement,
and automatic recovery with preserved history after a real host reboot passed.
The demo host, both disks, and its IAM role/profile were then deleted. The network
foundation remains. There is no running AWS dashboard to visit now.

See [AWS demo results](docs/AWS_DEMO_RESULTS.md),
[deployment readiness](docs/AWS_DEPLOYMENT_READINESS.md), and
[architecture and operating plan](docs/AWS_DEPLOYMENT_PLAN.md).

### Monitoring readiness

The HTTP server can remain alive after its monitoring worker stops. /readyz
now returns 503 during startup, stale worker progress, failure, or shutdown,
and 200 after a fresh completed monitoring cycle. /healthz remains the process
liveness endpoint. Failed monitored targets do not make the monitor unready.

The dashboard displays worker state, /api/status includes monitoring progress,
and /metrics exports observatory_monitor_ready and the completed-cycle age.
Kubernetes readiness uses /readyz; liveness continues to use /healthz.
Freshness uses monotonic time and an envelope of max(30 seconds,
2 * (interval + sum of configured probe timeouts)). Demo mode uses 30 seconds.
This conservative envelope tolerates queued probes; it is not an SLA and can
be generous for large service lists. It does not prove current database
writability or restart a failed worker automatically.

The new behavior has local HTTP and state-transition tests; the historical AWS
image/digest in the deployment evidence predates it. Rebuild the local image
before applying the updated Kubernetes manifest. Existing published images do
not automatically gain new endpoints.
