# core.py - parse files, metadata resolving renaming, titles and such
# XXX: to tweak - perf (see: titleembed.py)

from __future__ import annotations

import os
import re
import shutil
import textwrap
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, Protocol

from shownamer.api import get_anime_episode, search_anime

from . import api, titleEmbed, utils
from .utils import parse_anime_filename

_anime_cache: dict[str, dict[str, Any] | None] = {}


class RenameArgs(Protocol):
    # INFO: shape of `argparse.Namespace` for this module.
    # INFO: used protocol instead of class because it works with `argparse.Namespace` with 0 cost @ runtime.
    dir: str
    ext: list[str]
    movie: bool
    anime: bool
    name: str | None
    format: str | None
    verbose: bool
    dry_run: bool
    title: bool
    char: str
    api_key: str | None
    tmdb_api_key: str | None


def process_directory(args: RenameArgs) -> None:
    if args.name:
        list_detected_media(args.dir, args.ext, args.movie, args)
        return

    filenames = [
        filename
        for filename in os.listdir(args.dir)
        if os.path.splitext(filename)[1][1:].lower() in [e.lower() for e in args.ext]
    ]

    if not args.anime:
        for filename in filenames:
            process_file(filename, args)
        return

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                partial(process_file, args=args),
                filenames,
            )
        )


def get_rating(media_info: dict[str, Any], source: str) -> str:
    for rating in media_info.get("Ratings", []):
        if rating.get("Source") == source:
            return rating.get("Value", "N/A")

    return "N/A"


def _print_field(label: str, value: Any) -> None:
    if value and value != "N/A":
        print(f"{label}: {value}")


def resolve_movie_metadata(
    name: str,
    year: str | None,
    raw: str,
    args: RenameArgs,
) -> dict[str, Any] | None:
    # INFO: hierarchy: tmdb > omdb (both optional)
    # INFO: if omdb key is stored (not prompted here), hybrid enrichment is applyed.

    tmdb_key_raw = args.tmdb_api_key or api.get_tmdb_key()
    tmdb_key: str | None = tmdb_key_raw if isinstance(tmdb_key_raw, str) else None

    omdb_hint_key = api.get_stored_omdb_key()

    if tmdb_key:
        media_info = api.fetch_tmdb_metadata(
            name,
            year,
            tmdb_key,
            omdb_hint_key,
        )

        if not media_info:
            fallback_title, fallback_year = utils.extractTitleFallback(raw)

            if fallback_title:
                if args.verbose:
                    print(
                        "  → [fallback] Retrying TMDb with "
                        f"extracted title: '{fallback_title}'"
                    )

                media_info = api.fetch_tmdb_metadata(
                    fallback_title,
                    fallback_year,
                    tmdb_key,
                    omdb_hint_key,
                )

        if media_info:
            if args.verbose:
                print(f"  → [TMDb] Match found: '{media_info.get('Title', name)}'")

            return media_info

        if args.verbose:
            print(f"  → [TMDb] No match for '{name}', falling back to OMDb")

    elif args.verbose:
        print("  → [TMDb] Skipped (no key configured)")

    omdb_key_raw = args.api_key or api.get_omdb_key()

    omdb_key: str | None = omdb_key_raw if isinstance(omdb_key_raw, str) else None

    if not omdb_key:
        if args.verbose:
            print("  → [OMDb] Skipped (no key configured)")

        return None

    media_info = api.fetch_omdb_metadata(
        name,
        year,
        omdb_key,
    )

    if not media_info:
        fallback_title, fallback_year = utils.extractTitleFallback(raw)

        if fallback_title:
            if args.verbose:
                print(
                    "  → [fallback] Retrying OMDb with "
                    f"extracted title: '{fallback_title}'"
                )

            media_info = api.fetch_omdb_metadata(
                fallback_title,
                fallback_year,
                omdb_key,
            )

    if media_info and args.verbose:
        print(f"  → [OMDb] Match found: '{media_info.get('Title', name)}'")

    return media_info


