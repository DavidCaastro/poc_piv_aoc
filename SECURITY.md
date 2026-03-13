# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 1.x (current) | ✅ |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

To report a security vulnerability, please use one of these channels:

1. **GitHub Private Vulnerability Reporting** (preferred):
   Go to the [Security tab](../../security/advisories/new) of this repository
   and click "Report a vulnerability".

2. **Email:** Contact the repository owner directly via GitHub profile.

### What to include in your report

- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (optional)

### Response timeline

- **Acknowledgement:** Within 48 hours
- **Initial assessment:** Within 7 days
- **Fix timeline:** Depends on severity — critical issues prioritized

### Scope

This is a portfolio/demo project. The following are **in scope**:

- Authentication bypass
- Authorization escalation (RBAC/ownership)
- Token forgery or replay attacks
- Rate limiting bypass
- Injection vulnerabilities (though no SQL is used)
- Information disclosure via error messages

The following are **out of scope** (known limitations by design):

- In-memory storage losing state on restart
- Credentials visible in demo documentation (they are test-only users)
- Render free tier cold start latency

## Security Design Principles Applied

See [README.md](README.md#principios-de-seguridad-aplicados) for the full list of
security mechanisms implemented in this project.
