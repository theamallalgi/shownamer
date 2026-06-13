import os
import shutil
from pathlib import Path
from . import utils, api
from . import titleEmbed
import textwrap
import re


def process_directory(args):
    if args.name:
        list_detected_media(args.dir, args.ext, args.movie, args)
        return

    for filename in os.listdir(args.dir):
        file_ext = os.path.splitext(filename)[1][1:]
        if file_ext.lower() in [e.lower() for e in args.ext]:
            process_file(filename, args)


def get_rating(media_info, source):
    for rating in media_info.get("Ratings", []):
        if rating.get("Source") == source:
            return rating.get("Value", "N/A")
    return "N/A"


def process_file(filename, args):
    if args.format:
        try:
            utils.validate_format(args.format)
        except ValueError as e:
            print(f"[!] Error: {e}")
            return

    if args.verbose:
        print(f"Processing: {filename}")

    file_path = os.path.join(args.dir, filename)
    rawStem = os.path.splitext(filename)[0]
    file_info = utils.parse_filename(rawStem, args.movie)

    if not file_info:
        if args.verbose:
            print(f"[skip] Could not parse file information from '{filename}'")
        return

    file_info["raw"] = rawStem

    rename_succeeded = False
    new_name = ""
    if args.movie:
        new_name = rename_movie(file_info, args)
    else:
        if not file_info.get("is_movie"):
            new_name = rename_show(file_info, args)

    if new_name:
        file_ext = os.path.splitext(filename)[1]
        new_filename = new_name + file_ext
        new_filepath = os.path.join(args.dir, new_filename)

        if filename == new_filename:
            print(f"[skip] '{filename}' already matches the target name.")
        elif not args.dry_run:
            if os.path.exists(new_filepath):
                print(f"[skip] '{new_filename}' already exists.")
            else:
                try:
                    print(f"[rename] '{filename}' → '{new_filename}'")
                    shutil.move(file_path, new_filepath)
                    rename_succeeded = True
                except OSError as e:
                    print(f"  → [!] Error renaming file: {e}")
        else:
            print(f"[rename] '{filename}' → '{new_filename}'")

    if args.title:
        resolved_name = new_name if new_name else os.path.splitext(filename)[0]

        titleStr = _buildTitleStr(resolved_name, args, file_info)

        if args.dry_run:
            print(f"  → [title] Would embed: {titleStr}")
        else:
            target_path = Path(new_filepath) if rename_succeeded else Path(file_path)

            success = titleEmbed.embedTitle(target_path, titleStr)

            if args.verbose:
                if success:
                    print(f"  → [title] Embedded: {titleStr}")
                else:
                    print(
                        f"  → [title] Failed to embed metadata (ffmpeg/mutagen required)"
                    )
    elif args.verbose and not new_name:
        print(f"[skip] No new name generated for '{filename}'")


def _buildTitleStr(resolvedName: str, args, fileInfo: dict) -> str:
    if args.format:
        return resolvedName
    if args.movie:
        name, _, year = resolvedName.rpartition(" (")
        return titleEmbed.buildMovieTitle(name, year.rstrip(")"))
    season = fileInfo.get("season", 1)
    episode = fileInfo.get("episode", 1)
    title = resolvedName.split(" - ", 1)[-1] if " - " in resolvedName else resolvedName
    showName = fileInfo.get("name", resolvedName)
    return titleEmbed.buildShowTitle(showName, season, episode, title)


def format_episode_ranges(episodes):
    episodes = sorted(episodes)

    if not episodes:
        return ""

    ranges = []
    start = end = episodes[0]

    for ep in episodes[1:]:
        if ep == end + 1:
            end = ep
        else:
            ranges.append((start, end))
            start = end = ep

    ranges.append((start, end))

    parts = []

    for start, end in ranges:
        if start == end:
            parts.append(str(start))
        else:
            parts.append(f"{start}-{end}")

    return ", ".join(parts)


def format_ranges(numbers):
    numbers = sorted(numbers)

    if not numbers:
        return "None"

    ranges = []
    start = end = numbers[0]

    for n in numbers[1:]:
        if n == end + 1:
            end = n
        else:
            ranges.append((start, end))
            start = end = n

    ranges.append((start, end))

    parts = []

    for start, end in ranges:
        if start == end:
            parts.append(f"{start:02}")
        else:
            parts.append(f"{start:02}-{end:02}")

    return ", ".join(parts)


def rename_show(file_info, args):
    media_info = api.search_media(file_info["name"], "shows")
    if not media_info:
        if args.verbose:
            print(f"  → [API Error] Could not find show '{file_info['name']}'")
        return None

    show_id = media_info["id"]
    episode_info = api.get_episode_by_number(
        show_id, file_info["season"], file_info["episode"]
    )
    if not episode_info:
        if args.verbose:
            print(
                f"  → [API Error] Could not find episode S{file_info['season']:02}E{file_info['episode']:02} for '{media_info['name']}'"
            )
        return None

    format_str = args.format or "{name} S{season:02}E{episode:02} - {title}"

    try:
        return format_str.format(
            name=utils.clean_show_name(media_info["name"], args.char),
            season=file_info["season"],
            episode=file_info["episode"],
            title=utils.clean_show_name(episode_info["name"], args.char),
            year=media_info.get("premiered", "N/A").split("-")[0]
            if media_info.get("premiered")
            else "N/A",
        )
    except KeyError as e:
        print(f"[!] Unknown placeholder in --format: {e}")
        return None


