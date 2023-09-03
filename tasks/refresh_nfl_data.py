import pandas as pd
import datetime
import pytz
import requests
import numpy as np

from sqlalchemy import create_engine, inspect
from config import POSTGRES_URL

def moneylineWinPercent(ml):
    if (ml > 0):
        return (100 / (ml + 100))
    else:
        ml = abs(ml)
        return (ml / (ml + 100))

def getNFLData(week, season):

    # regular season
    if week <= 18:
        url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/types/2/weeks/{week}/events"
    else: # playoffs
        url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/types/3/weeks/{week-18}/events"

    r = requests.get(url)
    data = r.json()["items"]

    # get data for each game
    rows = []
    for x in data:
        # get game data
        ufd = requests.get(x["$ref"])
        ha = ufd.json()

        # flatten
        gamePk = ha["id"]

        # parse out team names
        if "@" in ha["shortName"]:
            team2 = ha["shortName"].replace("@", "").split("  ")[0]
            team1 = ha["shortName"].replace("@", "").split("  ")[1]
        else: # likely SuperBowl
            team2 = ha["shortName"].replace("VS", "").split("  ")[0]
            team1 = ha["shortName"].replace("VS", "").split("  ")[1]

        odds_url = ha['competitions'][0].get("odds", {}).get('$ref', "")
        date = ha["date"]
        team2_name = ha["name"].split(" at ")[0]
        team1_name = ha["name"].split(" at ")[1]

        # get scores (can be sketch)
        try:
            comp_links = ha['competitions'][0]["competitors"]
            if len(comp_links) > 0:
                home_comp = [x for x in comp_links if x["homeAway"] == "home"][0]
                home_url = home_comp["score"]["$ref"]
                resp = requests.get(home_url)
                score1 = resp.json()["value"]

                # away score
                away_comp = [x for x in comp_links if x["homeAway"] == "away"][0]
                away_url = away_comp["score"]["$ref"]
                resp = requests.get(away_url)
                score2 = resp.json()["value"]
            else:
                score1 = np.nan
                score2 = np.nan
        except:
            score1 = np.nan
            score2 = np.nan

        # odds are a bit sketch too
        try:
            # get odds
            if (odds_url):
                resp = requests.get(odds_url)
                data2 = resp.json()
                away_odds = data2["items"][0]["awayTeamOdds"].get("moneyLine", 100)
                home_odds = data2["items"][0]["homeTeamOdds"].get("moneyLine", 100)

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

        # final flat data
        row = {"date": date, "gamepk": gamePk, "team1": team1, "team2": team2, "team1_name": team1_name, "team2_name": team2_name, "odds_provider": provider, "odds_details": details, "team2_odds": away_odds, "team1_odds": home_odds, "score1": score1, "score2": score2}
        rows.append(row)

    # make final dataframe
    df3 = pd.DataFrame(rows)
    df3["team2_odds_wp"] = df3.team2_odds.apply(moneylineWinPercent)
    df3["team1_odds_wp"] = df3.team1_odds.apply(moneylineWinPercent)

    df3["team2_odds"] = [f"+{x}" if x > 0 else f"{x}" for x in df3.team2_odds]
    df3["team1_odds"] = [f"+{x}" if x > 0 else f"{x}" for x in df3.team1_odds]

    # fun with datetime
    df3["date"] = pd.to_datetime(df3["date"]).dt.tz_convert('US/Eastern')
    df3['date_str'] = df3['date'].dt.strftime('%m/%d/%Y')
    df3["time"] = df3["date"].dt.strftime("%I:%M %p").str.strip("0")
    df3["game_id"] = df3.team2 + "_" + df3.team1 + "_" + df3.gamepk.astype(str)

    return(df3)

# dynamic season
now = datetime.datetime.now()
season = now.year if now.month >= 3 else now.year - 1

# list for data
game_data = []

# loop through each week and playoffs
for week in range(1, 24):
    if week == 22:
        continue # pro bowl

    # else, get data
    sub = getNFLData(week, season)
    sub["nfl_week"] = week
    sub["nfl_season"] = season

    # back to records
    rtn = sub.to_dict(orient="records")
    game_data.extend(rtn)
    print(week)

# make dataframe
df = pd.DataFrame(game_data)
df["weekday"] = df["date"].apply(lambda x: x.weekday())

# map weekday
df.loc[df.weekday == 0, "weekday"] = "Monday"
df.loc[df.weekday == 1, "weekday"] = "Tuesday"
df.loc[df.weekday == 2, "weekday"] = "Wednesday"
df.loc[df.weekday == 3, "weekday"] = "Thursday"
df.loc[df.weekday == 4, "weekday"] = "Friday"
df.loc[df.weekday == 5, "weekday"] = "Saturday"
df.loc[df.weekday == 6, "weekday"] = "Sunday"

# write to database
engine = create_engine(POSTGRES_URL)
conn = engine.connect()

engine.execute(f"delete from table nfl_games where nfl_season = {season}")
df.to_sql("nfl_games", con=conn, index=False, if_exists="append", method="multi")
