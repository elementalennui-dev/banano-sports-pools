import pandas as pd
import datetime
import pytz
import time
from bananopie import RPC, Wallet
from sqlalchemy import create_engine
from config import POSTGRES_URL, SEED

# rpc
rpc = RPC("https://kaliumapi.appditto.com/api")

# connect to account
my_account = Wallet(rpc, seed=SEED, index=0, try_work=True)

#get address of self
print(my_account.get_address())
bal = my_account.get_balance()
print(bal)

#receive funds
receive_more = True
while receive_more:
    # receive and check balance
    my_account.receive_all(threshold=0)
    bal = my_account.get_balance()
    print(bal)

    # pending transactions
    pend_dec = float(bal["pending_decimal"])
    rec_dec = float(bal["receivable_decimal"])

    # loop until no more transactions to receive
    if (pend_dec == 0) & (rec_dec == 0):
        receive_more = False
    else:
        time.sleep(2) # sleep before receiving again

# db conn
engine = create_engine(POSTGRES_URL)
conn = engine.connect()

# get season
now = datetime.datetime.now()
season = now.year

# get rwc week
query = f"""
        select
            coalesce(min(match_round), 'group')
        from
            rugby_world_cup_games rwc
        where
            rwc.season = {season}
            and rwc."date" > (NOW() - INTERVAL '1 DAY');"""

match_round = list(conn.execute(query))[0][0]
match_round = f"'{match_round}'"

# get games
games = pd.read_sql(f"select season, match_round, game_id, date, team1, team2, score1, score2 from rugby_world_cup_games where season = {season} and match_round = {match_round}", con=conn)
games["date"] = games["date"].dt.tz_localize("UTC").dt.tz_convert('US/Eastern')

# get deposits
bets = pd.read_sql(f"select * from rugby_world_cup_bets where season = {season} and match_round = {match_round}", con=conn)
bets_agg = bets.groupby(["season", "match_round", "game_id", "betting_team", "ban_address"], as_index=False)["bet_amount"].sum()
if "bet_amount" not in bets_agg.columns:
    bets_agg["bet_amount"] = None

# get payments to avoid double sending
payments = pd.read_sql(f"select season, match_round, game_id, betting_team, ban_address, block from rugby_world_cup_bets_payouts where season = {season} and match_round = {match_round}", con=conn)

# join bets/games. Determine payments
full = pd.merge(bets_agg, games, on=["season", "match_round", "game_id"])
full = pd.merge(full, payments, on=["season", "match_round", "game_id", "betting_team", "ban_address"], how="left")

# remove any already paid out games for that week
paid_games = full.loc[pd.notnull(full.block), "game_id"].unique()
print(paid_games)
full = full.loc[~full.game_id.isin(paid_games)]
full.drop(columns="block", inplace=True)

# only payout completed games
full = full.loc[full.date < datetime.datetime.now(pytz.timezone("US/Eastern"))]

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
transactions = full.loc[(full.is_winner) | (full.is_refund) | (full.is_tie), ["season", "match_round", "game_id", "ban_address", "bet_amount", "betting_team", "winning_pool", "losing_pool", "is_winner", "is_refund", "is_tie"]]

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
    print(row["ban_address"], payout, type(row["payout"]))

    resp = my_account.send(row["ban_address"], payout)
    print(resp)
    blocks.append(resp["hash"])
    time.sleep(1)

# store blocks
transactions["block"] = blocks

# match db columns
transactions.rename(columns={"bet_amount": "total_bet"}, inplace=True)

# save outputs
if len(transactions) > 0:
    transactions.to_sql("rugby_world_cup_bets_payouts", con=engine, index=False, if_exists="append", method="multi")
else:
    print("No transactions")

# close db
conn.close()
engine.dispose()
