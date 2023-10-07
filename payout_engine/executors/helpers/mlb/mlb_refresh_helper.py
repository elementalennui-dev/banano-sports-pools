import pandas as pd
import requests

class MLBRefreshHelper():
    def __init__(self, refreshHelper):
        self.refreshHelper = refreshHelper
        self.rounds = {"Quarterfinal": "Division Series",
         "Semifinal": "Championship Series",
         "Round of 16": "Wildcard",
         "Final": "World Series"}

    ############################################################
    ###################### MLB #################################
    ############################################################
    def getMLBData(self, season):

        # get data by date range (2 pages)
        data = []

        for page in range(1,3):
            # playoffs
            url = f"https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb/seasons/{season}/types/3/events?page={page}"
            r = requests.get(url)
            data_page = r.json()
            data.extend(data_page["items"])

        game_data = self.refreshHelper.getGameData(data)
        return (game_data)

    def refreshMLBData(self, season):
        # make dataframe
        df = self.getMLBData(season)

        if len(df) > 0:
            df = self.refreshHelper.getWeekday(df)
            df["match_round"] = [self.rounds[x] if x in self.rounds.keys() else None for x in df.game_type]
            df["mlb_season"] = season

            # get gamepks
            gamepks = ", ".join(df.gamepk.astype(str).to_list())

            # write to database
            self.refreshHelper.writeToDatabase(df, "mlb_games", gamepks)
        else:
            print("No MLB Data Found to refresh..")
        return({"ok": True})
