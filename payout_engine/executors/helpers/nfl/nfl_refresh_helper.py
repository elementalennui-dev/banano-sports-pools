import pandas as pd
import requests
from sqlalchemy import text

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
        query =f"""
                select
                    nfl_week
                from
                    nfl_games ng
                where
                    ng.nfl_season = {nfl_season}
                    and ng."date" > (NOW() - INTERVAL '1 DAY')
                order by
                    ng."date" asc
                limit 1;"""

        with self.refreshHelper.engine.connect() as conn:
            result = conn.execute(text(query))
            nfl_week = list(result)[0][0]

        return(int(nfl_week))

    def refreshNFLData(self, season):
        curr_week = 1

        # make dataframe
        df = self.getNFLData(curr_week, season)

        if len(df) > 0:
            df["nfl_week"] = curr_week
            df["nfl_season"] = season
            df = self.refreshHelper.getWeekday(df)

            # get gamepks
            gamepks = ", ".join(df.gamepk.astype(str).to_list())

            # write to database
            self.refreshHelper.writeToDatabase(df, "nfl_games", gamepks)
        else:
            print("No NFL Data Found to refresh..")
        return({"ok": True})
