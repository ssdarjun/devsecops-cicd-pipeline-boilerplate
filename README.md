# DevSecOps CI/CD Pipeline Boilerplate

> A production-grade CI/CD pipeline built with **GitHub Actions** that automates build, test, and security gate validation for containerized Python applications. It enforces **shift-left security** by integrating SAST, SCA, container image scanning, and automated quality gates — all before code reaches production.

![Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)
![Security](https://img.shields.io/badge/Security-Trivy_%7C_Bandit_%7C_pip--audit-red?logo=aquasecurity)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Container-Docker_Multi--Stage-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Pipeline Architecture

```
  Push / PR
      │
      ▼
┌─────────────┐
│  1. Lint    │  flake8 — syntax & style validation
└──────┬──────┘
       │
  ┌────┴────┐
  ▼         ▼
┌──────┐  ┌──────┐
│ SAST │  │ SCA  │  Bandit (code) + pip-audit (deps) — run in parallel
└──┬───┘  └───┬──┘
   └────┬─────┘
        ▼
┌───────────────┐
│  Unit Tests   │  pytest + coverage (≥80% required)
└───────┬───────┘
        ▼
┌───────────────────┐
│ Container Build & │  Docker multi-stage build + Trivy image scan
│    Image Scan     │
└───────┬───────────┘
        ▼
┌───────────────┐
│ Quality Gate  │  Aggregates all stage results — blocks on any failure
└───────────────┘
```

---

## Security Controls (Shift-Left Model)

| Stage | Tool | What It Catches | Blocks Pipeline |
|---|---|---|---|
| **SAST** | [Bandit](https://bandit.readthedocs.io/) | Insecure code patterns (hardcoded secrets, SQL injection, etc.) | ✅ Yes — High/Critical |
| **SCA** | [pip-audit](https://pypi.org/project/pip-audit/) | Known CVEs in third-party Python packages | ✅ Yes — Any vulnerability |
| **Container Scan** | [Trivy](https://trivy.dev/) | OS package CVEs, misconfigurations in the Docker image | ✅ Yes — High/Critical |
| **Filesystem Scan** | [Trivy](https://trivy.dev/) | Secrets and IaC misconfigurations in the repo | ✅ Yes — High/Critical |
| **Dependency Review** | [GitHub Action](https://github.com/actions/dependency-review-action) | New vulnerable dependencies introduced in a PR | ✅ Yes — High/Critical |
| **Scheduled Scan** | [Trivy](https://trivy.dev/) | Newly disclosed CVEs against the existing codebase | ⚠️ Alerts only (nightly) |

---

## Project Structure

```
devsecops-cicd-pipeline-boilerplate/
│
├── .github/
│   └── workflows/
│       ├── devsecops-pipeline.yml   # Main CI pipeline (6 stages)
│       ├── dependency-review.yml    # PR dependency gate
│       └── scheduled-scan.yml       # Nightly Trivy repo scan
│
├── app/
│   ├── main.py                      # Flask application
│   ├── requirements.txt             # Production dependencies
│   ├── requirements-dev.txt         # Dev/test dependencies
│   └── tests/
│       └── test_main.py             # pytest unit tests
│
├── Dockerfile                       # Multi-stage Docker build (non-root)
├── .dockerignore                    # Excludes secrets & build artefacts
├── .flake8                          # Linting configuration
├── .bandit                          # SAST configuration
├── .trivyignore                     # Documented CVE exceptions
├── .gitignore
├── pyproject.toml                   # pytest & coverage configuration
├── SECURITY.md                      # Vulnerability disclosure policy
└── README.md
```

---

## Workflow Details

### `devsecops-pipeline.yml` — Main CI Pipeline

Triggered on every `push` to `main`/`develop` and every pull request targeting `main`.

#### Stage 1 — Lint
```yaml
- name: Run flake8
  run: flake8 app/ --max-line-length=100
```
Validates PEP 8 compliance and catches syntax errors before any heavier tooling runs.

#### Stage 2 — SAST (Static Application Security Testing)
```yaml
- name: Run Bandit SAST Scan
  run: bandit -r app/ --severity-level medium --format json --output bandit-report.json
```
Bandit scans Python source code for over 40 classes of security issues including:
- Hardcoded passwords and secret keys
- Use of insecure functions (`subprocess`, `eval`, `exec`)
- SQL injection risk patterns
- Weak cryptography

**Quality Gate:** Fails the build if any **High** or **Critical** finding is detected.

#### Stage 3 — SCA (Software Composition Analysis)
```yaml
- name: Run pip-audit SCA Scan
  run: pip-audit --requirement app/requirements.txt --format json
```
Cross-references every declared dependency against the [OSV](https://osv.dev/) and [PyPA Advisory DB](https://github.com/pypa/advisory-database) for known CVEs.

**Quality Gate:** Fails the build if **any** unpatched vulnerability is found.

#### Stage 4 — Unit Tests & Coverage
```yaml
- name: Run Tests with Coverage
  run: pytest app/tests/ --cov=app --cov-fail-under=80
```
Runs the full test suite and enforces a **minimum 80% code coverage** threshold.

#### Stage 5 — Container Build & Image Scan
```yaml
- name: Run Trivy Image Vulnerability Scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: "devsecops-app:${{ github.sha }}"
    severity: "CRITICAL,HIGH"
    exit-code: "1"
    ignore-unfixed: true
```
- Builds a **multi-stage Docker image** to minimise the attack surface.
- Runs as a **non-root user** (`appuser`) inside the container.
- Trivy scans the final image for OS-level and application-level CVEs.
- Results are uploaded to **GitHub Security → Code Scanning** as SARIF.

**Quality Gate:** Fails the build if any **High** or **Critical** patched CVE is found.

#### Stage 6 — Quality Gate
Aggregates all five upstream stage results. The build is **blocked** unless every stage reports `success`. A single failure is surfaced clearly in the Actions UI.

---

### `dependency-review.yml` — PR Dependency Gate

Runs exclusively on pull requests. Uses [GitHub's Dependency Review Action](https://github.com/actions/dependency-review-action) to block merges that introduce new packages with known High or Critical CVEs. Automatically posts a summary comment on the PR.

---

### `scheduled-scan.yml` — Nightly Security Scan

Runs at **02:00 UTC** every day (or manually via `workflow_dispatch`). Scans the full repository with Trivy to catch newly disclosed CVEs against existing dependencies. Results are surfaced in GitHub Security.

---

## Multi-Stage Dockerfile

The image uses a **builder/runtime pattern** to minimise the final image footprint:

```dockerfile
# Build stage — installs dependencies
FROM python:3.12-slim AS builder
...

# Runtime stage — copies only the installed packages
FROM python:3.12-slim AS runtime
RUN useradd --system appuser   # Non-root user
USER appuser
...
```

Security hardening applied:
- ✅ Non-root runtime user
- ✅ Minimal `python:3.12-slim` base (fewer packages = smaller attack surface)
- ✅ No secrets or dev tools in the final image
- ✅ Docker `HEALTHCHECK` configured
- ✅ `.dockerignore` excludes `.env` files and git history

---

## Getting Started

### Prerequisites
- Python 3.12+
- Docker
- GitHub repository with Actions enabled

### Local Development

```bash
# Clone the repository
git clone https://github.com/<your-username>/devsecops-cicd-pipeline-boilerplate.git
cd devsecops-cicd-pipeline-boilerplate

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# Install dependencies
pip install -r app/requirements.txt -r app/requirements-dev.txt
```

### Run the Application Locally

```bash
python app/main.py
# → Listening on http://localhost:8080
```

### Run the Full Security & Test Suite Locally

```bash
# Lint
flake8 app/

# SAST
bandit -r app/ --exclude app/tests --severity-level medium

# SCA
pip-audit --requirement app/requirements.txt

# Unit Tests + Coverage
pytest app/tests/ --cov=app --cov-report=term-missing

# Container build + scan (requires Docker and Trivy CLI)
docker build -t devsecops-app:local .
trivy image --severity CRITICAL,HIGH devsecops-app:local
```

### Build & Run the Docker Image

```bash
docker build -t devsecops-app:local .
docker run -p 8080:8080 devsecops-app:local
curl http://localhost:8080/health
# → {"status": "healthy"}
```

---

## Adapting This Boilerplate

| Goal | What to change |
|---|---|
| Use a different language | Replace `main.py`, `requirements*.txt`, `flake8`/`bandit` steps with language equivalents |
| Push image to a registry | Add `docker/login-action` + set `push: true` in `build-push-action` |
| Add DAST | Append an OWASP ZAP step after the container is started in a service container |
| Notify on failure | Add a Slack/Teams notification step in `quality-gate` with `if: failure()` |
| Raise coverage threshold | Change `--cov-fail-under=80` in the test stage |
| Adjust severity threshold | Change `severity: "CRITICAL,HIGH"` in Trivy steps |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
