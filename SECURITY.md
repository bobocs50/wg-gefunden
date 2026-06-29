# Security Policy

## Supported Versions

Security fixes are provided for the latest `main` branch.

## Reporting a Vulnerability

Please do not open public issues for security problems.

- Email: **bobocs50@proton.me**
- Subject: `SECURITY: WG-Gesucht Agent`
- Include:
  - affected file/module
  - reproduction steps
  - expected vs actual behavior
  - potential impact

I will acknowledge receipt within 72 hours and share remediation status as fixes are prepared.

## Sensitive Data Handling

- Never commit `.env`, `config.toml`, runtime `data/`, or credentials.
- Rotate credentials immediately if a leak is suspected.