def rename_movie(file_info, args):
    api_key = args.api_key or api.get_omdb_key()
    media_info = api.fetch_omdb_metadata(file_info["name"], file_info["year"], api_key)

    if not media_info:
        fallbackTitle, fallbackYear = utils.extractTitleFallback(file_info["raw"])
        if fallbackTitle:
            if args.verbose:
                print(f"  → [fallback] Retrying with extracted title: '{fallbackTitle}'")
            media_info = api.fetch_omdb_metadata(fallbackTitle, fallbackYear, api_key)

    if not media_info:
        if args.verbose:
            print(f"  → [API Error] Could not find movie '{file_info['name']}'")
        return None

    format_str = args.format or "{name} ({year})"

    try:
        return format_str.format(
            name=utils.clean_show_name(media_info["Title"], args.char),
            year=media_info.get("Year", "N/A"),
            director=media_info.get("Director", "N/A").split(",")[0],
            genre=media_info.get("Genre", "N/A").split(",")[0],
        )
    except KeyError as e:
        print(f"[!] Unknown placeholder in --format: {e}")
        return None


def list_detected_media(directory, extensions, is_movie=False, args=None):
    if is_movie and args is None:
        raise ValueError("args is required when is_movie=True")

    media = {}
    if is_movie:
        api_key = args.api_key or api.get_omdb_key()

    for filename in os.listdir(directory):
        file_ext = os.path.splitext(filename)[1][1:]
        if file_ext.lower() in [e.lower() for e in extensions]:
            rawStem = os.path.splitext(filename)[0]
            info = utils.parse_filename(rawStem, is_movie)
            if info:
                name = info["name"]
                if is_movie:
                    if name not in media:
                        media_info = api.fetch_omdb_metadata(
                            info["name"], info["year"], api_key
                        )
                        if not media_info:
                            fallbackTitle, fallbackYear = utils.extractTitleFallback(rawStem)
                            if fallbackTitle:
                                media_info = api.fetch_omdb_metadata(fallbackTitle, fallbackYear, api_key)
                        if media_info:
                            media[name] = {
                                "filename": filename,
                                "title": media_info.get("Title", "N/A"),
                                "year": media_info.get("Year", "N/A"),
                                "director": media_info.get("Director", "N/A"),
                                "genre": media_info.get("Genre", "N/A"),
                                "runtime": media_info.get("Runtime", "N/A"),
                                "rated": media_info.get("Rated", "N/A"),
                                "released": media_info.get("Released", "N/A"),
                                "writer": media_info.get("Writer", "N/A"),
                                "actors": media_info.get("Actors", "N/A"),
                                "plot": media_info.get("Plot", "N/A"),
                                "language": media_info.get("Language", "N/A"),
                                "country": media_info.get("Country", "N/A"),
                                "awards": media_info.get("Awards", "N/A"),
                                "imdb_rating": media_info.get("imdbRating", "N/A"),
                                "rotten_tomatoes": get_rating(
                                    media_info, "Rotten Tomatoes"
                                ),
                                "metacritic": get_rating(media_info, "Metacritic"),
                                "box_office": media_info.get("BoxOffice", "N/A"),
                                "production": media_info.get("Production", "N/A"),
                            }
                else:
                    if name not in media:
                        show_info = api.search_media(name, "shows")

                        all_episodes = []
                        cast = []

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
            print(f"Year: {data['year']}")
            print(f"Director(s): {data['director']}")
            print(f"Genre(s): {data['genre']}")
            print(f"Runtime: {data['runtime']}")
            print(f"Rated: {data['rated']}")
            print(f"Released: {data['released']}")
            print(f"Writer(s): {data['writer']}")
            print(f"Main Cast: {data['actors']}")
            wrapped_plot = textwrap.fill(
                data["plot"], width=80, subsequent_indent="      "
            )
            print(f"Plot: {wrapped_plot}")
            print(f"Language(s): {data['language']}")
            print(f"Country: {data['country']}")
            print(f"Awards: {data['awards']}")
            print(f"IMDb Rating: {data['imdb_rating']}")
            print(f"Rotten Tomatoes: {data['rotten_tomatoes']}")
            print(f"Metacritic: {data['metacritic']}")
            print(f"Box Office: {data['box_office']}")
            print(f"Production/Studio: {data['production']}")
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
                summary = re.sub(r"<[^>]*>", "", summary)
                wrapped_summary = textwrap.fill(
                    summary, width=80, subsequent_indent="         "
                )
                print(f"Summary: {wrapped_summary}")

            official = {}
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
                total = official.get(season_num, set())
                owned_count = len(owned)
                total_count = len(total)
                if total_count and owned_count == total_count:
                    print(
                        f"[✓] Season {season_num:02}: "
                        f"{owned_count} / {total_count} episodes (Complete)"
                    )
                else:
                    print(
                        f"[!] Season {season_num:02}: "
                        f"{owned_count} / {total_count} episodes"
                    )
                    if total:
                        missing = sorted(total - owned)
                        if missing:
                            available = sorted(owned)
                            print(
                                f"    Available: Episodes {format_episode_ranges(available)}"
                            )
                            print(
                                f"    Missing: Episodes {format_episode_ranges(missing)}"
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