def process_file(
    filename: str,
    args: RenameArgs,
) -> None:
    if args.format:
        try:
            utils.validate_format(args.format)
        except ValueError as e:
            print(f"[!] Error: {e}")
            return

    if args.verbose:
        print(f"Processing: {filename}")

    file_path = os.path.join(args.dir, filename)
    raw_stem = os.path.splitext(filename)[0]

    # Anime
    if args.anime:
        file_info = parse_anime_filename(raw_stem)

        if file_info["episode"] is None:
            if args.verbose:
                print(f"[skip] Could not detect anime episode from '{filename}'")

            return

        anime_info = get_anime_metadata(raw_stem)

        if not anime_info:
            if args.verbose:
                print(f"[skip] Could not resolve anime metadata for '{filename}'")

            return

        format_str = args.format or "{title} - {episode:02}. {episode_title}"

        try:
            new_name = format_str.format(
                title=utils.clean_show_name(
                    anime_info["title"],
                    args.char,
                ),
                episode=anime_info["episode"],
                episode_title=utils.clean_show_name(
                    anime_info["episode_title"],
                    args.char,
                ),
            )

        except KeyError as e:
            print(f"[!] Unknown placeholder in --format: {e}")
            return

        file_ext = os.path.splitext(filename)[1]
        new_filename = new_name + file_ext
        new_filepath = os.path.join(
            args.dir,
            new_filename,
        )

        if filename == new_filename:
            print(f"[skip] '{filename}' already matches the target name.")

        elif not args.dry_run:
            if os.path.exists(new_filepath):
                print(f"[skip] '{new_filename}' already exists.")

            else:
                try:
                    print(f"[rename] '{filename}' → '{new_filename}'")

                    shutil.move(
                        file_path,
                        new_filepath,
                    )

                except OSError as e:
                    print(f"  → [!] Error renaming file: {e}")

        else:
            print(f"[rename] '{filename}' → '{new_filename}'")

        return

    # Movies / TV shows
    file_info = utils.parse_filename(
        raw_stem,
        args.movie,
    )

    if not file_info:
        if args.verbose:
            print(f"[skip] Could not parse file information from '{filename}'")

        return

    file_info["raw"] = raw_stem

    rename_succeeded = False
    new_name = ""
    new_filepath: str = file_path

    if args.movie:
        new_name = rename_movie(
            file_info,
            args,
        )

    else:
        if not file_info.get("is_movie"):
            new_name = rename_show(
                file_info,
                args,
            )

    if new_name:
        file_ext = os.path.splitext(filename)[1]
        new_filename = new_name + file_ext
        new_filepath = os.path.join(
            args.dir,
            new_filename,
        )

        if filename == new_filename:
            print(f"[skip] '{filename}' already matches the target name.")

        elif not args.dry_run:
            if os.path.exists(new_filepath):
                print(f"[skip] '{new_filename}' already exists.")

            else:
                try:
                    print(f"[rename] '{filename}' → '{new_filename}'")

                    shutil.move(
                        file_path,
                        new_filepath,
                    )

                    rename_succeeded = True

                except OSError as e:
                    print(f"  → [!] Error renaming file: {e}")

        else:
            print(f"[rename] '{filename}' → '{new_filename}'")

    if args.title:
        resolved_name = new_name if new_name else os.path.splitext(filename)[0]

        title_str = _buildTitleStr(
            resolved_name,
            args,
            file_info,
        )

        if args.dry_run:
            print(f"  → [title] Would embed: {title_str}")

        else:
            target_path = Path(new_filepath) if rename_succeeded else Path(file_path)

            success = titleEmbed.embedTitle(
                target_path,
                title_str,
            )

            if args.verbose:
                if success:
                    print(f"  → [title] Embedded: {title_str}")
                else:
                    print(
                        "  → [title] Failed to embed metadata (ffmpeg/mutagen required)"
                    )

    elif args.verbose and not new_name:
        print(f"[skip] No new name generated for '{filename}'")


def _buildTitleStr(
    resolvedName: str,
    args: RenameArgs,
    fileInfo: dict[str, Any],
) -> str:
    if args.format:
        return resolvedName

    if args.movie:
        name, _, year = resolvedName.rpartition(" (")

        return titleEmbed.buildMovieTitle(
            name,
            year.rstrip(")"),
        )

    season = fileInfo.get("season", 1)
    episode = fileInfo.get("episode", 1)

    title = resolvedName.split(" - ", 1)[-1] if " - " in resolvedName else resolvedName

    showName = fileInfo.get(
        "name",
        resolvedName,
    )

    return titleEmbed.buildShowTitle(
        showName,
        season,
        episode,
        title,
    )


