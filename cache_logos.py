import os
import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("nfl_logos_fetch_log.log"),
        logging.StreamHandler()
    ]
)

# Constants
CACHE_DIR = "static/logos_cache"
URL = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLTeams"
HEADERS = {
    "x-rapidapi-key": "9c9309abe7msh101dd7af4a69049p104574jsn77ffafbb2831",
    "x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
}

# Playoff teams (team abbreviations)
PLAYOFF_TEAMS = ["KC", "BUF", "BAL", "HOU", "LAC", "PIT", "DEN", "DET", "PHI", "TB", "LAR", "MIN", "WSH", "GB"]

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Fetch data from the API
def fetch_logo_data():
    querystring = {"rosters": "false", "schedules": "false"}
    try:
        response = requests.get(URL, headers=HEADERS, params=querystring)
        if response.status_code == 429:
            logging.error("Rate limit exceeded.")
            return None
        response.raise_for_status()
        try:
            data = response.json()
            return data
        except json.JSONDecodeError:
            logging.error("Invalid JSON response.")
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
    return None

# Save logos for playoff teams
def save_logos_for_playoff_teams(data):
    if data:
        # Loop through teams and check if they're in the PLAYOFF_TEAMS list
        for team in data.get('body', []):
            team_abv = team.get('teamAbv')
            espn_logo_url = team.get('espnLogo1')

            if team_abv in PLAYOFF_TEAMS and espn_logo_url:
                try:
                    # Download and save the logo image
                    logo_response = requests.get(espn_logo_url, stream=True)
                    if logo_response.status_code == 200:
                        logo_path = os.path.join(CACHE_DIR, f"{team_abv}_logo.png")
                        with open(logo_path, 'wb') as f:
                            for chunk in logo_response.iter_content(1024):
                                f.write(chunk)
                        logging.info(f"Logo saved for {team_abv}.")
                    else:
                        logging.error(f"Failed to download logo for {team_abv}.")
                except requests.RequestException as e:
                    logging.error(f"Error downloading logo for {team_abv}: {e}")

# Main
if __name__ == "__main__":
    logging.info("Fetching logo data for playoff teams...")
    data = fetch_logo_data()
    if data:
        save_logos_for_playoff_teams(data)
    logging.info("Done fetching and saving logos for playoff teams.")