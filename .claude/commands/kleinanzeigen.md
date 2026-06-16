# Kleinanzeigen Hamburg Apartment Scanner

Run the Playwright-based scanner and report results.

## Step 1 — Run the scan

```bash
cd /Users/philipp/Documents/Repos/wggesucht && venv/bin/python3 scripts/kleinanzeigen_scan.py
```

## Step 2 — Report

Relay the one-line summary from the script output:
`Kleinanzeigen: X listings found · Y new · Z passed filters · N notifications sent`

If the script prints `WARNING: no cards — possible bot detection`, report that Kleinanzeigen
is blocking headless Chromium and suggest the user run it from a machine with a fresh IP
or add a residential proxy.
