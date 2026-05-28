#!/usr/bin/env python3
"""
Daily heartbeat — run via cron at 07:00 to confirm the bot is alive.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from datetime import datetime
import src.telegram as telegram

now = datetime.now().strftime("%d.%m.%Y %H:%M")
telegram.send(f"✅ WG-Gesucht bot is running\n🕐 {now}")
