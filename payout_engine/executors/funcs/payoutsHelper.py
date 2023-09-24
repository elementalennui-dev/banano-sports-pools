import pandas as pd
from datetime import datetime
import pytz
import time
from bananopie import RPC, Wallet
from sqlalchemy import create_engine
from config import POSTGRES_URL, SEED

class PayoutsHelper():
    def __init__(self):
        self.engine = create_engine(POSTGRES_URL)
        self.rpc = RPC("https://booster.dev-ptera.com/banano-rpc", legacy=True)
        self.my_account = Wallet(self.rpc, seed=SEED, index=0, try_work=True)

    def receiveFunds(self):
        # get account
        bal = self.my_account.get_balance()
        print(bal)

        #receive funds
        receive_more = True
        while receive_more:
            # receive and check balance
            self.my_account.receive_all(threshold=0)
            bal = self.my_account.get_balance()
            print(bal)

            # pending transactions
            pend_dec = float(bal["pending_decimal"])
            rec_dec = float(bal["receivable_decimal"])

            # loop until no more transactions to receive
            if (pend_dec == 0) & (rec_dec == 0):
                receive_more = False
            else:
                time.sleep(1) # sleep before receiving again

        return({"ok": True})

    def sendPayments(self, deposits, transactions_table, season_col, week_col):
        # remove any already paid out games for that week
        paid_games = deposits.loc[pd.notnull(deposits.block), "game_id"].unique()
        print(f'Paid out games: {paid_games}')
        deposits = deposits.loc[~deposits.game_id.isin(paid_games)]
        deposits.drop(columns="block", inplace=True)
        print(f'Games to pay: {deposits.game_id.unique()}')

        # only payout completed games
        deposits = deposits.loc[deposits.date < datetime.now(pytz.timezone("US/Eastern"))]

        # determine winners/refunds
        deposits["is_winner"] = False
        deposits["is_refund"] = False
        deposits["is_tie"] = False

        deposits.loc[(deposits.score2 > deposits.score1) & (deposits["betting_team"] == deposits.team2), "is_winner"] = True
        deposits.loc[(deposits.score1 > deposits.score2) & (deposits["betting_team"] == deposits.team1), "is_winner"] = True
        deposits.loc[(deposits.score2 == deposits.score1), "is_tie"] = True

        # aggregate total pools
        rows = []

        # loop through each game to get a pool agg
        for game in deposits.game_id.unique():
            sub = deposits.loc[(deposits.game_id == game)]

            data = {}
            data["game_id"] = game
            data["losing_pool"] = sub.loc[~(sub.is_winner | sub.is_tie)]["bet_amount"].sum()
            data["winning_pool"] = sub.loc[(sub.is_winner | sub.is_tie)]["bet_amount"].sum()

            rows.append(data)

        # pools df
        pools = pd.DataFrame(rows, columns=["game_id", "losing_pool", "winning_pool"]).fillna(0)
        deposits = pd.merge(deposits, pools, on="game_id")

        # lost bet, but nobody bet on the winner (refund)
        deposits.loc[(deposits.score2 > deposits.score1) & (deposits["betting_team"] == deposits.team1) & (deposits.winning_pool == 0), "is_refund"] = True
        deposits.loc[(deposits.score1 > deposits.score2) & (deposits["betting_team"] == deposits.team2) & (deposits.winning_pool == 0), "is_refund"] = True

        # transactions to send
        transactions = deposits.loc[(deposits.is_winner) | (deposits.is_refund) | (deposits.is_tie), [season_col, week_col, "game_id", "ban_address", "bet_amount", "betting_team", "winning_pool", "losing_pool", "is_winner", "is_refund", "is_tie"]]

        # round to 2 decimal places
        transactions["percent_of_pool"] = transactions.bet_amount / transactions.winning_pool
        transactions["amount_won"] = round(transactions.percent_of_pool * transactions.losing_pool, 2)
        transactions["payout"] = round(transactions.amount_won + transactions.bet_amount, 2)

        # refunds are special (losers but nobody bet on winner)
        transactions.loc[transactions.is_refund, "percent_of_pool"] = 0
        transactions.loc[transactions.is_refund, "amount_won"] = 0
        transactions.loc[transactions.is_refund, "payout"] = transactions.loc[transactions.is_refund, "bet_amount"]

        # get blocks for each transaction
        blocks = []

        # use bananopie to send the transaction
        for indx, row in transactions.iterrows():
            payout = "{:.2f}".format(row["payout"])
            print(row["ban_address"], payout)

            resp = self.my_account.send(row["ban_address"], payout)
            print(resp)
            blocks.append(resp["hash"])
            time.sleep(1)

        # store blocks
        transactions["block"] = blocks

        # match db columns
        transactions.rename(columns={"bet_amount": "total_bet"}, inplace=True)

        # save outputs
        if len(transactions) > 0:
            transactions.to_sql(transactions_table, con=self.engine, index=False, if_exists="append", method="multi")
        else:
            print("No transactions")

        return({"ok": True})
