import requests
from pathlib import Path

BASE_URL = "http://api.tvmaze.com"
OMDB_KEY_FILE = Path.home() / ".shownamer_omdb_key"
OMDB_URL = "http://www.omdbapi.com/"

def get_omdb_key():
    """Check local storage, else prompt user"""
    if OMDB_KEY_FILE.exists():
        return OMDB_KEY_FILE.read_text().strip()
    print("To use the movie renaming feature, you need an OMDb API key.")
    print("You can get one for free from http://www.omdbapi.com/apikey.aspx")
    key = input("Enter your OMDb API key: ").strip()
    OMDB_KEY_FILE.write_text(key)
    return key

def fetch_omdb_metadata(title, year=None, api_key=None):
    params = {"t": title, "apikey": api_key, "type": "movie"}
    if year:
        params["y"] = year

    try:
        r = requests.get(OMDB_URL, params=params, timeout=8)
        data = r.json()
        if data.get("Response") == "True":
            return data
    except Exception:
        pass
    return None

def search_media(name, media_type="shows"):
    """
    Searches for a show or movie by name.
    """
    endpoint = "search/shows"
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params={"q": name})
        response.raise_for_status()
        results = response.json()
        if results:
            return results[0]["show"] # Return the first result
    except requests.exceptions.RequestException as e:
        print(f"[!] Error searching for {name}: {e}")
    return None

def get_episode_by_number(show_id, season, episode):
    """
    Gets a specific episode by season and episode number.
    """
    try:
        response = requests.get(f"{BASE_URL}/shows/{show_id}/episodebynumber", params={"season": season, "number": episode})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[!] Error getting episode S{season:02}E{episode:02}: {e}")
    return None
