import re

COMMON_TAGS = [
    "1080p", "720p", "2160p", "x264", "x265", "bluray", "brrip",
    "webrip", "hdrip", "dvdrip", "web-dl", "hdtv", "unrated", "extended",
    "proper", "limited"
]

def clean_filename_movie(filename):
    name = re.sub(r"[._\-]+", " ", filename)
    name = re.sub(r"\s+", " ", name).strip()
    for tag in COMMON_TAGS:
        name = re.sub(rf"\b{tag}\b", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip()
    name = " ".join(word.capitalize() for word in name.split())
    return name

def extract_title_and_year(filename):
    name = clean_filename_movie(filename)
    years = re.findall(r"(19\d{2}|20\d{2})", name)
    year = min(years) if years else None
    if year:
        name = name.split(year)[0].strip()
    return name, year

def parse_filename(filename, is_movie=False):
    """
    Parses a filename to extract show name, season, and episode number, or movie title and year.
    Returns a dictionary with the parsed information.
    """
    if is_movie:
        title, year = extract_title_and_year(filename)
        return {"name": title, "year": year, "is_movie": True}

    # Regex to capture different patterns like S01E01, 1x01, etc.
    patterns = [
        re.compile(r"^(.*?)(?:S(\d{1,2})E(\d{1,2}))", re.IGNORECASE),
        re.compile(r"^(.*?)(?:(\d{1,2})x(\d{1,2}))", re.IGNORECASE),
        re.compile(r"^(.*?)(?:E(\d{1,2}))", re.IGNORECASE), # For formats like 'TheOffice_E05.avi'
    ]

    for pattern in patterns:
        match = pattern.match(filename)
        if match:
            name = match.group(1).replace(".", " ").replace("_", " ").strip()
            
            if len(match.groups()) == 3: # Matched SXXEXX or XxXX
                season = int(match.group(2))
                episode = int(match.group(3))
            else: # Matched EXX
                season = 1 # Default to season 1
                episode = int(match.group(2))
            
            return {"name": name, "season": season, "episode": episode, "is_movie": False}

    return None

def clean_show_name(name, subst_char="_"):
    """
    Removes illegal characters from a filename.
    """
    illegal_chars = r'[\\/:"*?<>|]'
    return re.sub(illegal_chars, subst_char, name)

def validate_format(format_str):
    """
    Validates the format string for illegal characters.
    """
    illegal_chars = r'[\\/:"*?<>|]'
    if re.search(illegal_chars, format_str):
        raise ValueError(f"Illegal character found in format string: {format_str}")
