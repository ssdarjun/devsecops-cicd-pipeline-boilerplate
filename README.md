# DevSecOps CI/CD Pipeline Boilerplate

A production-grade CI/CD pipeline built with **GitHub Actions** that automates build, test, and security gate validation for containerized applications. It enforces shift-left security by integrating SAST, SCA, and automated container scanning.

## Pipeline Workflow
1. **Code Checkout & Linting:** Validates syntax and formatting.
2. **SAST (Static Application Security Testing):** Scans raw code for security vulnerabilities using static analysis tools.
3. **SCA (Software Composition Analysis):** Checks third-party dependencies for known CVEs via automated dependency scanners.
4. **Container Build & Image Scan:** Builds a multi-stage Docker image and scans it using **Trivy**.
5. **Quality Gate Decision:** Automatically *fails* the build if a Critical or High vulnerability is discovered.

## Automated Security Gates Example (GitHub Actions snippet)
```yaml
name: DevSecOps CI Pipeline
on: [push, pull_request]
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Run Trivy Vulnerability Scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
