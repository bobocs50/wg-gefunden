"""
Regression tests for the last-resort crash reporter.

Guards against the 2026-06-29 incident where a missing ``config.toml`` on the
server made every cron invocation of ``main.py`` and ``scripts/heartbeat.py``
die at import time, with no Telegram alert.
"""
import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from src import crash_alert


ROOT = Path(__file__).resolve().parent.parent


class TestFormatAlert(unittest.TestCase):
    def test_alert_contains_entry_point_and_exception_type(self):
        try:
            raise FileNotFoundError("config.toml missing")
        except FileNotFoundError as exc:
            msg = crash_alert.format_alert("main.py", type(exc), exc, exc.__traceback__)
        self.assertIn("main.py", msg)
        self.assertIn("FileNotFoundError", msg)
        self.assertIn("config.toml missing", msg)

    def test_alert_traceback_is_truncated(self):
        try:
            raise ValueError("x" * 10_000)
        except ValueError as exc:
            msg = crash_alert.format_alert("main.py", type(exc), exc, exc.__traceback__)
        # The message header + 1500 char tail. Keep a generous ceiling.
        self.assertLess(len(msg), 3000)


class TestInstallExcepthook(unittest.TestCase):
    def setUp(self):
        self._original_hook = sys.excepthook
        self._sent = []

    def tearDown(self):
        sys.excepthook = self._original_hook

    def _capture(self, text):
        self._sent.append(text)

    def test_hook_sends_on_uncaught_exception(self):
        crash_alert.install_excepthook("main.py", send=self._capture)
        try:
            raise RuntimeError("boom")
        except RuntimeError as exc:
            sys.excepthook(type(exc), exc, exc.__traceback__)
        self.assertEqual(len(self._sent), 1)
        self.assertIn("boom", self._sent[0])
        self.assertIn("main.py", self._sent[0])

    def test_hook_ignores_systemexit(self):
        crash_alert.install_excepthook("main.py", send=self._capture)
        with patch.object(sys, "__excepthook__", lambda *a: None):
            sys.excepthook(SystemExit, SystemExit(0), None)
        self.assertEqual(self._sent, [])

    def test_hook_ignores_keyboard_interrupt(self):
        crash_alert.install_excepthook("main.py", send=self._capture)
        sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
        self.assertEqual(self._sent, [])

    def test_hook_survives_send_failure(self):
        def broken_send(_text):
            raise RuntimeError("telegram down")

        crash_alert.install_excepthook("main.py", send=broken_send)
        # The hook must NOT raise even if the alerter itself throws —
        # letting an exception escape the excepthook is worse than being silent.
        try:
            raise ValueError("real error")
        except ValueError as exc:
            sys.excepthook(type(exc), exc, exc.__traceback__)


class TestEntryPointsWireInHook(unittest.TestCase):
    """The excepthook only fires if the entry point actually installs it.
    A regex check on the source keeps that wiring from silently regressing.
    """

    def test_main_py_installs_excepthook_before_config_import(self):
        text = (ROOT / "main.py").read_text()
        install_idx = text.find("install_excepthook(")
        config_idx = text.find("from src.config")
        self.assertGreater(install_idx, 0, "main.py must call install_excepthook")
        self.assertGreater(config_idx, install_idx,
                           "install_excepthook must run before src.config is imported")

    def test_heartbeat_installs_excepthook_before_config_import(self):
        text = (ROOT / "scripts" / "heartbeat.py").read_text()
        install_idx = text.find("install_excepthook(")
        config_idx = text.find("from src.config")
        self.assertGreater(install_idx, 0, "heartbeat.py must call install_excepthook")
        self.assertGreater(config_idx, install_idx,
                           "install_excepthook must run before src.config is imported")


class TestConfigLoaderErrorMessage(unittest.TestCase):
    """config.toml missing is the most common cause of the silent crash.
    The loader error message should name the file and the fix — it becomes
    the body of the Telegram alert.
    """

    def test_missing_config_toml_error_names_the_file_and_the_fix(self):
        from src.config import _load, ROOT_DIR
        with patch("src.config.ROOT_DIR", ROOT_DIR / "definitely-does-not-exist"):
            try:
                _load()
                self.fail("expected FileNotFoundError")
            except FileNotFoundError as e:
                msg = str(e)
                self.assertIn("config.toml", msg)
                self.assertIn("config.toml.example", msg)


class TestSubprocessCrashAlert(unittest.TestCase):
    """End-to-end: run a fresh Python subprocess that imports crash_alert,
    installs the excepthook, and then raises. Verify the alert function is called.

    Simulating the actual ``main.py`` crash-on-missing-config in a subprocess
    would require a fake Telegram HTTP server; instead we drive the same
    excepthook mechanism with a captured-side-channel send.
    """

    def test_uncaught_exception_in_subprocess_triggers_alert(self):
        # Use a scratch file to capture the "sent" alert since we can't share
        # mocks across processes.
        marker = ROOT / "tests" / "_crash_alert_marker.tmp"
        marker.unlink(missing_ok=True)

        script = textwrap.dedent(f"""
            import sys, pathlib
            sys.path.insert(0, {str(ROOT)!r})
            from src import crash_alert

            def capture(text):
                pathlib.Path({str(marker)!r}).write_text(text)

            crash_alert.install_excepthook("test_entry", send=capture)
            raise FileNotFoundError("config.toml not found at /root/wggefunden/config.toml")
        """)
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(marker.exists(),
                        f"expected crash alert marker file to be written. stderr:\n{result.stderr}")
        body = marker.read_text()
        self.assertIn("test_entry", body)
        self.assertIn("FileNotFoundError", body)
        self.assertIn("config.toml", body)
        marker.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
