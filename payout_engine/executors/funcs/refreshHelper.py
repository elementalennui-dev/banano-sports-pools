import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
import time
from fractions import Fraction

from sqlalchemy import create_engine, text
from config import POSTGRES_URL

class RefreshHelper():
    def __init__(self):
        # Initialize the database engine using the provided POSTGRES_URL
        self.engine = create_engine(POSTGRES_URL)

        # Default logo URL if a team's logo is not found
        self.default_logo = "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/default-team-logo-500.png"

    ############################################################
    ##################### Helper Functions #####################
    ############################################################

    # Calculate win percentage based on moneyline odds
    def moneylineWinPercent(self, ml):
        if ml > 0:
            return 100 / (ml + 100)  # Formula for positive moneyline odds
        else:
            ml = abs(ml)
            return ml / (ml + 100)   # Formula for negative moneyline odds

    # Convert fractional odds (e.g., "5/1") to moneyline format
    def fracToMoneyline(self, frac):
        frac = float(sum(Fraction(s) for s in frac.split()))  # Convert fractional odds to float
        # Convert to moneyline format
        frac = frac * 100 if frac >= 1 else -100 / frac
        return round(frac)

    # Add a 'weekday' column to the DataFrame based on a 'date' column
    def getWeekday(self, df):
        df["weekday"] = df["date"].apply(lambda x: x.weekday())  # Get weekday from 'date'

        # Map numeric weekday to corresponding weekday name
        weekday_map = {
            0: "Monday", 1: "Tuesday", 2: "Wednesday",
            3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"
        }
        df["weekday"] = df["weekday"].map(weekday_map)

        return df

    # Fetch and process game data from an external API within a given date range
    def getGameData(self, data, time_min=365, time_max=365):
        rows = []  # List to store rows of game data

        for game in data:
            # Fetch game-specific data
            game_response = requests.get(game["$ref"])
            game_info = game_response.json()

            # Convert game date to Eastern time zone and define date range
            game_date = pd.to_datetime(game_info["date"]).tz_convert('US/Eastern')
            now_min = datetime.now(pytz.timezone("US/Eastern")) - timedelta(days=time_min)
            now_max = datetime.now(pytz.timezone("US/Eastern")) + timedelta(days=time_max)

            # Skip games outside the date range
            if game_date < now_min or game_date > now_max:
                time.sleep(1)
                continue

            gamePk = game_info["id"]  # Unique game identifier
            print(gamePk)
            comp_links = game_info['competitions'][0]["competitors"]

            # Extract game type information
            type_txt = game_info['competitions'][0].get("type", {}).get("text", None)
            type_abbr = game_info['competitions'][0].get("type", {}).get("abbreviation", None)

            # Fetch and process home team data
            home_team = [x for x in comp_links if x["homeAway"] == "home"][0]
            home_team_url = home_team["team"]["$ref"]
            home_team_info = requests.get(home_team_url).json()

            team1_id = home_team_info["id"]
            team1 = home_team_info["abbreviation"]
            team1_name = home_team_info["displayName"]

            team1_logo = self.getTeamLogo(home_team_info)

            # Fetch home team score (if available)
            score1 = self.getTeamScore(home_team)

            # Fetch and process away team data
            away_team = [x for x in comp_links if x["homeAway"] == "away"][0]
            away_team_url = away_team["team"]["$ref"]
            away_team_info = requests.get(away_team_url).json()

            team2_id = away_team_info["id"]
            team2 = away_team_info["abbreviation"]
            team2_name = away_team_info["displayName"]

            team2_logo = self.getTeamLogo(away_team_info)

            # Fetch away team score (if available)
            score2 = self.getTeamScore(away_team)

            # Fetch and process game odds
            home_odds, away_odds, provider, details = self.getGameOdds(game_info)

            # Fetch game status (if available)
            status_id, status = self.getGameStatus(game_info)

            # Assemble row data for the current game
            row = {
                "date": game_info["date"], "gamepk": gamePk, "game_type": type_txt,
                "game_type_abbr": type_abbr, "team1": team1, "team2": team2,
                "team1_name": team1_name, "team2_name": team2_name, "team1_id": team1_id,
                "team2_id": team2_id, "team1_logo": team1_logo, "team2_logo": team2_logo,
                "odds_provider": provider, "odds_details": details, "team2_odds": away_odds,
                "team1_odds": home_odds, "score1": score1, "score2": score2,
                "status_id": status_id, "status": status
            }
            rows.append(row)

            # Pause between API requests to avoid hitting rate limits
            time.sleep(1)

        # Convert rows to a DataFrame
        df3 = pd.DataFrame(rows)

        if not df3.empty:
            # Calculate win percentages based on odds
            df3["team2_odds_wp"] = df3.team2_odds.apply(self.moneylineWinPercent)
            df3["team1_odds_wp"] = df3.team1_odds.apply(self.moneylineWinPercent)

            # Format odds as strings (positive or negative)
            df3["team2_odds"] = [f"+{x}" if x > 0 else f"{x}" for x in df3.team2_odds]
            df3["team1_odds"] = [f"+{x}" if x > 0 else f"{x}" for x in df3.team1_odds]

            # Convert datetime fields and generate game identifiers
            df3["date"] = pd.to_datetime(df3["date"]).dt.tz_convert('US/Eastern')
            df3['date_str'] = df3['date'].dt.strftime('%m/%d/%Y')
            df3["time"] = df3["date"].dt.strftime("%I:%M %p").str.strip("0")
            df3["game_id"] = df3.team2 + "_" + df3.team1 + "_" + df3.gamepk.astype(str)

        return df3

    # Helper function to fetch and return a team's logo URL
    def getTeamLogo(self, team_info):
        logos = team_info.get("logos", [])
        return logos[0].get("href", self.default_logo) if logos else self.default_logo

    # Helper function to fetch and return a team's score
    def getTeamScore(self, team_comp):
        try:
            score_url = team_comp["score"]["$ref"]
            score_response = requests.get(score_url).json()
            return score_response.get("value", 0)
        except:
            return 0

    # Helper function to fetch and return game odds
    def getGameOdds(self, game_info):
        odds_url = game_info['competitions'][0].get("odds", {}).get('$ref', "")
        if odds_url:
            try:
                odds_response = requests.get(odds_url).json()
                away_odds = odds_response["items"][0]["awayTeamOdds"].get("moneyLine", 100)
                home_odds = odds_response["items"][0]["homeTeamOdds"].get("moneyLine", 100)
                provider = odds_response["items"][0]["provider"].get("name", "")
                details = odds_response["items"][0].get("details", "")
            except:
                away_odds, home_odds, provider, details = 100, 100, "", ""
        else:
            away_odds, home_odds, provider, details = 100, 100, "", ""
        return home_odds, away_odds, provider, details

    # Helper function to fetch and return the game status
    def getGameStatus(self, game_info):
        status_url = game_info['competitions'][0].get("status", {}).get('$ref', "")
        if status_url:
            try:
                status_response = requests.get(status_url).json()
                status_id = int(status_response.get("type", {}).get("id", None))
                status = status_response.get("type", {}).get("name", None)
            except:
                status_id, status = None, None
        else:
            status_id, status = None, None
        return status_id, status

    # Write processed game data to the database
    def writeToDatabase(self, df, inp_table, gamepks):

        with self.engine.connect() as conn:

            # Delete existing rows for specific gamepks in the target table
            formatted_gamepks = ",".join(item.strip() for item in gamepks.split(','))
            query = f"DELETE FROM {inp_table} WHERE gamepk IN ({formatted_gamepks})"
            print(query)
            # Execute the query
            result = conn.execute(text(query))
            conn.commit()
            print(f"Deleted {result.rowcount} rows from {inp_table}")

            # Write the new data to the database
            df.to_sql(name=inp_table, con=self.engine, schema="public", index=False, if_exists="append", method="multi")
            print(f"Wrote {len(df)} rows to {inp_table}")
