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
        r = requests.get(f"http://core.espnuk.org/v2/sports/cricket/leagues/8039/seasons/{season}/events")
        data = r.json()["items"]

        game_data = self.refreshHelper.getGameData(data)
        return (game_data)

    def refreshCWCData(self, season):
        # make dataframe
        df = self.getCWCData(season)

        if len(df) > 0:
            df = self.refreshHelper.getWeekday(df)
            df["match_round"] = "group"
            df["season"] = 2023

            # cricket runs - either 286/9 or 289 (...)
            df["score1"] = df.score1.str.split("/").str[0].str.strip()
            df["score2"] = df.score2.str.split("/").str[0].str.strip()
            df["score1"] = df.score1.str.split(" ").str[0].str.strip()
            df["score2"] = df.score2.str.split(" ").str[0].str.strip()
            df["score1"] = pd.to_numeric(df.score1)
            df["score2"] = pd.to_numeric(df.score2)

            df["score1"] = df.score1.fillna(0)
            df["score2"] = df.score2.fillna(0)

            # get gamepks
            gamepks = ", ".join(df.gamepk.astype(str).to_list())

            # write to database
            self.refreshHelper.writeToDatabase(df, "cricket_world_cup_games", gamepks)
        else:
            print("No CWC Data Found to refresh..")
        return({"ok": True})
