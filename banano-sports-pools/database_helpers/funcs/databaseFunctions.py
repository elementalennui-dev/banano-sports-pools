import pandas as pd
import numpy as np
import datetime
import pytz

class DatabaseFunctions():

    def __init__(self):
        pass

    def cleanGameOdds(self, df):
        # localize datetimes
        df["gametime"] = df.gametime.dt.tz_localize('UTC').dt.tz_convert('US/Eastern')

        # set disabled flag
        now = datetime.datetime.now(pytz.timezone("US/Eastern"))
        now = pd.Timestamp(now)
        df["started"] = df["gametime"] < now
        df["disabled"] = ["disabled" if x else "" for x in df.started]
        df["score1"] = df.score1.astype(str)
        df["score2"] = df.score2.astype(str)

        # score placeholder
        df.loc[~df.started, "score1"] = "-"
        df.loc[~df.started, "score2"] = "-"

        return (df)

    def cleanLeaderboardCols(self, df, ban_address=None):
        # new cols
        df["return_perc"] = (df.payout - df.bet_amount) / df.bet_amount
        df["profit"] = df.payout - df.bet_amount
        df["win_perc"] = df.is_winner.astype(int)

        # determine if single leaderboard or game
        if (ban_address):
            cols = ['ban_address', 'bet_amount', 'game_id', 'betting_team', 'is_winner',
                    'is_tie', 'payout', 'profit', 'return_perc', 'win_perc']
            rtn = df.loc[df.ban_address == ban_address, cols].sort_values(by="profit", ascending=False).reset_index(drop=True)
        else:
            # group by ban_address, calc summary stats
            summ = df.groupby(["ban_address"]).agg({"bet_amount": "sum", "game_id":"nunique", "is_winner": "sum", "is_tie":"sum", "payout": "sum"}).reset_index()
            summ["profit"] = summ.payout - summ.bet_amount
            summ["return_perc"] = (summ.payout - summ.bet_amount) / summ.bet_amount
            summ["win_perc"] = summ.is_winner / summ.game_id
            cols = ['ban_address', 'bet_amount', 'game_id', 'is_winner',
                    'is_tie', 'payout', 'profit', 'return_perc', 'win_perc']
            rtn = summ.loc[:, cols].sort_values(by="profit", ascending=False)

        return (rtn)

    def calculateDepositAggregates(self, df):
        df_sub = df.groupby(["game_id", "betting_team_num"]).bet_amount.sum().reset_index()
        df_sub = df_sub.sort_values(by="game_id")

        # have to transpose to one row per game
        new_rows = []

        games = df_sub.game_id.unique()

        for game_id in games:
            new_row = {"game_id": game_id, "team1_bets": np.nan, "team2_bets" : np.nan}
            sub = df_sub.loc[df_sub.game_id == game_id]
            for _, row in sub.iterrows():
                new_row[f"{row.betting_team_num}_bets"] = row.bet_amount

            new_rows.append(new_row)

        # deposit aggregates
        if len(new_rows) > 0:
            deposits = pd.DataFrame(new_rows)
        else:
            deposits = pd.DataFrame(columns=["game_id", "team1_bets", "team2_bets"])
        deposits_total = df.groupby(["game_id"]).bet_amount.sum().reset_index()

        # final merge
        deposits = pd.merge(deposits, deposits_total, on="game_id")
        deposits["team1_perc"] = deposits.team1_bets / deposits.bet_amount
        deposits["team2_perc"] = deposits.team2_bets / deposits.bet_amount

        return (deposits)
