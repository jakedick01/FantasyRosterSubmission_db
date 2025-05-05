import logging
import os
import requests
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("nfl_fetch_log.log"),
        logging.StreamHandler()
    ]
)

# Constants
CACHE_DIR = "rosters_cache"
URL = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLTeamRoster"
HEADERS = {
    "x-rapidapi-key": "9c9309abe7msh101dd7af4a69049p104574jsn77ffafbb2831",
    "x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
}

# Arrays for teams and corresponding team IDs
PLAYOFF_TEAMS = ["KC", "BUF", "BAL", "HOU", "LAC", "PIT", "DEN", "DET", "PHI", "TB", "LAR", "MIN", "WSH", "GB"]
ALL_TEAMS = ["MIA", "NE", "BUF", "NYJ", "PIT", "BAL", "CIN", "CLE", "HOU", "IND", "JAX", "TEN", "LAC", "KC", "LV", "DEN", "PHI", "DAL", "WSH", "NYG", "DET", "MIN", "CHI", "GB", "NO", "TB", "CAR", "ATL", "SF", "SEA", "LAR", "ARI"]
TEAM_IDS = ["20", "22", "4", "25", "26", "3", "7", "8", "13", "14", "15", "31", "18", "16", "17", "10", "27", "9", "32", "24", "11", "21", "6", "12", "23", "30", "5", "2", "28", "29", "19", "1"]

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Fetch data from API
def fetch_data(team_abv, team_id):
    QUERYSTRING = {"teamID": team_id, "teamAbv": team_abv}
    try:
        response = requests.get(URL, headers=HEADERS, params=QUERYSTRING)
        if response.status_code == 429:
            logging.error(f"Rate limit exceeded for {team_abv}.")
            return None
        response.raise_for_status()
        try:
            data = response.json()
            if "roster" in data.get("body", {}):
                # Save roster data to a file specific to the team
                cache_file = os.path.join(CACHE_DIR, f"rosters{team_abv}_cache.json")
                with open(cache_file, "w") as f:
                    json.dump(data, f)
                logging.info(f"Data cached for {team_abv}.")
                return data
            else:
                logging.error(f"'roster' key not found in response for {team_abv}.")
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON response for {team_abv}.")
    except requests.RequestException as e:
        logging.error(f"Request failed for {team_abv}: {e}")
    return None

# Process roster data
def process_roster_data(data, team_abv):
    if data:
        roster = data.get("body", {}).get("roster", [])
        logging.info(f"Total players for {team_abv}: {len(roster)}")
        for player in roster[:10]:  # Log only the first 10 players for readability
            logging.info(f"Name: {player.get('longName')}, Position: {player.get('pos')}, Team: {player.get('team')}")

# Fetch and process data for a specific list of teams
def get_team_data(team_list, team_ids):
    for team_abv, team_id in zip(team_list, team_ids):
        data = fetch_data(team_abv, team_id)
        process_roster_data(data, team_abv)

# Main
if __name__ == "__main__":
    logging.info("Fetching data for playoff teams...")
    # Dynamically match team IDs for playoff teams
    get_team_data(PLAYOFF_TEAMS, [TEAM_IDS[ALL_TEAMS.index(team)] for team in PLAYOFF_TEAMS])
    logging.info("Done fetching data for playoff teams.")