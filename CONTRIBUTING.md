# Contributing

Thanks for contributing.

## Development Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
cp config.toml.example config.toml
```

## Before Opening a PR

- Run tests: `python3 -m unittest -v`
- Keep secrets out of git (`.env`, `config.toml`, `data/` are local-only).
- Keep changes focused and include clear commit messages.
- Update README/docs when behavior changes.

## Code Guidelines

- Keep filtering/business logic deterministic and easy to test.
- Handle external failures gracefully (WG sites, Telegram, OpenAI).
- Prefer small functions with explicit input/output.

## Pull Requests

- Describe what changed and why.
- Mention test coverage for your change.
- Include any manual verification steps for scraper/runtime behavior.
