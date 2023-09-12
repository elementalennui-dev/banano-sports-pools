import pandas as pd
from database_helpers.funcs.databaseFunctions import DatabaseFunctions
from database_helpers.funcs.queryFunctions import QueryFunctions

#########################################################################
########################### RUGBY WORLD CUP #########################################
#########################################################################

class RWCDatabase():

    def __init__(self, engine):
        self.engine = engine
        self.func = DatabaseFunctions()
        self.queries = QueryFunctions()

    # Gets current week for dynamic pools page
    def getCurrentRWCWeek(self, season):
        conn = self.engine.connect()
        query = f"""
                select
                    coalesce(min(match_round), 'group')
                from
                    rugby_world_cup_games rwc
                where
                    rwc.season = {season}
                    and rwc."date" > now();"""

        curr_week = list(conn.execute(query))[0][0]
        conn.close()

        return(curr_week)

    # pool deposits
    def getRWCDepositData(self, match_round_inp, season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = self.queries.getDepositQuery(table="rugby_world_cup_bets", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp,
                                             season_inp=season_inp, min_ban=min_ban, max_ban=max_ban)
        df = pd.read_sql(query, conn)
        df["date"] = df["date"].astype(str)
        conn.close()

        return(df)

    # payouts page
    def getRWCPayouts(self, match_round_inp, season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = self.queries.getPayoutQuery(table="rugby_world_cup_bets_payouts", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp,
                                             season_inp=season_inp, min_ban=min_ban, max_ban=max_ban)
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # helper for history page
    def getRWCDepositDataAggregates(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getDepositAggregatesQuery(table="rugby_world_cup_bets", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        # calculate deposit aggs
        deposits = self.func.calculateDepositAggregates(df)
        return(deposits)

    # leaderboard page
    def getRWCBanAddresses(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getBANAddressesQuery(table="rugby_world_cup_bets_agg", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # leaderboard individual
    def getRWCWeekLeaderboards(self, match_round_inp, season_inp, ban_address):
        conn = self.engine.connect()
        query = self.queries.getLeaderboardsQuery(table1="rugby_world_cup_bets_agg", table2= "rugby_world_cup_bets_payouts",
                                                  week_col="match_round", season_col="season",
                                                  week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        # clean up cols
        rtn = self.func.cleanLeaderboardCols(df, ban_address=ban_address)

        # clean up RWC Rounds for display
        if len(match_round_inp.split(",")) > 0:
            rtn["match_round"] = "All"
        else:
            rtn["match_round"] = match_round_inp.strip('"').replace("'", "")

        return(rtn)

    # used to confirm deposit
    def getRWCGameOdds(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getGameOddsQuery(table="rugby_world_cup_games", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp, season_inp=season_inp)

        df = pd.read_sql(query, conn)
        conn.close()

        # cleans up datetimes, disabled, etc
        df = self.func.cleanGameOdds(df)
        return(df)
