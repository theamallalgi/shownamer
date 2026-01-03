import argparse
import sys
from . import __version__

def main():
    """Main function for the shownamer CLI."""
    parser = argparse.ArgumentParser(
        description="A powerful yet lightweight command-line tool that automatically renames your TV show and movie files."
    )

    parser.add_argument(
        "--dir",
        type=str,
        default=".",
        help="Specifies the directory where your media files are located. Defaults to the current working directory.",
    )
    parser.add_argument(
        "-m", "--movie",
        action="store_true",
        help="Look for movie files instead of TV shows.",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Your OMDb API key. Overrides the stored API key.",
    )
    parser.add_argument(
        "--ext",
        nargs="+",
        default=["mkv", "mp4", "avi", "mov", "flv"],
        help="Specifies the file extensions to consider. Defaults to .mkv, .mp4, .avi, .mov, and .flv.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="See what changes will be made without actually renaming any files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show more details about what is happening behind the scenes.",
    )
    parser.add_argument(
        "--name",
        action="store_true",
        help="List all the TV show names detected in the directory. Use with --movie to list movie details.",
    )
    parser.add_argument(
        "--format",
        type=str,
        help="""Define your own custom filename format.
        For shows, available keys are: {name}, {season}, {episode}, {title}, {year}.
        Default: '{name} S{season:02}E{episode:02} - {title}'
        For movies, available keys are: {name}, {year}, {director}, {genre}.
        Default: '{name} ({year})'
        Example for a movie: '{director} - {name} ({year})' will result in 'Rahi Anil Barve - Tumbbad (2018).mkv'
        """,
    )
    parser.add_argument(
        "--char",
        type=str,
        default="",
        help="Replace illegal characters in filenames with a specific character. Available characters: _ - . and empty string.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Print the current version of Shownamer and exit.",
    )

    args = parser.parse_args()

    from .core import process_directory
    process_directory(args)


if __name__ == "__main__":
    main()
