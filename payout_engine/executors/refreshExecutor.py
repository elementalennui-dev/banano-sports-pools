from executors.funcs.refreshHelper import RefreshHelper
from executors.helpers.nfl.nfl_refresh_helper import NFLRefreshHelper
# from executors.helpers.rwc.rwc_refresh_helper import RWCRefreshHelper
# from executors.helpers.mlb.mlb_refresh_helper import MLBRefreshHelper
# from executors.helpers.cwc.cwc_refresh_helper import CWCRefreshHelper
# from executors.helpers.nba.nba_refresh_helper import NBARefreshHelper
# from executors.helpers.nhl.nhl_refresh_helper import NHLRefreshHelper
from datetime import datetime
import pytz

class RefreshExecutor():
    def __init__(self):
        self.refreshHelper = RefreshHelper()
        self.nflRefreshHelper = NFLRefreshHelper(self.refreshHelper)
        # self.rwcRefreshHelper = RWCRefreshHelper(self.refreshHelper)
        # self.mlbRefreshHelper = MLBRefreshHelper(self.refreshHelper)
        # self.cwcRefreshHelper = CWCRefreshHelper(self.refreshHelper)
        # self.nbaRefreshHelper = NBARefreshHelper(self.refreshHelper)
        # self.nhlRefreshHelper = NHLRefreshHelper(self.refreshHelper)

        # dynamic season
        self.now = datetime.now(pytz.timezone("US/Eastern"))
        self.season = self.now.year
        self.nfl_season = self.now.year if self.now.month >= 3 else self.now.year - 1

    def refreshSports(self):
        # refresh RWC Data
        # print(f"Refreshing RWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        # self.rwcRefreshHelper.refreshRWCData(self.season)
        # print(f"Refreshed RWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # refresh NFL Data
        print(f"Refreshing NFL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        self.nflRefreshHelper.refreshNFLData(self.nfl_season)
        print(f"Refreshed NFL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # refresh MLB Data
        # print(f"Refreshing MLB data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        # self.mlbRefreshHelper.refreshMLBData(self.season)
        # print(f"Refreshed MLB data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # refresh CWC Data
        # print(f"Refreshing CWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        # self.cwcRefreshHelper.refreshCWCData(self.season)
        # print(f"Refreshed CWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # refresh NBA Data
        # print(f"Refreshing NBA data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        # self.nbaRefreshHelper.refreshNBAData(self.season)
        # print(f"Refreshed NBA data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # refresh NHL Data
        # print(f"Refreshing NHL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        # self.nhlRefreshHelper.refreshNHLData(self.season)
        # print(f"Refreshed NHL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        return True
