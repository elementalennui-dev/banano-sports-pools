from executors.funcs.refreshHelper import RefreshHelper
from executors.helpers.nfl.nfl_refresh_helper import NFLRefreshHelper
from executors.helpers.rwc.rwc_refresh_helper import RWCRefreshHelper
from datetime import datetime
import pytz

class RefreshExecutor():
    def __init__(self):
        self.refreshHelper = RefreshHelper()
        self.nflRefreshHelper = NFLRefreshHelper(self.refreshHelper)
        self.rwcRefreshHelper = RWCRefreshHelper(self.refreshHelper)

        # dynamic season
        self.now = datetime.now(pytz.timezone("US/Eastern"))
        self.season = self.now.year
        self.nfl_season = self.now.year if self.now.month >= 3 else self.now.year - 1

    def refreshSports(self):
        # refresh RWC Data
        print(f"Refreshing RWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        self.rwcRefreshHelper.refreshRWCData(self.season)
        print(f"Refreshed RWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # refresh NFL Data
        print(f"Refreshing NFL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        self.nflRefreshHelper.refreshNFLData(self.nfl_season)
        print(f"Refreshed NFL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        return True
