## Security Policy

### Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | ✅ Yes             |
| develop | ✅ Yes             |
| others  | ❌ No              |

### Reporting a Vulnerability

If you discover a security vulnerability in this project, please **do not** open a public GitHub issue.

Instead, report it privately via [GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) or by contacting the maintainer directly.

We aim to triage and respond to all security reports within **72 hours**.

### Security Controls in This Project

| Control               | Tool          | Stage       |
| --------------------- | ------------- | ----------- |
| Static Analysis (SAST)| Bandit        | Pre-build   |
| Dependency Scan (SCA) | pip-audit     | Pre-build   |
| Container Image Scan  | Trivy         | Post-build  |
| Scheduled Repo Scan   | Trivy         | Nightly     |
| Dependency Review     | GitHub Action | On PR       |