def format_episode_ranges(
    episodes: list[int],
) -> str:
    episodes = sorted(episodes)

    if not episodes:
        return ""

    ranges: list[tuple[int, int]] = []

    start: int = episodes[0]
    end: int = episodes[0]

    for ep in episodes[1:]:
        if ep == end + 1:
            end = ep

        else:
            ranges.append((start, end))
            start = end = ep

    ranges.append((start, end))

    parts: list[str] = [str(s) if s == e else f"{s}-{e}" for s, e in ranges]

    return ", ".join(parts)


def format_ranges(
    numbers: list[int],
) -> str:
    numbers = sorted(numbers)

    if not numbers:
        return "None"

    ranges: list[tuple[int, int]] = []

    start: int = numbers[0]
    end: int = numbers[0]

    for n in numbers[1:]:
        if n == end + 1:
            end = n

        else:
            ranges.append((start, end))
            start = end = n

    ranges.append((start, end))

    parts: list[str] = [f"{s:02}" if s == e else f"{s:02}-{e:02}" for s, e in ranges]

    return ", ".join(parts)


def rename_show(
    file_info: dict[str, Any],
    args: RenameArgs,
) -> str | None:
    media_info = api.search_media(
        file_info["name"],
        "shows",
    )

    if not media_info:
        if args.verbose:
            print(f"  → [API Error] Could not find show '{file_info['name']}'")

        return None

    show_id = media_info["id"]

    episode_info = api.get_episode_by_number(
        show_id,
        file_info["season"],
        file_info["episode"],
    )

    if not episode_info:
        if args.verbose:
            print(
                f"  → [API Error] Could not find episode "
                f"S{file_info['season']:02}"
                f"E{file_info['episode']:02} "
                f"for '{media_info['name']}'"
            )

        return None

    format_str = args.format or "{name} S{season:02}E{episode:02} - {title}"

    try:
        return format_str.format(
            name=utils.clean_show_name(
                media_info["name"],
                args.char,
            ),
            season=file_info["season"],
            episode=file_info["episode"],
            title=utils.clean_show_name(
                episode_info["name"],
                args.char,
            ),
            year=(
                media_info.get(
                    "premiered",
                    "N/A",
                ).split("-")[0]
                if media_info.get("premiered")
                else "N/A"
            ),
        )

    except KeyError as e:
        print(f"[!] Unknown placeholder in --format: {e}")
        return None


def rename_movie(
    file_info: dict[str, Any],
    args: RenameArgs,
) -> str | None:
    media_info = resolve_movie_metadata(
        file_info["name"],
        file_info["year"],
        file_info["raw"],
        args,
    )

    if not media_info:
        if args.verbose:
            print(f"  → [API Error] Could not find movie '{file_info['name']}'")

        return None

    format_str = args.format or "{name} ({year})"

    try:
        return format_str.format(
            name=utils.clean_show_name(
                media_info["Title"],
                args.char,
            ),
            year=media_info.get(
                "Year",
                "N/A",
            ),
            director=media_info.get(
                "Director",
                "N/A",
            ).split(",")[0],
            genre=media_info.get(
                "Genre",
                "N/A",
            ).split(",")[0],
        )

    except KeyError as e:
        print(f"[!] Unknown placeholder in --format: {e}")
        return None


