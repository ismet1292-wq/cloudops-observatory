# Validation for v0.4 — October 4, 2026

Executed in the Linux development workspace: `python3 -m unittest -v`.
Result: 12 tests passed.

Verified: HTTP health/failure probes and status API; metrics output; incident
opening, deduplication and recovery; latest-120-sample window; nearest-rank p95;
unsupported endpoint scheme rejection; threshold validation; persisted counters;
concurrent probes; timed demo boundaries; standalone lesson connection failure.

Also executed the actual app.py --demo process with a fresh database and an
automatically assigned local port. Observed healthy at 0 seconds, HTTP outage
at 10 seconds, an open incident at 12 seconds, recovery at 22 seconds, and the
same incident resolved at 24 seconds. Verified dashboard, metrics and health
routes returned HTTP 200. Dashboard JavaScript passed node --check.

Validated on Windows 11: local Python launch, Docker image build, container health endpoint, non-root UID/GID 10001, SQLite persistence through a named volume and container replacement, and GitHub-hosted CI.

Not executed: GHCR publication, Kubernetes deployment, AWS deployment, production load testing, or a production security audit. The project is a local prototype with supplied deployment files.
