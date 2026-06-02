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

Installing Shownamer is as simple as running a single command. All you need is Python 3.7 or higher.

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

| Flag              | Description                                                                                            |
| :---------------- | :----------------------------------------------------------------------------------------------------- |
| `--dir`           | Specifies the directory where your media files are located. Defaults to the current working directory. |
| `-m`, `--movie`   | Look for movie files instead of TV shows.                                                              |
| `--api-key`       | Your OMDb API key. Overrides the stored API key. (only required for renaming movie files)              |
| `--ext`           | Specifies the file extensions to consider. Defaults to `mkv`, `mp4`, `avi`, `mov`, `flv`.              |
| `--dry-run`       | See what changes will be made without actually renaming any files.                                     |
| `--verbose`       | Show more details about what is happening behind the scenes.                                           |
| `--name`          | List all the TV show names detected in the directory. Use with `--movie` to list movie details.        |
| `--format`        | Define your own custom filename format.                                                                |
| `--char`          | Replace illegal characters in filenames with a specific character (`_`, `-`, `.`).                     |
| `--title`         | Embed media title into file metadata after renaming. Compatible with `--format` and `--movie`.         |
| `-h`, `--help`    | Print this help message.                                                                               |
| `-v`, `--version` | Print the current version of Shownamer and exit.                                                       |

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
shownamer -m --name
```

For TV shows, it prints: Show Name, Premiered, Ended, Status, Genres, Language, Country, Runtime, Main Cast, Rating, Summary, Total Seasons, Total Episodes, Local Collection Status (per season, with available/missing episode breakdown), Missing Seasons, and a Collection Summary.

```
user@device: shownamer --name
Show Name: Raising Hope
Premiered: 2010
Ended: 2014
Status: Ended
Genres: Comedy, Family
Language: English
Country: United States
Runtime: 30 min
Main Cast: Lucas Neff, Martha Plimpton, Garret Dillahunt, Shannon Woodward, Cloris Leachman
Rating: 7.9
Summary: At 23 years old, Jimmy Chance is going nowhere in life. He skims pools for a
         living, parties every night and still lives at home with his family,
         including his parents and his cousin, Mike. Jimmy's life takes a
         drastic turn when a chance romantic encounter with Lucy goes awry once
         he discovers she is a wanted felon. Months later, when Jimmy pays a
         visit to the local prison, he discovers Lucy gave birth to their baby,
         who he is now charged with raising.
Total Seasons: 4
Total Episodes: 88
	
Local Collection Status:
[!] Season 04: 15 / 22 episodes
    Available: Episodes 8-22
    Missing: Episodes 1-7

Missing Seasons: 01-03

Collection Summary:
Seasons Present: 1 / 4
Episodes Present: 15 / 88
---
```

For movies, it prints: Movie Name, Filename, Year, Director(s), Genre(s), Runtime, Rated, Released, Writer(s), Main Cast, Plot, Language(s), Country, Awards, IMDb Rating, Rotten Tomatoes, Metacritic, Box Office.

```
user@device: shownamer --movie --name
Movie Name: The Secret Life of Walter Mitty
Filename: the.secret.life.of.walter.mitty.720p.mkv
Year: 2013
Director(s): Ben Stiller
Genre(s): Adventure, Comedy, Drama
Runtime: 114 min
Rated: PG
Released: 25 Dec 2013
Writer(s): Steve Conrad, James Thurber
Main Cast: Ben Stiller, Kristen Wiig, Jon Daly
Plot: When both he and a colleague are about to lose their job, Walter takes action by
      embarking on an adventure more extraordinary than anything he ever
      imagined.
Language(s): English, Spanish, Icelandic
Country: United States, United Kingdom
Awards: 5 wins & 18 nominations total
IMDb Rating: 7.3
Rotten Tomatoes: 52%
Metacritic: 54/100
Box Office: $58,236,838
---
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

### Title Embedding

Use the `--title` flag to write a title string directly into the file's metadata after renaming.

```bash
# Embed title metadata after renaming TV show files
shownamer --title

# Embed title metadata after renaming movie files
shownamer --movie --title

# Works alongside --format
shownamer --title --format "{name} ({year}) - {season}x{episode} - {title}"

# Preview what would be embedded without touching files
shownamer --title --dry-run
```

The title string embedded into the metadata follows this format:

| Mode   | Embedded Title Format                  | Example                        |
| :----- | :------------------------------------- | :----------------------------- |
| Show   | `S{season:02}xE{episode:02} - {title}` | `S02xE05 - The Dinner Party`   |
| Movie  | `{name} ({year})`                      | `The Green Knight (2021)`      |

When `--format` is used, the formatted filename string is embedded as-is instead of the defaults above.

**Dependencies:**

For `.mp4`, `.m4v`, and `.mov` files, title embedding uses `mutagen`, which is installed automatically with shownamer. For all other formats (`.mkv`, `.avi`, etc.), it falls back to `ffmpeg`, which must be available in your `PATH` separately.

## FAQ

### Will this overwrite existing files?

No. The script does not overwrite files. It renames only when the target filename does not exist. You can use `--dry-run` to preview the result first.

### Does it fetch subtitles or cover images?

No. This tool only renames the video files with accurate episode titles.

## Contributions

Pull requests, suggestions, and issues are welcome! Let's make it smarter and broader (e.g., subtitle renaming, fuzzy matching, show aliases, etc.).
