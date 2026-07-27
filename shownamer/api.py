# api.py - api stuff mostly (tvmaze, omdb, tmdb)

import requests
from pathlib import Path
from typing import Any

BASE_URL = "http://api.tvmaze.com"

OMDB_KEY_FILE = Path.home() / ".shownamer_omdb_key"
OMDB_URL = "http://www.omdbapi.com/"

TMDB_KEY_FILE = Path.home() / ".shownamer_tmdb_key"
TMDB_URL = "https://api.themoviedb.org/3"

_tmdb_key_cache: dict[str, bool | str | None] = {"checked": False, "key": None}
_omdb_key_cache: dict[str, bool | str | None] = {"checked": False, "key": None}


def get_omdb_key() -> str | None:
    if OMDB_KEY_FILE.exists():
        return OMDB_KEY_FILE.read_text().strip()
    if _omdb_key_cache["checked"]:
        return _omdb_key_cache["key"]  # type: ignore[return-value]

    print("OMDb is used as a fallback movie source when TMDb has no key or no match.")
    print("Get a free OMDb API key from http://www.omdbapi.com/apikey.aspx")
    key = input("Add OMDb key (n or empty to skip): ").strip()

    _omdb_key_cache["checked"] = True
    if not key or key.lower() == "n":
        return None

    OMDB_KEY_FILE.write_text(key)
    _omdb_key_cache["key"] = key
    return key


def get_stored_omdb_key() -> str | None:
    if OMDB_KEY_FILE.exists():
        key = OMDB_KEY_FILE.read_text().strip()
        return key or None
    return None


def get_tmdb_key():
    if TMDB_KEY_FILE.exists():
        return TMDB_KEY_FILE.read_text().strip()
    if _tmdb_key_cache["checked"]:
        return _tmdb_key_cache["key"]  # type: ignore[return-value]

    print("TMDb pulls richer movie metadata (tagline, studio, cast) than OMDb.")
    print( "Get a free TMDb API key (v3 auth) from https://www.themoviedb.org/settings/api")
    key = input("Add TMDb key (n or empty to skip): ").strip()

    _tmdb_key_cache["checked"] = True
    if not key or key.lower() == "n":
        return None

    TMDB_KEY_FILE.write_text(key)
    _tmdb_key_cache["key"] = key
    return key


def fetch_omdb_metadata(
    title: str, year: str | None = None, api_key: str | None = None
) -> dict[str, Any] | None:
    params: dict[str, str | None] = {"t": title, "apikey": api_key, "type": "movie"}
    if year:
        params["y"] = year
    try:
        r = requests.get(OMDB_URL, params=params, timeout=8)
        data = r.json()
        if data.get("Response") == "True":
            data["Source"] = "omdb"
            return data
    except Exception:
        pass
    return None


def fetch_omdb_metadata_by_imdb_id(
    imdb_id: str, api_key: str | None = None
) -> dict[str, Any] | None:
    params: dict[str, str | None] = {"i": imdb_id, "apikey": api_key}
    try:
        r = requests.get(OMDB_URL, params=params, timeout=8)
        data = r.json()
        if data.get("Response") == "True":
            return data
    except Exception:
        pass
    return None


def _tmdb_names(items: list[dict[str, Any]]) -> str:
    return ", ".join(item.get("name", "") for item in items if item.get("name"))


def _tmdb_certification(
    release_dates: dict[str, Any] | None, country: str = "US"
) -> str | None:
    if not release_dates:
        return None
    results = release_dates.get("results", [])
    for entry in results:
        if entry.get("iso_3166_1") == country:
            for rd in entry.get("release_dates", []):
                cert = rd.get("certification")
                if cert:
                    return cert
    for entry in results:
        for rd in entry.get("release_dates", []):
            cert = rd.get("certification")
            if cert:
                return cert
    return None


def _format_currency(amount: int | None) -> str | None:
    if not amount:
        return None
    return f"${amount:,}"


