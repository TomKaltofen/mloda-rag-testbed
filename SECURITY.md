# Security

This app exists to be scanned. It plants a secret, a retrieval canary, and a poisoned document on
purpose (see [README.md](README.md)), and its whole isolation layer is designed to be probed for
leaks. Finding those is the intended use, not a vulnerability report.

If you find a genuine bug in the app itself, something outside the documented scenarios, for
example a crash, an unintended information leak that is not one of the planted artifacts, or a
dependency CVE, please open a [GitHub issue](https://github.com/TomKaltofen/mloda-rag-testbed/issues)
or, for something sensitive, use GitHub's private vulnerability reporting on this repository.

Do not run this app on a host with sensitive data reachable, or with real credentials in its
environment; see the Security note in the README for why.
