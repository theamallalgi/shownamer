import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# Allow running tests without mutagen installed in minimal environments.
if "mutagen" not in sys.modules:
    sys.modules["mutagen"] = MagicMock()
    sys.modules["mutagen.mp4"] = MagicMock()
    sys.modules["mutagen.easyid3"] = MagicMock()

from shownamer.core import process_file


def _make_args(directory: str, **overrides: object) -> SimpleNamespace:
    defaults: dict[str, object] = {
        "dir": directory,
        "ext": ["mkv"],
        "movie": False,
        "anime": False,
        "name": None,
        "format": None,
        "verbose": True,
        "dry_run": True,
        "title": False,
        "char": "",
        "api_key": None,
        "tmdb_api_key": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestVerboseDryRunOutput(unittest.TestCase):
    def test_failed_show_lookup_does_not_print_redundant_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = "Breaking.Bad.S01E01.mkv"
            Path(tmpdir, filename).touch()
            args = _make_args(tmpdir, verbose=True, dry_run=True, title=False)

            buf = io.StringIO()
            with patch("shownamer.api.search_media", return_value=None):
                with redirect_stdout(buf):
                    process_file(filename, args)

            output = buf.getvalue()
            self.assertIn("[API Error] Could not find show", output)
            self.assertNotIn("[skip]", output)

    def test_failed_movie_lookup_does_not_print_redundant_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = "Inception.2010.mkv"
            Path(tmpdir, filename).touch()
            args = _make_args(
                tmpdir, movie=True, verbose=True, dry_run=True, title=False
            )

            buf = io.StringIO()
            with (
                patch("shownamer.api.get_tmdb_key", return_value=None),
                patch("shownamer.api.get_stored_omdb_key", return_value=None),
                patch("shownamer.api.get_omdb_key", return_value=None),
            ):
                with redirect_stdout(buf):
                    process_file(filename, args)

            output = buf.getvalue()
            self.assertIn("[API Error] Could not find movie", output)
            self.assertNotIn("[skip]", output)

    def test_unparseable_filename_prints_single_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = "random_file.mkv"
            Path(tmpdir, filename).touch()
            args = _make_args(tmpdir, verbose=True, dry_run=True, title=False)

            buf = io.StringIO()
            with redirect_stdout(buf):
                process_file(filename, args)

            lines = [line for line in buf.getvalue().splitlines() if "[skip]" in line]
            self.assertEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main()
