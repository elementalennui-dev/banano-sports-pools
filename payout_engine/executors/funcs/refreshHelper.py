import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
import time
from fractions import Fraction

from sqlalchemy import create_engine
from config import POSTGRES_URL

class RefreshHelper():
    def __init__(self):
        self.engine = create_engine(POSTGRES_URL)
        self.default_logo = "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/default-team-logo-500.png"

    ############################################################
    ##################### Helper Functions #####################
    ############################################################
    def moneylineWinPercent(self, ml):
        if (ml > 0):
            return (100 / (ml + 100))
        else:
            ml = abs(ml)
            return (ml / (ml + 100))

    def fracToMoneyline(self, frac):
        frac = float(sum(Fraction(s) for s in frac.split()))
        frac = frac * 100 if frac >= 1 else -100 / frac
        frac = round(frac)
        return(frac)

    # df has to have a datetime col called date
    def getWeekday(self, df):
        df["weekday"] = df["date"].apply(lambda x: x.weekday())

        # map weekday
        df.loc[df.weekday == 0, "weekday"] = "Monday"
        df.loc[df.weekday == 1, "weekday"] = "Tuesday"
        df.loc[df.weekday == 2, "weekday"] = "Wednesday"
        df.loc[df.weekday == 3, "weekday"] = "Thursday"
        df.loc[df.weekday == 4, "weekday"] = "Friday"
        df.loc[df.weekday == 5, "weekday"] = "Saturday"
        df.loc[df.weekday == 6, "weekday"] = "Sunday"
        return (df)

    # this works for all sports
    def getGameData(self, data):
        # get data for each game
        rows = []
        for x in data:
            # get game data
            ufd = requests.get(x["$ref"])
            ha = ufd.json()

            # only do current dates
            game_date = ha["date"]
            game_date = pd.to_datetime(game_date).tz_convert('US/Eastern')
            now_min = datetime.now(pytz.timezone("US/Eastern")) - timedelta(days=1)
            now_max = datetime.now(pytz.timezone("US/Eastern")) + timedelta(days=1)

            # skip game if beyond date range
            if (game_date < now_min) or (game_date > now_max):
                time.sleep(1)
                continue

            # flatten
            gamePk = ha["id"]
            print(gamePk)
            comp_links = ha['competitions'][0]["competitors"]

            # type
            type_txt = ha['competitions'][0].get("type", {}).get("text", None)
            type_abbr = ha['competitions'][0].get("type", {}).get("abbreviation", None)

            # HOME Team (team1)
            home_comp = [x for x in comp_links if x["homeAway"] == "home"][0]
            team1_url = home_comp["team"]["$ref"]
            resp = requests.get(team1_url).json()

            # get team1 metadata
            team1_id = resp["id"]
            team1 = resp["abbreviation"]
            team1_name = resp["displayName"]

            team1_logos = resp.get("logos", [])
            if len(team1_logos) > 0:
                team1_logo = team1_logos[0].get("href", self.default_logo)
            else:
                team1_logo = self.default_logo

            # scores can be sketch
            try:
                home_url = home_comp["score"]["$ref"]
                resp = requests.get(home_url)
                score1 = resp.json().get("value", 0)
            except:
                score1 = 0

            # AWAY Team
            away_comp = [x for x in comp_links if x["homeAway"] == "away"][0]
            team2_url = away_comp["team"]["$ref"]
            resp = requests.get(team2_url).json()

            # get team2 metadata
            team2_id = resp["id"]
            team2 = resp["abbreviation"]
            team2_name = resp["displayName"]

            team2_logos = resp.get("logos", [])
            if len(team2_logos) > 0:
                team2_logo = team2_logos[0].get("href", self.default_logo)
            else:
                team2_logo = self.default_logo

            # scores can be sketch
            try:
                away_url = away_comp["score"]["$ref"]
                resp = requests.get(away_url)
                score2 = resp.json().get("value", 0)
            except:
                score2 = 0

            # odds for both are a bit sketch
            odds_url = ha['competitions'][0].get("odds", {}).get('$ref', "")
            date = ha["date"]
            try:
                # get odds
                if (odds_url):
                    resp = requests.get(odds_url)
                    data2 = resp.json()

                    # cricket has frac odds
                    if "moneyLine" in data2["items"][0]["awayTeamOdds"].keys():
                        away_odds = data2["items"][0]["awayTeamOdds"].get("moneyLine", 100)
                        home_odds = data2["items"][0]["homeTeamOdds"].get("moneyLine", 100)
                    else:
                        away_odds = data2["items"][0]["awayTeamOdds"]["odds"].get("summary", "1/1")
                        home_odds = data2["items"][0]["homeTeamOdds"]["odds"].get("summary", "1/1")

                        # convert to moneyline
                        away_odds = self.fracToMoneyline(away_odds)
                        home_odds = self.fracToMoneyline(home_odds)

                    provider = data2["items"][0]["provider"].get("name", "")
                    details = data2["items"][0].get("details", "")
                else:
                    home_odds = 100
                    away_odds = 100
                    provider = ""
                    details = ""
            except:
                # defaults
                home_odds = 100
                away_odds = 100
                provider = ""
                details = ""

            # get game_status
            status_url = ha['competitions'][0].get("status", {}).get('$ref', "")
            try:
                # get status
                if (status_url):
                    resp = requests.get(status_url)
                    data3 = resp.json()
                    status_id = data3.get("type", {}).get("id", None)
                    if status_id:
                        status_id = int(status_id)

                    # dumb CWC status data
                    if "name" in data3.get("type", {}):
                        status = data3.get("type", {}).get("name", None)
                    else:
                        status = data3.get("type", {}).get("shortDetail", None)
                        status = f"STATUS_{status.upper()}"
                else:
                    status_id = None
                    status = None
            except:
                # defaults
                status_id = None
                status = None

            # final flat data
            row = {"date": date, "gamepk": gamePk, "game_type": type_txt, "game_type_abbr": type_abbr, "team1": team1, "team2": team2, "team1_name": team1_name, "team2_name": team2_name, "team1_id": team1_id, "team2_id": team2_id, "team1_logo": team1_logo, "team2_logo": team2_logo, "odds_provider": provider, "odds_details": details, "team2_odds": away_odds, "team1_odds": home_odds, "score1": score1, "score2": score2, "status_id": status_id, "status": status}
            rows.append(row)

            # sleep
            time.sleep(1)

        # make final dataframe
        df3 = pd.DataFrame(rows)

        if len(df3) > 0:
            df3["team2_odds_wp"] = df3.team2_odds.apply(self.moneylineWinPercent)
            df3["team1_odds_wp"] = df3.team1_odds.apply(self.moneylineWinPercent)

            df3["team2_odds"] = [f"+{x}" if x > 0 else f"{x}" for x in df3.team2_odds]
            df3["team1_odds"] = [f"+{x}" if x > 0 else f"{x}" for x in df3.team1_odds]

            # fun with datetime
            df3["date"] = pd.to_datetime(df3["date"]).dt.tz_convert('US/Eastern')
            df3['date_str'] = df3['date'].dt.strftime('%m/%d/%Y')
            df3["time"] = df3["date"].dt.strftime("%I:%M %p").str.strip("0")
            df3["game_id"] = df3.team2 + "_" + df3.team1 + "_" + df3.gamepk.astype(str)

        return(df3)

    def writeToDatabase(self, df, inp_table, gamepks):
        # write to database
        conn = self.engine.connect()

        query = f"delete from {inp_table} where gamepk in ({gamepks})"
        self.engine.execute(query)

        # write out
        df.to_sql(inp_table, con=conn, index=False, if_exists="append", method="multi")

        # close connection
        conn.close()
        return({"ok": True})
