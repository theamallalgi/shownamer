import argparse
import sys
from . import __version__


class _Fmt(argparse.RawTextHelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=26, width=80)

    def _format_usage(self, usage, actions, groups, prefix):
        return (
            f"shownamer {__version__}\n"
            "Rename TV show and movie files using metadata from OMDb and TVmaze.\n"
            "\n"
            "Usage:\n"
            "  shownamer [options]\n"
            "\n"
        )

    def _format_action_invocation(self, action):
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar
        parts = list(action.option_strings)
        if action.nargs != 0:
            args_string = self._format_args(action, action.dest.upper())
            parts[-1] += " " + args_string
        return ", ".join(parts)

    def _format_actions_usage(self, actions, groups):
        return ""


def main():
    parser = argparse.ArgumentParser(
        prog="shownamer",
        add_help=False,
        formatter_class=_Fmt,
    )

    g = parser.add_argument_group("Options")

    g.add_argument(
        "--dir",
        metavar="<path>",
        default=".",
        help="Directory to scan. Default: current directory.",
    )
    g.add_argument(
        "-m",
        "--movie",
        action="store_true",
        help="Target movie files instead of TV shows.",
    )
    g.add_argument(
        "--api-key", metavar="<key>", help="OMDb API key. Overrides the stored key."
    )
    g.add_argument(
        "--ext",
        metavar="<ext>",
        nargs="+",
        default=["mkv", "mp4", "avi", "mov", "flv"],
        help="File extensions to scan. Default: mkv mp4 avi mov flv.",
    )
    g.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without renaming any files.",
    )
    g.add_argument(
        "--verbose", action="store_true", help="Show detailed output during processing."
    )
    g.add_argument(
        "--name",
        action="store_true",
        help="List detected show or movie names in the directory.",
    )
    g.add_argument(
        "--format",
        metavar="<fmt>",
        help=(
            "Custom filename format string.\n"
            "  Show keys:     {name} {season} {episode} {title} {year}\n"
            "  Movie keys:    {name} {year} {director} {genre}\n"
            "  Show default:  {name} S{season:02}E{episode:02} - {title}\n"
            "  Movie default: {name} ({year})"
        ),
    )
    g.add_argument(
        "--char",
        metavar="<char>",
        default="",
        help="Replace illegal filename characters. Accepts: _ - . or empty.",
    )
    g.add_argument(
        "--title",
        action="store_true",
        help=(
            "Embed media title into file metadata after renaming.\n"
            "  Show: S02xE12 - Title  |  Movie: Name (Year)\n"
            "  Compatible with --format and --movie."
        ),
    )
    g.add_argument("-h", "--help", action="help", help="Print this help message.")
    g.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Print version and exit.",
    )

    args = parser.parse_args()

    from .core import process_directory

    process_directory(args)


if __name__ == "__main__":
    main()
