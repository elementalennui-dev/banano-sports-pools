import pandas as pd
from database_helpers.funcs.databaseFunctions import DatabaseFunctions
from database_helpers.funcs.queryFunctions import QueryFunctions

#########################################################################
########################### NFL #########################################
#########################################################################

class NFLDatabase():

    def __init__(self, engine):
        self.engine = engine
        self.func = DatabaseFunctions()
        self.queries = QueryFunctions()

    # Gets current week for dynamic pools page
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

    # pool deposits
    def getNFLDepositData(self, nfl_week_inp, nfl_season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = self.queries.getDepositQuery(table="nfl_bets", week_col="nfl_week",
                                        season_col="nfl_season", week_inp=nfl_week_inp,
                                        season_inp=nfl_season_inp, min_ban=min_ban, max_ban=max_ban)
        df = pd.read_sql(query, conn)
        df["date"] = df["date"].astype(str)
        conn.close()

        return(df)

    # payouts page
    def getNFLPayouts(self, nfl_week_inp, nfl_season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = self.queries.getPayoutQuery(table="nfl_bets_payouts", week_col="nfl_week",
                                        season_col="nfl_season", week_inp=nfl_week_inp,
                                        season_inp=nfl_season_inp, min_ban=min_ban, max_ban=max_ban)
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # helper for history page
    def getNFLDepositDataAggregates(self, nfl_week_inp, nfl_season_inp):
        conn = self.engine.connect()
        query = self.queries.getDepositAggregatesQuery(table="nfl_bets", week_col="nfl_week",
                                        season_col="nfl_season", week_inp=nfl_week_inp, season_inp=nfl_season_inp)
        df = pd.read_sql(query, conn)
        df["game_id"] = df.game_id.astype(str)
        conn.close()

        # calculate deposit aggs
        deposits = self.func.calculateDepositAggregates(df)

        return(deposits)

    # leaderboard page
    def getNFLBanAddresses(self, nfl_week_inp, nfl_season_inp):
        conn = self.engine.connect()
        query = self.queries.getBANAddressesQuery(table="nfl_bets_agg", week_col="nfl_week",
                                        season_col="nfl_season", week_inp=nfl_week_inp, season_inp=nfl_season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # leaderboard individual
    def getNFLWeekLeaderboards(self, nfl_week_inp, nfl_season_inp, ban_address):
        conn = self.engine.connect()
        query = self.queries.getLeaderboardsQuery(table1="nfl_bets_agg", table2= "nfl_bets_payouts",
                                            week_col="nfl_week", season_col="nfl_season",
                                            week_inp=nfl_week_inp, season_inp=nfl_season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        # clean up cols
        rtn = self.func.cleanLeaderboardCols(df, ban_address=ban_address)

        # clean up NFL Week for display
        if len(nfl_week_inp.split(",")) > 5:
            rtn["nfl_week"] = "All"
        elif len(nfl_week_inp.split(",")) > 1:
            rtn["nfl_week"] = "Playoffs"
        else:
            rtn["nfl_week"] = nfl_week_inp.strip('"').replace("'", "")

        return(rtn)

    # used to confirm deposit
    def getNFLGameOdds(self, nfl_week_inp, nfl_season_inp):
        conn = self.engine.connect()
        query = self.queries.getGameOddsQuery(table="nfl_games", week_col="nfl_week",
                                             season_col="nfl_season", week_inp=nfl_week_inp, season_inp=nfl_season_inp)

        df = pd.read_sql(query, conn)
        conn.close()

        # cleans up datetimes, disabled, etc
        df = self.func.cleanGameOdds(df)
        return(df)
