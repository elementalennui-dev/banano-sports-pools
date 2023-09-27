import pandas as pd
import requests

class NFLRefreshHelper():
    def __init__(self, refreshHelper):
        self.refreshHelper = refreshHelper

    ############################################################
    ###################### NFL #################################
    ############################################################
    def getNFLData(self, week, season):

        # regular season
        if week <= 18:
            url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/types/2/weeks/{week}/events"
        else: # playoffs
            url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/types/3/weeks/{week-18}/events"

        r = requests.get(url)
        data = r.json()["items"]
        game_data = self.refreshHelper.getGameData(data)
        return (game_data)

    def getCurrentNFLWeek(self, nfl_season):
        # get nfl week
        query = f"""
                select
                    coalesce(min(nfl_week), 23)
                from
                    nfl_games ng
                where
                    ng.nfl_season = {nfl_season}
                    and ng."date" > (NOW() - INTERVAL '1 DAY');"""

        nfl_week = list(self.refreshHelper.engine.execute(query))[0][0]
        return(int(nfl_week))

    def refreshNFLData(self, season):
        # curr_week = self.getCurrentNFLWeek(season)

        # list for data
        game_data = []

        # loop through each week and playoffs
        for week in range(1, 24):
            if week == 22:
                continue # pro bowl

            # else, get data
            sub = self.getNFLData(week, season)
            sub["nfl_week"] = week
            sub["nfl_season"] = season

            # back to records
            rtn = sub.to_dict(orient="records")
            game_data.extend(rtn)
            print(week)

        # make dataframe
        df = pd.DataFrame(game_data)
        df = self.refreshHelper.getWeekday(df)

        # write to database
        self.refreshHelper.writeToDatabase(df, "nfl_games", season, "nfl_season")
        return({"ok": True})
