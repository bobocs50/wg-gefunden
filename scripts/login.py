"""One-shot manual login — only needed to create the initial session.json.
After that, main.py re-logins automatically when the session expires."""
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv()

from src.auth import ensure_session


def main():
    if not ensure_session():
        raise SystemExit("Login failed — check WGG_EMAIL / WGG_PASSWORD in .env")
    print("Done.")


if __name__ == "__main__":
    main()
