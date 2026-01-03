![Intro](https://github.com/theamallalgi/shownamer/blob/main/docs/assets/header.png?raw=true)

# Shownamer - The Ultimate Media Renamer

Shownamer is a powerful yet lightweight command-line tool written in Python that automatically renames your TV show and movie files. It fetches accurate episode titles, release years, and other metadata from online sources like TVmaze and OMDb, transforming your messy filenames into a clean, consistent, and organized format.

> [!NOTE]
> Fetches details and metadata from [TVmaze](https://www.tvmaze.com/) and [OMDb API](https://www.omdbapi.com/).
> No API Keys of further tweaking will be required to rename and handle TV Show files.
> But, OMDb Will ask the user for an API Key when trying to use shownamer with movie files.

## The Philosophy

The philosophy behind Shownamer is simplicity. It's designed to work "out of the box" with minimal configuration. While movie renaming requires a free API key from OMDb, the tool is designed to be as straightforward as possible. It does one thing and does it well: renaming your media files to make your collection look neat and tidy.

## Installation

Installing Shownamer is as simple as running a single command. All you need is Python 3.6 or higher.

```bash
pip install shownamer
```

That's it! You're ready to start renaming your files.

## Usage

You can use Shownamer by simply typing `shownamer` in your terminal. By default, it will scan the current directory for TV show files and rename them.

To see a list of all available options, you can use the `--help` flag:

```bash
shownamer --help
```

### Arguments

| Flag            | Description                                                                                            |
| :-------------- | :----------------------------------------------------------------------------------------------------- |
| `--dir`         | Specifies the directory where your media files are located. Defaults to the current working directory. |
| `-m`, `--movie` | Look for movie files instead of TV shows.                                                              |
| `--api-key`     | Your OMDb API key. Overrides the stored API key. (only required for renaming movie files)              |
| `--ext`         | Specifies the file extensions to consider. Defaults to `mkv`, `mp4`, `avi`, `mov`, `flv`.              |
| `--dry-run`     | See what changes will be made without actually renaming any files.                                     |
| `--verbose`     | Show more details about what is happening behind the scenes.                                           |
| `--name`        | List all the TV show names detected in the directory. Use with `--movie` to list movie details.        |
| `--format`      | Define your own custom filename format.                                                                |
| `--char`        | Replace illegal characters in filenames with a specific character (`_`, `-`, `.`).                     |
| `--version`     | Print the current version of Shownamer and exit.                                                       |

### Examples

**Rename TV Show Episodes**

```bash
# Rename all supported video files in the current directory
shownamer

# Specify a directory
shownamer --dir "/path/to/your/shows"

# Only consider .mkv and .mp4 files
shownamer --ext mkv mp4
```

**Rename Movie Files**

The first time you run the movie command, you will be prompted for a free OMDb API key.
This key will be stored safety until the key is replaced by a new one.
Get your API Key here https://www.omdbapi.com/apikey.aspx

```bash
# Rename movie files in the current directory
shownamer --movie

# Provide an API key directly
shownamer --movie --api-key YOUR_API_KEY
```

**Dry Run and Verbose Mode**

```bash
# Preview the changes without actually renaming any files
shownamer --dry-run

# See detailed logs of what the tool is doing
shownamer --verbose
```

**List Detected Media**

```bash
# List all detected TV shows in the current directory
shownamer --name

# List all detected movies
shownamer --name --movie
```

### Custom Filename Formatting

You can use the `--format` argument to define your own filename structure.

**Available Placeholders:**

*   **For TV Shows:** `{name}`, `{season}`, `{episode}`, `{title}`, `{year}`
*   **For Movies:** `{name}`, `{year}`, `{director}`, `{genre}`

**Formatting Examples:**

```bash
# Default TV show format: {name} S{season:02}E{episode:02} - {title}
# Output: The Office S01E01 - Pilot.mkv

# Custom TV show format
shownamer --format "{name} ({year}) - {season}x{episode} - {title}"

# Default movie format: {name} ({year})
# Output: The Green Knight (2021).mkv

# Custom movie format
shownamer --movie --format "{director} - {name} ({year}) [{genre}]"
```

## FAQ

### Will this overwrite existing files?

No. The script does not overwrite files. It renames only when the target filename does not exist. You can use `--dry-run` to preview the result first.

### Does it fetch subtitles or cover images?

No. This tool only renames the video files with accurate episode titles.

## Contributions

Pull requests, suggestions, and issues are welcome! Let's make it smarter and broader (e.g., subtitle renaming, fuzzy matching, show aliases, etc.).
