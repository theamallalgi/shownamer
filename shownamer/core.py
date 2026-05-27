import os
import shutil
from pathlib import Path
from . import utils, api
from . import titleEmbed


def process_directory(args):
    if args.name:
        list_detected_media(args.dir, args.ext, args.movie, args)
        return

    for filename in os.listdir(args.dir):
        file_ext = os.path.splitext(filename)[1][1:]
        if file_ext.lower() in [e.lower() for e in args.ext]:
            process_file(filename, args)


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
    file_info = utils.parse_filename(os.path.splitext(filename)[0], args.movie)

    if not file_info:
        if args.verbose:
            print(f"[skip] Could not parse file information from '{filename}'")
        return

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

        print(f"[rename] '{filename}' → '{new_filename}'")

        if not args.dry_run:
            if os.path.exists(new_filepath):
                print(f"[skip] '{new_filename}' already exists.")
            else:
                try:
                    shutil.move(file_path, new_filepath)
                    if args.title:
                        titleStr = _buildTitleStr(new_name, args, file_info)
                        success = titleEmbed.embedTitle(Path(new_filepath), titleStr)
                        if args.verbose:
                            if success:
                                print(f"  → [title] Embedded: {titleStr}")
                            else:
                                print(f"  → [title] Failed to embed metadata (ffmpeg/mutagen required)")
                except OSError as e:
                    print(f"  → [!] Error renaming file: {e}")
        else:
            if args.title:
                titleStr = _buildTitleStr(new_name, args, file_info)
                print(f"  → [title] Would embed: {titleStr}")
    elif args.verbose:
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


def rename_show(file_info, args):
    media_info = api.search_media(file_info["name"], "shows")
    if not media_info:
        if args.verbose:
            print(f"  → [API Error] Could not find show '{file_info['name']}'")
        return None

    show_id = media_info["id"]
    episode_info = api.get_episode_by_number(show_id, file_info["season"], file_info["episode"])
    if not episode_info:
        if args.verbose:
            print(f"  → [API Error] Could not find episode S{file_info['season']:02}E{file_info['episode']:02} for '{media_info['name']}'")
        return None

    format_str = args.format or "{name} S{season:02}E{episode:02} - {title}"

    try:
        return format_str.format(
            name=utils.clean_show_name(media_info["name"], args.char),
            season=file_info["season"],
            episode=file_info["episode"],
            title=utils.clean_show_name(episode_info["name"], args.char),
            year=media_info.get("premiered", "N/A").split("-")[0] if media_info.get("premiered") else "N/A",
        )
    except KeyError as e:
        print(f"[!] Unknown placeholder in --format: {e}")
        return None


def rename_movie(file_info, args):
    api_key = args.api_key or api.get_omdb_key()
    media_info = api.fetch_omdb_metadata(file_info["name"], file_info["year"], api_key)

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
            info = utils.parse_filename(os.path.splitext(filename)[0], is_movie)
            if info:
                name = info["name"]
                if is_movie:
                    if name not in media:
                        media_info = api.fetch_omdb_metadata(info["name"], info["year"], api_key)
                        if media_info:
                            media[name] = {
                                "filename": filename,
                                "year": media_info.get("Year", "N/A"),
                                "director": media_info.get("Director", "N/A"),
                                "genre": media_info.get("Genre", "N/A"),
                            }
                else:
                    if name not in media:
                        media[name] = {"seasons": set(), "episodes": 0}
                    media[name]["seasons"].add(info["season"])
                    media[name]["episodes"] += 1

    for name, data in media.items():
        if is_movie:
            print(f"Movie Name: {name}")
            print(f"Filename: {data['filename']}")
            print(f"Year of Release: {data['year']}")
            print(f"Director: {data['director']}")
            print(f"Genre: {data['genre']}")
            print("---\n")
        else:
            print(f"[i] {name}: {len(data['seasons'])} season(s), {data['episodes']} episode(s)")
