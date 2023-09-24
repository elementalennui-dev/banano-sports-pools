from executors.funcs.payoutsHelper import PayoutsHelper
from executors.helpers.nfl.nfl_payouts_helper import NFLPayoutsHelper
from executors.helpers.rwc.rwc_payouts_helper import RWCPayoutsHelper
from datetime import datetime
import pytz

class PayoutsExecutor():
    def __init__(self):
        self.payoutsHelper = PayoutsHelper()
        self.nflPayoutsHelper = NFLPayoutsHelper(self.payoutsHelper)
        self.rwcPayoutsHelper = RWCPayoutsHelper(self.payoutsHelper)

        # dynamic season
        self.now = datetime.now(pytz.timezone("US/Eastern"))
        self.season = self.now.year
        self.nfl_season = self.now.year if self.now.month >= 3 else self.now.year - 1

    def receiveFunds(self):
        print(f"Receiving funds at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        self.payoutsHelper.receiveFunds()
        print(f"Received funds at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        return True

    def sendPayouts(self):
        # payouts for RWC Data
        print(f"Paying out RWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        match_round = self.rwcPayoutsHelper.getCurrentRWCWeek(self.season)
        self.rwcPayoutsHelper.sendRWCPayouts(self.season, match_round)
        print(f"Paid out RWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # payouts for NFL Data
        print(f"Paying out NFL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        nfl_week = self.nflPayoutsHelper.getCurrentNFLWeek(self.nfl_season)
        self.nflPayoutsHelper.sendNFLPayouts(self.nfl_season, nfl_week)
        print(f"Paid out NFL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        return True
