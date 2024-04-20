from executors.funcs.payoutsHelper import PayoutsHelper
# from executors.helpers.nfl.nfl_payouts_helper import NFLPayoutsHelper
# from executors.helpers.rwc.rwc_payouts_helper import RWCPayoutsHelper
# from executors.helpers.mlb.mlb_payouts_helper import MLBPayoutsHelper
# from executors.helpers.cwc.cwc_payouts_helper import CWCPayoutsHelper
from executors.helpers.nba.nba_payouts_helper import NBAPayoutsHelper
from executors.helpers.nhl.nhl_payouts_helper import NHLPayoutsHelper
from datetime import datetime
import pytz

class PayoutsExecutor():
    def __init__(self):
        self.payoutsHelper = PayoutsHelper()
        # self.nflPayoutsHelper = NFLPayoutsHelper(self.payoutsHelper)
        # self.rwcPayoutsHelper = RWCPayoutsHelper(self.payoutsHelper)
        # self.mlbPayoutsHelper = MLBPayoutsHelper(self.payoutsHelper)
        # self.cwcPayoutsHelper = CWCPayoutsHelper(self.payoutsHelper)
        self.nbaPayoutsHelper = NBAPayoutsHelper(self.payoutsHelper)
        self.nhlPayoutsHelper = NHLPayoutsHelper(self.payoutsHelper)

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
        # print(f"Paying out RWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        # match_round = self.rwcPayoutsHelper.getCurrentRWCWeek(self.season)
        # self.rwcPayoutsHelper.sendRWCPayouts(self.season, match_round)
        # print(f"Paid out RWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # payouts for NFL Data
        # print(f"Paying out NFL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        # nfl_week = self.nflPayoutsHelper.getCurrentNFLWeek(self.nfl_season)
        # self.nflPayoutsHelper.sendNFLPayouts(self.nfl_season, nfl_week)
        # print(f"Paid out NFL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # payouts for MLB Data
        # print(f"Paying out MLB data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        # match_round = self.mlbPayoutsHelper.getCurrentMLBWeek(self.season)
        # self.mlbPayoutsHelper.sendMLBPayouts(self.season, match_round)
        # print(f"Paid out MLB data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # payouts for CWC Data
        # print(f"Paying out CWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        # match_round = self.cwcPayoutsHelper.getCurrentCWCWeek(self.season)
        # self.cwcPayoutsHelper.sendCWCPayouts(self.season, match_round)
        # print(f"Paid out CWC data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # payouts for NBA Data
        print(f"Paying out NBA data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        match_round = self.nbaPayoutsHelper.getCurrentNBAWeek(self.season)
        self.nbaPayoutsHelper.sendNBAPayouts(self.season, match_round)
        print(f"Paid out NBA data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        # payouts for NHL Data
        print(f"Paying out NHL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")
        match_round = self.nhlPayoutsHelper.getCurrentNHLWeek(self.season)
        self.nhlPayoutsHelper.sendNHLPayouts(self.season, match_round)
        print(f"Paid out NHL data at {datetime.now(pytz.timezone('US/Eastern')).isoformat()}")

        return True
