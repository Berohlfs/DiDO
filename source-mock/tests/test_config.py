"""Matrix 3 — config.load_config(env_path)."""
import os
import tempfile
import unittest
from unittest import mock

from ingest import config


FULL = """
# DiDO ingest config
GBRAIN_BASE_URL=http://localhost:8787
GBRAIN_CLIENT_ID=gbrain_cl_abc
GBRAIN_CLIENT_SECRET=gbrain_cs_xyz
"""


class TestLoadConfig(unittest.TestCase):
    def _write(self, text):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        with open(path, "w") as f:
            f.write(text)
        self.addCleanup(os.remove, path)
        return path

    # Matrix 3: valid full .env → populated Config with defaults applied
    def test_valid_full(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = config.load_config(self._write(FULL))
        self.assertEqual(cfg.base_url, "http://localhost:8787")
        self.assertEqual(cfg.client_id, "gbrain_cl_abc")
        self.assertEqual(cfg.client_secret, "gbrain_cs_xyz")
        # defaults
        self.assertEqual(cfg.scopes, "read write")
        self.assertEqual(cfg.sources_dir, "sources")
        self.assertEqual(cfg.log_dir, ".ingest-logs")
        self.assertEqual(cfg.max_bytes, 1_048_576)

    # Matrix 3: missing required key → clear error
    def test_missing_required(self):
        text = "GBRAIN_CLIENT_ID=x\nGBRAIN_CLIENT_SECRET=y\n"
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(config.ConfigError):
                config.load_config(self._write(text))

    # Matrix 3: real env var overrides .env value
    def test_env_overrides_file(self):
        with mock.patch.dict(os.environ, {"GBRAIN_BASE_URL": "http://override:9999"}, clear=True):
            cfg = config.load_config(self._write(FULL))
        self.assertEqual(cfg.base_url, "http://override:9999")

    # Matrix 3: defaults applied when keys absent; overrides honored when present
    def test_overridable_defaults(self):
        text = FULL + "GBRAIN_SCOPES=read\nGBRAIN_MAX_BYTES=512\nGBRAIN_SOURCES_DIR=in\nGBRAIN_LOG_DIR=logs\n"
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = config.load_config(self._write(text))
        self.assertEqual(cfg.scopes, "read")
        self.assertEqual(cfg.max_bytes, 512)
        self.assertEqual(cfg.sources_dir, "in")
        self.assertEqual(cfg.log_dir, "logs")

    # Matrix 3: comments and blank lines ignored
    def test_comments_blank_lines(self):
        text = "\n\n# comment\n   # indented comment\n" + FULL
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = config.load_config(self._write(text))
        self.assertEqual(cfg.client_id, "gbrain_cl_abc")

    # Matrix 3: value containing '=' splits on first '='
    def test_value_with_equals(self):
        text = "GBRAIN_BASE_URL=http://x\nGBRAIN_CLIENT_ID=id\nGBRAIN_CLIENT_SECRET=YWJjZA==\n"
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = config.load_config(self._write(text))
        self.assertEqual(cfg.client_secret, "YWJjZA==")

    # Matrix 3: surrounding whitespace trimmed
    def test_whitespace_trimmed(self):
        text = "GBRAIN_BASE_URL =  http://x  \nGBRAIN_CLIENT_ID = id \nGBRAIN_CLIENT_SECRET = sec \n"
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = config.load_config(self._write(text))
        self.assertEqual(cfg.base_url, "http://x")
        self.assertEqual(cfg.client_id, "id")
        self.assertEqual(cfg.client_secret, "sec")

    # Matrix 3: missing env file but env vars present → still loads
    def test_missing_file_uses_env(self):
        env = {
            "GBRAIN_BASE_URL": "http://x",
            "GBRAIN_CLIENT_ID": "id",
            "GBRAIN_CLIENT_SECRET": "sec",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = config.load_config("/nonexistent/.env")
        self.assertEqual(cfg.base_url, "http://x")


if __name__ == "__main__":
    unittest.main()
