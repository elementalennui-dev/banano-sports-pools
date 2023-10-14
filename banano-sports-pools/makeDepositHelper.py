import pandas as pd
import datetime
import requests
import pytz
import numpy as np
from databaseHelper import DataBaseHelper

class MakeDepositHelper():

    def __init__(self):
        # Define x minutes as a timedelta object
        self.ten_minute_duration = datetime.timedelta(minutes=10)
        self.databaseHelper = DataBaseHelper()

    #########################################################################
    ########################### DEPOSITS ####################################
    #########################################################################
    def confirmDeposit(self, ban_address, sport, game_id, team_num, team_abbr, deposit_amount, table, week_col, season_col, week_inp, season_inp):
        if sport == "nfl":
            bet_table = "nfl_bets"
            data = self.databaseHelper.nfl.getNFLGameOdds(week_inp, season_inp)
        elif sport == "mlb":
            bet_table = "mlb_bets"
            data = self.databaseHelper.mlb.getMLBGameOdds(week_inp, season_inp)
        elif sport == "cwc":
            bet_table = "cricket_world_cup_bets"
            data = self.databaseHelper.cwc.getCWCGameOdds(week_inp, season_inp)
        else:
            bet_table = "rugby_world_cup_bets"
            data = self.databaseHelper.rwc.getRWCGameOdds(week_inp, season_inp)

        game = data.loc[data.game_id == game_id]
        game_time = game.reset_index().gametime[0]

        now = datetime.datetime.now(pytz.timezone("US/Eastern"))

        if now > game_time:
            # can't place deposit after game time
            return ({"confirmed": False, "message": "Can't place deposit after game starts!"})

        # check creeper for transaction
        url = "https://api.creeper.banano.cc/banano/v2/account/confirmed-transactions"
        payload = {
            "address": ban_address,
            "size": 10,
            "offset": 0,
            "includeReceive": False,
            "includeChange": False,
            "includeSend": True,
            "filterAddresses": ["ban_3sprts3a8hzysquk4mcy4ct4f6izp1mxtbnybiyrriprtjrn9da9cbd859qf"],
            "excludedAddresses": [],
            "reverse": False,
            "onlyIncludeKnownAccounts": False,
            "onlyIncludeUnknownAccounts": False
        }

        response = requests.post(url, json = payload)

        data = response.json()
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df.date).dt.tz_localize('UTC').dt.tz_convert('US/Eastern')

        now = pd.Timestamp(now)
        diff = now - df["date"][0]
        found_amount = df["amount"][0]

        # check block exists in database instead of time limit
        block_exists = self.databaseHelper.checkBlockExists(bet_table, df.hash[0])
        # print(block_exists)
        if (block_exists["ok"]) & (diff <= self.ten_minute_duration) & (deposit_amount == found_amount):
            row = {"block": df.hash[0],
                    "bet_amount": df.amount[0],
                    "ban_address": ban_address,
                    "game_id": game_id,
                    "betting_team_num": team_num,
                    "betting_team": team_abbr,
                    "date": df.date[0].strftime('%m/%d/%Y %H:%M:%S'),
                    "timestamp": df.timestamp[0],
                    week_col: week_inp,
                    season_col: season_inp,
                    "is_active": True}

            insert_df = pd.DataFrame([row])
            self.databaseHelper.writeDeposit(insert_df, table)

            return ({"confirmed": True, "message": f"Deposit Confirmed! Received {df.amount[0]} BAN at {df.date[0].strftime('%m/%d/%Y %H:%M:%S')} ET on {team_abbr} to win. Block: {df.hash[0]}. <a target='_blank' href='https://creeper.banano.cc/hash/{df.hash[0]}'>View Block on Creeper</a>"})
        else:
            return ({"confirmed": False, "message": "Deposit not found! Why don't you give it a minute and then try again?"})
