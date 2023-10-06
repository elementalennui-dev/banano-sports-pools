import pandas as pd
import requests

class CWCRefreshHelper():
    def __init__(self, refreshHelper):
        self.refreshHelper = refreshHelper

    ############################################################
    ###################### CWC #################################
    ############################################################
    def getCWCData(self, season):

        # get data by date range
        r = requests.get(f"http://core.espnuk.org/v2/sports/cricket/leagues/8039/seasons/2023/events")
        data = r.json()["items"]

        game_data = self.refreshHelper.getGameData(data)
        return (game_data)

    def refreshCWCData(self, season):
        # make dataframe
        df = self.getCWCData(season)
        df = self.refreshHelper.getWeekday(df)
        df["match_round"] = None
        df.loc[0:48, "match_round"] = "group"
        df["season"] = 2023

        # cricket runs
        df["score1"] = df.score1.str.split("/").str[0]
        df["score2"] = df.score2.str.split("/").str[0]
        df["score1"] = pd.to_numeric(df.score1)
        df["score2"] = pd.to_numeric(df.score2)

        # write to database
        self.refreshHelper.writeToDatabase(df, "cricket_world_cup_games", season, "season")
        return({"ok": True})
