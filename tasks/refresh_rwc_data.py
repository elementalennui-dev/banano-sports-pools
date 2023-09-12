import pandas as pd
import datetime
import pytz
import requests
import numpy as np

from sqlalchemy import create_engine
from config import POSTGRES_URL

def moneylineWinPercent(ml):
    if (ml > 0):
        return (100 / (ml + 100))
    else:
        ml = abs(ml)
        return (ml / (ml + 100))

def getRWCData():
    # get data by date range (2 pages)
    data = []
    for page in range(1,3):
        r = requests.get(f"https://sports.core.api.espn.com/v2/sports/rugby/leagues/164205/events?dates=20230908-20231028&page={page}")
        data_page = r.json()
        data.extend(data_page["items"])
        print(page)

    # get data for each game
    rows = []
    for x in data:
        # get game data
        ufd = requests.get(x["$ref"])
        ha = ufd.json()

        # flatten
        gamePk = ha["id"]
        comp_links = ha['competitions'][0]["competitors"]

        # HOME Team (team1)
        home_comp = [x for x in comp_links if x["homeAway"] == "home"][0]
        team1_url = home_comp["team"]["$ref"]
        resp = requests.get(team1_url).json()

        # get team1 metadata
        team1_id = resp["id"]
        team1 = resp["abbreviation"]
        team1_name = resp["displayName"]
        default_logo = "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/default-team-logo-500.png"

        team1_logos = resp.get("logos", [])
        if len(team1_logos) > 0:
            team1_logo = team1_logos[0].get("href", default_logo)
        else:
            team1_logo = default_logo

        # SCORE
        home_url = home_comp["score"]["$ref"]
        resp = requests.get(home_url)
        score1 = resp.json().get("value", np.nan)

        # AWAY Team (team2)
        away_comp = [x for x in comp_links if x["homeAway"] == "away"][0]
        team2_url = away_comp["team"]["$ref"]
        resp = requests.get(team2_url).json()

        # get team2 metadata
        team2_id = resp["id"]
        team2 = resp["abbreviation"]
        team2_name = resp["displayName"]

        team2_logos = resp.get("logos", [])
        if len(team2_logos) > 0:
            team2_logo = team2_logos[0].get("href", default_logo)
        else:
            team2_logo = default_logo

        away_url = away_comp["score"]["$ref"]
        resp = requests.get(away_url)
        score2 = resp.json().get("value", np.nan)

        # odds are a bit sketch
        odds_url = ha['competitions'][0].get("odds", {}).get('$ref', "")
        date = ha["date"]
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
        row = {"date": date, "gamepk": gamePk, "team1": team1, "team2": team2, "team1_name": team1_name, "team2_name": team2_name, "team1_id": team1_id, "team2_id": team2_id, "team1_logo": team1_logo, "team2_logo": team2_logo, "odds_provider": provider, "odds_details": details, "team2_odds": away_odds, "team1_odds": home_odds, "score1": score1, "score2": score2}
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
season = now.year

# list for data
df = getRWCData()
df["weekday"] = df["date"].apply(lambda x: x.weekday())

# map weekday
df.loc[df.weekday == 0, "weekday"] = "Monday"
df.loc[df.weekday == 1, "weekday"] = "Tuesday"
df.loc[df.weekday == 2, "weekday"] = "Wednesday"
df.loc[df.weekday == 3, "weekday"] = "Thursday"
df.loc[df.weekday == 4, "weekday"] = "Friday"
df.loc[df.weekday == 5, "weekday"] = "Saturday"
df.loc[df.weekday == 6, "weekday"] = "Sunday"

# get group
groups = {'ARG': "D",
 'AUS': "C",
 'CHI': "D",
 'ENG': "D",
 'FIJI': "C",
 'FRA': "A",
 'GEORG': "C",
 'IRE': "B",
 'ITALY': "A",
 'JPN': "D",
 'NAMIB': "A",
 'NZ': "A",
 'PORT': "C",
 'ROM': "B",
 'SA': "B",
 'SAMOA': "D",
 'SCOT': "B",
 'TONGA': "B",
 'URUG': "A",
 'WALES': "C"}

df["group_name"] = [groups[x] if x in groups.keys() else None for x in df.team1]

# round and season
df["match_round"] = None
df.loc[0:40, "match_round"] = "group"
df.loc[40:, "group_name"] = None
df["season"] = season

# write to database
engine = create_engine(POSTGRES_URL)
conn = engine.connect()

engine.execute(f"delete from rugby_world_cup_games where season = {season}")
df.to_sql("rugby_world_cup_games", con=conn, index=False, if_exists="append", method="multi")

# close connection
conn.close()
engine.dispose()
print(f"Refreshed RWC data at {now.isoformat()}")
