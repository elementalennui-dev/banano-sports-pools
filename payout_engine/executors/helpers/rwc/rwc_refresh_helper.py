import pandas as pd
import requests

class RWCRefreshHelper():
    def __init__(self, refreshHelper):
        self.refreshHelper = refreshHelper
        self.rwc_groups = {'ARG': "D",
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

    ############################################################
    ###################### NFL #################################
    ############################################################
    def getRWCData(self):

        # get data by date range (2 pages)
        data = []
        for page in range(1,3):
            r = requests.get(f"https://sports.core.api.espn.com/v2/sports/rugby/leagues/164205/events?dates=20230908-20231029&page={page}")
            data_page = r.json()
            data.extend(data_page["items"])

        game_data = self.refreshHelper.getGameData(data)
        return (game_data)

    def refreshRWCData(self, season):
        # make dataframe
        df = self.getRWCData()

        if len(df) > 0:
            df = self.refreshHelper.getWeekday(df)
            # df["group_name"] = [self.rwc_groups[x] if x in self.rwc_groups.keys() else None for x in df.team1]

            # round and season
            df["match_round"] = "knockout"
            df.loc[:, "group_name"] = None
            df["season"] = season

            # get gamepks
            gamepks = ", ".join(df.gamepk.astype(str).to_list())

            # write to database
            self.refreshHelper.writeToDatabase(df, "rugby_world_cup_games", gamepks)
        else:
            print("No RWC Data Found to refresh..")
        return({"ok": True})
