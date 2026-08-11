# titleembed.py - does embed have two e's or is it the d's? bah!
# XXX: to tweak - perf

import subprocess
from pathlib import Path
from typing import Any

from mutagen import MutagenError


def buildShowTitle(name: str, season: int, episode: int, title: str) -> str:
    return f"S{season:02}xE{episode:02} - {title}"


def buildMovieTitle(name: str, year: str) -> str:
    return f"{name} ({year})"


def _embedViaffmpeg(filePath: Path, titleStr: str) -> bool:
    tmpPath = filePath.with_name(filePath.stem + ".sntmp" + filePath.suffix)
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(filePath),
                "-metadata",
                f"title={titleStr}",
                "-codec",
                "copy",
                str(tmpPath),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            filePath.unlink()
            tmpPath.rename(filePath)
            return True
    except FileNotFoundError:
        pass
    finally:
        if tmpPath.exists():
            tmpPath.unlink(missing_ok=True)
    return False


def _embedViaMutagen(filePath: Path, titleStr: str) -> bool:
    try:
        from mutagen.mp4 import MP4
    except ImportError:
        return False

    try:
        tags: Any = MP4(str(filePath))
        tags["\xa9nam"] = [titleStr]
        tags.save()
        return True
    except (OSError, ValueError, KeyError, MutagenError):
        return False


def embedTitle(filePath: Path, titleStr: str) -> bool:
    ext = filePath.suffix.lower()
    if ext in (".mp4", ".m4v", ".mov"):
        return _embedViaMutagen(filePath, titleStr) or _embedViaffmpeg(
            filePath, titleStr
        )
    return _embedViaffmpeg(filePath, titleStr)