def list_detected_media(
    directory: str,
    extensions: list[str],
    is_movie: bool = False,
    args: RenameArgs | None = None,
) -> None:
    if is_movie and args is None:
        raise ValueError("args is required when is_movie=True")

    media: dict[str, dict[str, Any]] = {}

    for filename in os.listdir(directory):
        file_ext = os.path.splitext(filename)[1][1:]

        if file_ext.lower() not in [e.lower() for e in extensions]:
            continue

        rawStem = os.path.splitext(filename)[0]
        info = utils.parse_filename(
            rawStem,
            is_movie,
        )

        if not info:
            continue

        name = str(info["name"])

        if is_movie:
            if name not in media:
                assert args is not None

                year_raw = info.get("year")
                year = str(year_raw) if year_raw is not None else None

                media_info = resolve_movie_metadata(
                    name,
                    year,
                    rawStem,
                    args,
                )

                if media_info:
                    media[name] = {
                        "filename": filename,
                        "title": media_info.get(
                            "Title",
                            "N/A",
                        ),
                        "year": media_info.get(
                            "Year",
                            "N/A",
                        ),
                        "tagline": media_info.get(
                            "Tagline",
                            "N/A",
                        ),
                        "collection": media_info.get(
                            "Collection",
                            "N/A",
                        ),
                        "director": media_info.get(
                            "Director",
                            "N/A",
                        ),
                        "genre": media_info.get(
                            "Genre",
                            "N/A",
                        ),
                        "runtime": media_info.get(
                            "Runtime",
                            "N/A",
                        ),
                        "rated": media_info.get(
                            "Rated",
                            "N/A",
                        ),
                        "released": media_info.get(
                            "Released",
                            "N/A",
                        ),
                        "writer": media_info.get(
                            "Writer",
                            "N/A",
                        ),
                        "actors": media_info.get(
                            "Actors",
                            "N/A",
                        ),
                        "plot": media_info.get(
                            "Plot",
                            "N/A",
                        ),
                        "language": media_info.get(
                            "Language",
                            "N/A",
                        ),
                        "country": media_info.get(
                            "Country",
                            "N/A",
                        ),
                        "awards": media_info.get(
                            "Awards",
                            "N/A",
                        ),
                        "imdb_rating": media_info.get(
                            "imdbRating",
                            "N/A",
                        ),
                        "rotten_tomatoes": get_rating(
                            media_info,
                            "Rotten Tomatoes",
                        ),
                        "metacritic": get_rating(
                            media_info,
                            "Metacritic",
                        ),
                        "box_office": media_info.get(
                            "BoxOffice",
                            "N/A",
                        ),
                        "production": media_info.get(
                            "Production",
                            "N/A",
                        ),
                    }

        else:
            if name not in media:
                show_info = api.search_media(
                    name,
                    "shows",
                )

                all_episodes: list[dict[str, Any]] = []
                cast: list[dict[str, Any]] = []

                if show_info:
                    all_episodes = api.get_show_episodes(show_info["id"])

                    cast = api.get_show_cast(show_info["id"])

                media[name] = {
                    "show_info": show_info,
                    "all_episodes": all_episodes,
                    "cast": cast,
                    "seasons": {},
                }

            season = info["season"]
            episode = info["episode"]

            if season not in media[name]["seasons"]:
                media[name]["seasons"][season] = set()

            media[name]["seasons"][season].add(episode)

    for name, data in media.items():
        if is_movie:
            print(f"Movie Name: {data['title']}")
            print(f"Filename: {data['filename']}")

            _print_field("Year", data["year"])
            _print_field("Tagline", data["tagline"])
            _print_field("Director(s)", data["director"])
            _print_field("Genre(s)", data["genre"])
            _print_field("Runtime", data["runtime"])
            _print_field("Rated", data["rated"])
            _print_field("Released", data["released"])
            _print_field("Writer(s)", data["writer"])
            _print_field("Main Cast", data["actors"])

            wrapped_plot = textwrap.fill(
                data["plot"],
                width=80,
                subsequent_indent="      ",
            )

            print(f"Plot: {wrapped_plot}")

            _print_field("Language(s)", data["language"])
            _print_field("Country", data["country"])
            _print_field("Collection", data["collection"])
            _print_field("Awards", data["awards"])
            _print_field("IMDb Rating", data["imdb_rating"])
            _print_field(
                "Rotten Tomatoes",
                data["rotten_tomatoes"],
            )
            _print_field(
                "Metacritic",
                data["metacritic"],
            )
            _print_field(
                "Box Office",
                data["box_office"],
            )
            _print_field(
                "Production/Studio",
                data["production"],
            )

            print("---\n")

        else:
            show = data.get("show_info")

            if not show:
                print(f"[i] {name}")
                continue

            print(f"Show Name: {show.get('name', 'N/A')}")

            premiered = show.get("premiered")

            if premiered:
                print(f"Premiered: {premiered[:4]}")

            ended = show.get("ended")

            if ended:
                print(f"Ended: {ended[:4]}")

            print(f"Status: {show.get('status', 'N/A')}")

            print(f"Genres: {', '.join(show.get('genres', [])) or 'N/A'}")

            print(f"Language: {show.get('language', 'N/A')}")

            network = show.get("network")
            country = None

            if network:
                country = network.get("country", {}).get("name")

            if country:
                print(f"Country: {country}")

            runtime = show.get("runtime")

            if runtime:
                print(f"Runtime: {runtime} min")

            cast_names = [actor["person"]["name"] for actor in data.get("cast", [])[:5]]

            if cast_names:
                print(f"Main Cast: {', '.join(cast_names)}")

            rating = show.get("rating", {})

            if rating.get("average"):
                print(f"Rating: {rating['average']}")

            summary = show.get("summary")

            if summary:
                summary = re.sub(
                    r"<[^>]*>",
                    "",
                    summary,
                )

                wrapped_summary = textwrap.fill(
                    summary,
                    width=80,
                    subsequent_indent="         ",
                )

                print(f"Summary: {wrapped_summary}")

            official: dict[int, set[int]] = {}

            for ep in data["all_episodes"]:
                season = ep["season"]

                if season not in official:
                    official[season] = set()

                official[season].add(ep["number"])

            print(f"Total Seasons: {len(official)}")

            total_episode_count = sum(len(eps) for eps in official.values())

            print(f"Total Episodes: {total_episode_count}")

            print("\t")
            print("Local Collection Status:")

            present_seasons = set(data["seasons"].keys())

            official_seasons = set(official.keys())

            for season_num in sorted(present_seasons):
                owned = data["seasons"][season_num]
                total = official.get(
                    season_num,
                    set(),
                )

                owned_count = len(owned)
                total_count = len(total)

                if total_count and owned_count == total_count:
                    print(
                        f"[✓] Season {season_num:02}: "
                        f"{owned_count} / {total_count} "
                        "(Complete)"
                    )

                else:
                    print(
                        f"[!] Season {season_num:02}: "
                        f"{owned_count} / {total_count} "
                        "episodes"
                    )

                    if total:
                        missing = sorted(total - owned)

                        if missing:
                            available = sorted(owned)

                            print(
                                "    Available: "
                                f"Episodes "
                                f"{format_episode_ranges(available)}"
                            )

                            print(
                                "    Missing: "
                                f"Episodes "
                                f"{format_episode_ranges(missing)}"
                            )

            missing_seasons = sorted(official_seasons - present_seasons)

            print()

            if missing_seasons:
                print(f"Missing Seasons: {format_ranges(missing_seasons)}")

            else:
                print("Missing Seasons: None")

            present_episode_count = sum(
                len(season) for season in data["seasons"].values()
            )

            print()

            print("Collection Summary:")

            print(f"Seasons Present: {len(present_seasons)} / {len(official_seasons)}")

            print(f"Episodes Present: {present_episode_count} / {total_episode_count}")

            if present_episode_count == total_episode_count and len(
                present_seasons
            ) == len(official_seasons):
                print("Collection Complete")

            print("---\n")


def find_best_anime(
    query: str,
) -> dict[str, Any] | None:
    cache_key = query.casefold().strip()

    if cache_key in _anime_cache:
        return _anime_cache[cache_key]

    results = search_anime(query)

    query = query.casefold().strip()

    best = None
    best_score = -1

    for anime in results:
        if anime["type"].lower() != "tv":
            continue

        titles = anime["titles"]

        candidates = {
            anime["title"],
            titles.get("en"),
            titles.get("en_jp"),
            titles.get("en_us"),
        }

        candidates = {title.casefold().strip() for title in candidates if title}

        if query in candidates:
            score = 1000

        elif any(query in title or title in query for title in candidates):
            score = 600

        else:
            score = 0

        if score > best_score:
            best = anime
            best_score = score

    _anime_cache[cache_key] = best

    return best


def get_anime_metadata(filename: str) -> dict[str, Any] | None:
    file_info = parse_anime_filename(filename)

    anime = find_best_anime(file_info["title"])

    if not anime:
        return None

    episode = get_anime_episode(
        anime["id"],
        file_info["episode"],
    )

    if not episode:
        return None

    return {
        "title": anime["title"],
        "episode": episode["number"],
        "episode_title": episode["title"],
    }