def fetch_tmdb_metadata(
    title: str,
    year: str | None = None,
    api_key: str | None = None,
    omdb_api_key: str | None = None,
) -> dict[str, Any] | None:
    # INFO: search tmdb for a movie and return metadata (normalized) to the same keys `fetch_omdb_metadata()` returns.
    # INFO: also returns the tagline, collection keys (not available from omdb)
    # INFO: also does hybrid enrichment pass against omdb (awards, scores)
    search_params: dict[str, str | None] = {"query": title, "api_key": api_key}
    if year:
        search_params["year"] = year

    try:
        r = requests.get(f"{TMDB_URL}/search/movie", params=search_params, timeout=8)
        results: list[dict[str, Any]] = r.json().get("results") or []
        if not results:
            return None
        movie_id = results[0]["id"]

        details_r = requests.get(
            f"{TMDB_URL}/movie/{movie_id}",
            params={
                "api_key": api_key,
                "append_to_response": "credits,release_dates,external_ids",
            },
            timeout=8,
        )
        details = details_r.json()
        if not details.get("id"):
            return None
    except Exception:
        return None

    credits = details.get("credits", {})
    crew = credits.get("crew", [])
    cast = credits.get("cast", [])

    director = next((c["name"] for c in crew if c.get("job") == "Director"), "N/A")
    writer = next(
        (c["name"] for c in crew if c.get("job") in ("Writer", "Screenplay")), "N/A"
    )
    actors = ", ".join(c["name"] for c in cast[:3]) or "N/A"
    release_date = details.get("release_date") or ""

    collection = details.get("belongs_to_collection")
    # imdb_id = (details.get("external_ids") or {}).get("imdb_id")
    external_ids: dict[str, Any] = details.get("external_ids") or {}
    imdb_id = external_ids.get("imdb_id")

    metadata: dict[str, Any] = {
        "Source": "tmdb",
        "Title": details.get("title") or title,
        "Year": release_date[:4] if release_date else "N/A",
        "Tagline": details.get("tagline") or "N/A",
        "Director": director,
        "Genre": _tmdb_names(details.get("genres", [])) or "N/A",
        "Runtime": f"{details['runtime']} min" if details.get("runtime") else "N/A",
        "Rated": _tmdb_certification(details.get("release_dates")) or "N/A",
        "Released": release_date or "N/A",
        "Writer": writer,
        "Actors": actors,
        "Plot": details.get("overview") or "N/A",
        "Language": details.get("original_language", "N/A"),
        "Country": _tmdb_names(details.get("production_countries", [])) or "N/A",
        "Awards": "N/A",
        "imdbRating": str(details.get("vote_average", "N/A")),
        "Ratings": [],
        "BoxOffice": _format_currency(details.get("revenue")) or "N/A",
        "Production": _tmdb_names(details.get("production_companies", [])) or "N/A",
        "Collection": collection.get("name") if collection else "N/A",
    }

    if imdb_id and omdb_api_key:
        enrichment = fetch_omdb_metadata_by_imdb_id(imdb_id, omdb_api_key)
        if enrichment:
            metadata["Ratings"] = enrichment.get("Ratings", [])
            metadata["Awards"] = enrichment.get("Awards", "N/A")
            if metadata["BoxOffice"] == "N/A":
                metadata["BoxOffice"] = enrichment.get("BoxOffice", "N/A")
            if metadata["Rated"] == "N/A":
                metadata["Rated"] = enrichment.get("Rated", "N/A")

    return metadata


def search_media(name: str, media_type: str = "shows") -> dict[str, Any] | None:
    endpoint = f"search/{media_type}"
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params={"q": name})
        response.raise_for_status()
        results = response.json()
        if results:
            return results[0]["show"]
    except requests.exceptions.RequestException as e:
        print(f"[!] Error searching for {name}: {e}")
    return None


def get_episode_by_number(show_id: str, season: int, episode: int):
    try:
        response = requests.get(
            f"{BASE_URL}/shows/{show_id}/episodebynumber",
            params={"season": season, "number": episode},
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[!] Error getting episode S{season:02}E{episode:02}: {e}")
    return None


def get_show_episodes(show_id: str) -> list[dict[str, Any]]:
    try:
        response = requests.get(f"{BASE_URL}/shows/{show_id}/episodes")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[!] Error getting episode list for show {show_id}: {e}")
    return []


def get_show_cast(show_id: str) -> list[dict[str, Any]]:
    try:
        response = requests.get(f"{BASE_URL}/shows/{show_id}/cast")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[!] Error getting cast for show {show_id}: {e}")
    return []
