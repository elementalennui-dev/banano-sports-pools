import pandas as pd
import datetime
import pytz
import requests
import numpy as np
from bananopie import RPC, Wallet
from sqlalchemy import create_engine, inspect
from config import POSTGRES_URL, SEED

# rpc
rpc = RPC("https://kaliumapi.appditto.com/api")

# connect to account
my_account = Wallet(rpc, seed=SEED, index=0)

#get address of self
print(my_account.get_address())

#receive funds
my_account.receive_all()

#get balance of self
print(my_account.get_balance())

# db conn
engine = create_engine(POSTGRES_URL)
conn = engine.connect()

# get season
now = datetime.datetime.now()
nfl_season = now.year if now.month >= 3 else now.year - 1

# get nfl week
query = f"""
        select
            coalesce(min(nfl_week), 23)
        from
            nfl_games ng
        where
            ng.nfl_season = {nfl_season}
            and ng."date" > now();"""

nfl_week = list(conn.execute(query))[0][0]

# get games
games = pd.read_sql(f"select nfl_season, nfl_week, game_id, date, team1, team2, score1, score2 from nfl_games where nfl_season = {nfl_season} and nfl_week = {nfl_week}", con=conn)
games["date"] = games["date"].dt.tz_localize("UTC").dt.tz_convert('US/Eastern')

# get deposits
bets = pd.read_sql(f"select * from nfl_bets where nfl_season = {nfl_season} and nfl_week = {nfl_week}", con=conn)
bets_agg = bets.groupby(["nfl_season", "nfl_week", "game_id", "betting_team", "ban_address"], as_index=False)["bet_amount"].sum()
if "bet_amount" not in bets_agg.columns:
    bets_agg["bet_amount"] = None

# get payments to avoid double sending
payments = pd.read_sql(f"select nfl_season, nfl_week, game_id, betting_team, ban_address, block from nfl_bets_payouts where nfl_season = {nfl_season} and nfl_week = {nfl_week}", con=conn)

# join bets/games. Determine payments
full = pd.merge(bets_agg, games, on=["nfl_season", "nfl_week", "game_id"])
full = pd.merge(full, payments, on=["nfl_season", "nfl_week", "game_id", "betting_team", "ban_address"], how="left")

# null blocks, only payout completed games
full = full.loc[(pd.isnull(full.block)) & (full.date < datetime.datetime.now(pytz.timezone("US/Eastern")))]
full.drop(columns="block", inplace=True)

# determine winners/refunds
full["is_winner"] = False
full["is_refund"] = False
full["is_tie"] = False

full.loc[(full.score2 > full.score1) & (full["betting_team"] == full.team2), "is_winner"] = True
full.loc[(full.score1 > full.score2) & (full["betting_team"] == full.team1), "is_winner"] = True
full.loc[(full.score2 == full.score1), "is_tie"] = True

# aggregate total pools
rows = []

# loop through each game to get a pool agg
for game in full.game_id.unique():
    sub = full.loc[(full.game_id == game)]

    data = {}
    data["game_id"] = game
    data["losing_pool"] = sub.loc[~(sub.is_winner | sub.is_tie)]["bet_amount"].sum()
    data["winning_pool"] = sub.loc[(sub.is_winner | sub.is_tie)]["bet_amount"].sum()

    rows.append(data)

# pools df
pools = pd.DataFrame(rows, columns=["game_id", "losing_pool", "winning_pool"]).fillna(0)
full = pd.merge(full, pools, on="game_id")

# lost bet, but nobody bet on the winner (refund)
full.loc[(full.score2 > full.score1) & (full["betting_team"] == full.team1) & (full.winning_pool == 0), "is_refund"] = True
full.loc[(full.score1 > full.score2) & (full["betting_team"] == full.team2) & (full.winning_pool == 0), "is_refund"] = True

# transactions to send
transactions = full.loc[(full.is_winner) | (full.is_refund) | (full.is_tie), ["nfl_week", "game_id", "ban_address", "bet_amount", "betting_team", "winning_pool", "losing_pool", "is_winner", "is_refund", "is_tie"]]

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
    resp = my_account.send(row["ban_address"], row["payout"])
    print(resp)
    blocks.append(resp["hash"])

# store blocks
transactions["block"] = blocks

# save outputs
if len(transactions) > 0:
    transactions.to_sql("nfl_bets_payouts", con=engine, index=False, if_exists="append", method="multi")
else:
    print("No transactions")

# close db
conn.close()
