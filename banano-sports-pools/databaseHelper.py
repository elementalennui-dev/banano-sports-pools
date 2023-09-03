import pandas as pd
import numpy as np
import datetime
import pytz
from sqlalchemy import create_engine, inspect
from config import POSTGRES_URL

class DataBaseHelper():

    def __init__(self):
        self.engine = create_engine(POSTGRES_URL)

    def writeDeposit(self, insert_df, table):
        conn = self.engine.connect()
        insert_df.to_sql(table, con=conn, if_exists="append", index=False)
        conn.close()
        return({"ok": True})

    def checkBlockExists(self, table, block):
        conn = self.engine.connect()

        inspector_gadget = inspect(self.engine)
        tables = inspector_gadget.get_table_names()
        table_exists = table in tables

        if table_exists:
            query = f"SELECT count(*) as block_exists from {table} where block = '{block}';"
            df2 = pd.read_sql(query, con=conn)
            block_exists = df2["block_exists"].values[0]

            if block_exists > 0:
                return ({"ok": False, "message": "Block already exists in database."})
            else:
                return ({"ok": True, "message": "Block is valid."})
        else:
            return ({"ok": True, "message": "Table doesn't exist in the database."})

    #########################################################################
    ########################### NFL #########################################
    #########################################################################

    def getCurrentNFLWeek(self, nfl_season):
        conn = self.engine.connect()
        query = f"""
                select
                    coalesce(min(nfl_week), 23)
                from
                    nfl_games ng
                where
                    ng.nfl_season = {nfl_season}
                    and ng."date" > now();"""

        curr_week = list(conn.execute(query))[0][0]
        conn.close()

        return(curr_week)

    # pool deposit
    def getNFLDepositData(self, nfl_week_inp, nfl_season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = f"""
                    SELECT
                        rowid,
                        block,
                        bet_amount,
                        ban_address,
                        game_id,
                        betting_team_num,
                        betting_team,
                        date,
                        timestamp,
                        nfl_week,
                        nfl_season
                    from
                        nfl_bets
                    where
                        nfl_week = {int(nfl_week_inp)}
                        and nfl_season = {int(nfl_season_inp)}
                        and bet_amount >= {min_ban}
                        and bet_amount <= {max_ban}
                        and is_active
                    order by
                        timestamp desc;
                """
        df = pd.read_sql(query, conn)
        df["game_id"] = df.game_id.astype(str)
        df["date"] = df["date"].astype(str)
        conn.close()

        return(df)

    # payouts page
    def getNFLPayouts(self, nfl_week_inp, nfl_season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = f"""
                    SELECT
                        rowid,
                        block,
                        ban_address,
                        game_id,
                        total_bet,
                        winning_pool,
                        percent_of_pool,
                        losing_pool,
                        amount_won,
                        payout,
                        nfl_week,
                        nfl_season
                    from
                        nfl_bets_payouts
                    where
                        nfl_week = {int(nfl_week_inp)}
                        and nfl_season = {int(nfl_season_inp)}
                        and payout >= {min_ban}
                        and payout <= {max_ban}
                    order by
                        rowid desc;
                """
        df = pd.read_sql(query, conn)
        df["game_id"] = df.game_id.astype(str)
        conn.close()

        return(df)

    # helper for history page
    def getNFLDepositDataAggregates(self, nfl_week_inp, nfl_season_inp):
        conn = self.engine.connect()
        query = f"SELECT * from nfl_bets where nfl_week = {int(nfl_week_inp)} and nfl_season = {int(nfl_season_inp)} and is_active;"
        df = pd.read_sql(query, conn)
        df["game_id"] = df.game_id.astype(str)
        conn.close()

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

        deposits = pd.merge(deposits, deposits_total, on="game_id")
        deposits["team1_perc"] = deposits.team1_bets / deposits.bet_amount
        deposits["team2_perc"] = deposits.team2_bets / deposits.bet_amount

        return(deposits)

    # leaderboard page
    def getNFLBanAddresses(self, nfl_week, nfl_season):
        conn = self.engine.connect()
        query = f"SELECT DISTINCT ban_address FROM nfl_bets_agg where nfl_week in ({nfl_week}) and nfl_season = {nfl_season} order by ban_address;"
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # leaderboard individual
    def getNFLWeekLeaderboards(self, nfl_week, nfl_season, ban_address):
        conn = self.engine.connect()
        query = f"""SELECT
                ma.nfl_season,
                ma.nfl_week,
                ma.game_id,
                ma.ban_address,
                coalesce(pv.betting_team, ma.betting_team) as betting_team,
                coalesce(pv.total_bet, ma.bet_amount) as bet_amount,
                coalesce(pv.is_winner, False) as is_winner,
                coalesce(pv.is_tie, False) as is_tie,
                coalesce(pv.is_refund, False) as is_refund,
                pv.winning_pool,
                pv.percent_of_pool,
                pv.losing_pool,
                pv.losing_pool > pv.winning_pool as is_upset,
                pv.amount_won,
                coalesce(pv.payout, 0) as payout,
                case when not (pv.is_winner or pv.is_tie or pv.is_refund) then -1*ma.bet_amount else 0 end as amount_lost,
                pv.block
            FROM
                nfl_bets_agg ma
                left join nfl_bets_payouts pv on ma.game_id = pv.game_id and ma.ban_address = pv.ban_address and ma.betting_team = pv.betting_team
            WHERE
                ma.nfl_week in ({nfl_week})
                and ma.nfl_season = {nfl_season}
            ORDER BY
                ma.game_id asc,
                ma.ban_address asc,
                ma.betting_team asc;
            """

        df = pd.read_sql(query, conn)
        conn.close()

        # new cols
        df["return_perc"] = (df.payout - df.bet_amount) / df.bet_amount
        df["profit"] = df.payout - df.bet_amount
        df["win_perc"] = df.is_winner.astype(int)

        if (ban_address):
            cols = ['ban_address', 'bet_amount', 'game_id', 'betting_team', 'is_winner',
                    'is_tie', 'payout', 'profit', 'return_perc', 'win_perc']
            rtn = df.loc[df.ban_address == ban_address, cols].sort_values(by="profit", ascending=False).reset_index(drop=True)
        else:
            summ = df.groupby(["ban_address"]).agg({"bet_amount": "sum", "game_id":"nunique", "is_winner": "sum", "is_tie":"sum", "payout": "sum"}).reset_index()
            summ["profit"] = summ.payout - summ.bet_amount
            summ["return_perc"] = (summ.payout - summ.bet_amount) / summ.bet_amount
            summ["win_perc"] = summ.is_winner / summ.game_id
            cols = ['ban_address', 'bet_amount', 'game_id', 'is_winner',
                    'is_tie', 'payout', 'profit', 'return_perc', 'win_perc']
            rtn = summ.loc[:, cols].sort_values(by="profit", ascending=False)

        # clean up NFL Week for display
        if len(nfl_week.split(",")) > 5:
            rtn["nfl_week"] = "All"
        elif len(nfl_week.split(",")) > 1:
            rtn["nfl_week"] = "Playoffs"
        else:
            rtn["nfl_week"] = nfl_week.strip('"').replace("'", "")

        return(rtn)


    def getNFLGameOdds(self, nfl_week, nfl_season):
        conn = self.engine.connect()
        query = f"""SELECT
                        nfl_season,
                        nfl_week,
                        game_id,
                        odds_provider,
                        team1,
                        team2,
                        team1_name,
                        team2_name,
                        team2_odds,
                        team1_odds,
                        team2_odds_wp,
                        team1_odds_wp,
                        score1,
                        score2,
                        date as gametime,
                        date_str,
                        time,
                        weekday
                    from
                        nfl_games
                    where
                        nfl_week = {nfl_week}
                        and nfl_season = {nfl_season};"""

        df = pd.read_sql(query, conn)
        df["gametime"] = df.gametime.dt.tz_localize('UTC').dt.tz_convert('US/Eastern')

        now = datetime.datetime.now(pytz.timezone("US/Eastern"))
        now = pd.Timestamp(now)
        df["started"] = df["gametime"] < now
        df["disabled"] = ["disabled" if x else "" for x in df.started]
        df["score1"] = df.score1.astype(str)
        df["score2"] = df.score2.astype(str)
        df.loc[~df.started, "score1"] = "-"
        df.loc[~df.started, "score2"] = "-"
        conn.close()

        return(df)
