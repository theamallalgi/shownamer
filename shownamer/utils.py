# utils.py - filename parsing, cleaning etc.

from __future__ import annotations

import re
from typing import Any

COMMON_TAGS = [
    "1080p",
    "720p",
    "2160p",
    "x264",
    "x265",
    "bluray",
    "brrip",
    "webrip",
    "hdrip",
    "dvdrip",
    "web-dl",
    "hdtv",
    "unrated",
    "extended",
    "proper",
    "limited",
]

ANIME_VIDEO_TAGS = [
    "480p",
    "576p",
    "720p",
    "1080p",
    "1440p",
    "2160p",
    "4k",
    "8k",
    "x264",
    "x265",
    "h264",
    "h265",
    "hevc",
    "av1",
]

ANIME_SOURCE_TAGS = [
    "bluray",
    "brrip",
    "webrip",
    "web-dl",
    "webdl",
    "hdtv",
    "dvdrip",
    "dvd",
]

ANIME_AUDIO_TAGS = [
    "aac",
    "flac",
    "opus",
    "ac3",
    "eac3",
]

ANIME_OTHER_TAGS = [
    "dual audio",
    "dual",
    "multi audio",
    "multi",
    "dub",
    "sub",
    "uncut",
    "remux",
]


def clean_filename_movie(filename: str) -> str:
    name = re.sub(r"[._\-]+", " ", filename)
    name = re.sub(r"\s+", " ", name).strip()
    for tag in COMMON_TAGS:
        name = re.sub(rf"\b{tag}\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name).strip()
    name = " ".join(word.capitalize() for word in name.split())
    return name


def extract_title_and_year(filename: str) -> tuple[str, str | None]:
    name = clean_filename_movie(filename)
    years = re.findall(r"(19\d{2}|20\d{2})", name)
    year = years[0] if years else None
    if year:
        name = name.split(year)[0].strip()
    return name, year


def extractTitleFallback(raw: str) -> tuple[str | None, str | None]:
    years = re.findall(r"(19\d{2}|20\d{2})", raw)
    if not years:
        return None, None

    year = years[0]
    before_year = raw.split(year)[0]

    # strip leading domain/site junk: e.g. "[www.site.com] - " or "www.site.com - "
    before_year = re.sub(r"^.*?(?:[-–]\s*|\]\s*|\)\s*)", "", before_year)
    before_year = re.sub(r"[._\-\(\)]+", " ", before_year)
    before_year = re.sub(r"\s+", " ", before_year).strip()

    for tag in COMMON_TAGS:
        before_year = re.sub(rf"\b{tag}\b", "", before_year, flags=re.IGNORECASE)

    title = " ".join(word.capitalize() for word in before_year.split()).strip()

    return (title if title else None), year


def parse_filename(filename: str, is_movie: bool = False):
    if is_movie:
        title, year = extract_title_and_year(filename)
        return {"name": title, "year": year, "is_movie": True}

    patterns = [
        re.compile(r"^(.*?)(?:S(\d{1,2})E(\d{1,2}))", re.IGNORECASE),
        re.compile(r"^(.*?)(?:(\d{1,2})x(\d{1,2}))", re.IGNORECASE),
        re.compile(r"^(.*?)(?:E(\d{1,2}))", re.IGNORECASE),
    ]

    for pattern in patterns:
        match = pattern.match(filename)
        if match:
            name = match.group(1).replace(".", " ").replace("_", " ").strip()
            if len(match.groups()) == 3:
                season = int(match.group(2))
                episode = int(match.group(3))
            else:
                season = 1
                episode = int(match.group(2))
            return {
                "name": name,
                "season": season,
                "episode": episode,
                "is_movie": False,
            }

    return None


def extract_anime_episode(filename: str) -> tuple[int | None, str, str]:
    """Extract episode number, title, and episode title."""
    patterns = [
        r"\bEpisode[\s._-]*(\d+)\b",
        r"\bEp[\s._-]*(\d+)\b",
        r"\bE(\d+)\b",
        r"\bS\d{1,2}E(\d+)\b",
        r"\b\d{1,2}x(\d+)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)

        if match:
            episode = int(match.group(1))
            title = filename[: match.start()]
            episode_title = filename[match.end() :]

            return episode, title, episode_title

    standalone_pattern = r"(?<!\d)[-.\s]\[?(\d{1,4})\]?(?=[-.\s]|$)"

    matches = list(re.finditer(standalone_pattern, filename))

    for match in reversed(matches):
        number = int(match.group(1))

        if number in {480, 576, 720, 1080, 1440, 2160}:
            continue

        title = filename[: match.start()]
        episode_title = filename[match.end() :]

        return number, title, episode_title

    return None, filename, ""


def strip_anime_release_tags(filename: str) -> str:
    """Remove common anime release tags from a filename."""
    tags = [
        r"\b\d{3,4}p\b",
        r"\b(?:4k|8k)\b",
        r"\b(?:x264|x265|h264|h265|hevc|av1)\b",
        r"\b(?:bluray|brrip|webrip|web-dl|webdl|hdtv|dvdrip|dvd)\b",
        r"\b(?:aac|flac|opus|ac3|eac3)\b",
        r"\b(?:dual audio|dual|multi audio|multi|du)\b",
    ]

    for pattern in tags:
        filename = re.sub(pattern, "", filename, flags=re.IGNORECASE)

    filename = re.sub(r"\[[^\]]*\]", "", filename)
    filename = re.sub(r"\([^)]*\)", "", filename)

    # Collapse whitespace.
    filename = re.sub(r"\s+", " ", filename)

    # Collapse repeated separators.
    filename = re.sub(r"(?:\s*-\s*){2,}", " - ", filename)

    # Remove separators left at the beginning/end.
    filename = filename.strip(" .-_")

    return filename


def parse_anime_filename(filename: str) -> dict[str, Any]:
    """Extract useful information from an anime filename."""
    episode, title, episode_title = extract_anime_episode(filename)

    title = strip_anime_release_tags(title)
    episode_title = strip_anime_release_tags(episode_title)

    return {
        "title": title,
        "episode": episode,
        "episode_title": episode_title,
    }


ILLEGAL_CHARS = r'[\x00<>:"/\\|?*]'


def clean_show_name(name: str, subst_char: str = "_") -> str:
    return re.sub(ILLEGAL_CHARS, subst_char, name)


def validate_format(format_str: str) -> None:
    if re.search(ILLEGAL_CHARS, format_str):
        raise ValueError(f"Illegal character found in format string: {format_str}")
