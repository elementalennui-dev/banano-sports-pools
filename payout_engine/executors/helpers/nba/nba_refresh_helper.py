import pandas as pd
import requests

class NBARefreshHelper():
    def __init__(self, refreshHelper):
        self.refreshHelper = refreshHelper
        # self.rounds = {"Quarterfinal": "Division Series",
        #  "Semifinal": "Championship Series",
        #  "Round of 16": "Wildcard",
        #  "Final": "World Series"}

    ############################################################
    ###################### NBA #################################
    ############################################################
    def getNBAData(self, season):

        # get data by date range
        data = []
        base_url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/{season}/types/3/events"
        pages = requests.get(base_url).json().get("pageCount", 1)

        for page in range(1, pages + 1):
            # playoffs
            url = f"{base_url}?page={page}"
            r = requests.get(url)
            data_page = r.json()
            data.extend(data_page["items"])

        game_data = self.refreshHelper.getGameData(data)
        return (game_data)

    def refreshNBAData(self, season):
        # make dataframe
        df = self.getNBAData(season)

        if len(df) > 0:
            df = self.refreshHelper.getWeekday(df)
            df["match_round"] = df.game_type
            df["nba_season"] = season

            # get gamepks
            gamepks = ", ".join(df.gamepk.astype(str).to_list())

            # write to database
            self.refreshHelper.writeToDatabase(df, "nba_games", gamepks)
        else:
            print("No NBA Data Found to refresh..")
        return({"ok": True})
