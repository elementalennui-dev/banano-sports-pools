import pandas as pd
from database_helpers.funcs.databaseFunctions import DatabaseFunctions
from database_helpers.funcs.queryFunctions import QueryFunctions
from sqlalchemy import text

#########################################################################
########################### MLB Playoffs #########################################
#########################################################################

class MLBDatabase():

    def __init__(self, engine):
        self.engine = engine
        self.func = DatabaseFunctions()
        self.queries = QueryFunctions()

    # Gets current week for dynamic pools page
    def getCurrentMLBWeek(self, season):
        conn = self.engine.connect()

        # get max week - if doesn't exist, use final from last season
        try:
            query = f"""
                    select
                        match_round
                    from
                        mlb_games mlb
                    where
                        mlb.mlb_season = {season}
                        and mlb."date" > (NOW() - INTERVAL '1 DAY')
                    order by
                        mlb."date" asc
                    limit 1;"""

            curr_week = list(conn.execute(text(query)))[0][0]
        except:
            query = f"""
                    select
                        match_round
                    from
                        mlb_games mlb
                    where
                        mlb."date" = (select max("date") from mlb_games)
                    order by
                        mlb."date" asc
                    limit 1;"""

            curr_week = list(conn.execute(text(query)))[0][0]

        conn.close()

        return(curr_week)

        conn.close()

        return(curr_week)

    # pool deposits
    def getMLBDepositData(self, match_round_inp, season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = self.queries.getDepositQuery(table="mlb_bets", week_col="match_round",
                                             season_col="mlb_season", week_inp=match_round_inp,
                                             season_inp=season_inp, min_ban=min_ban, max_ban=max_ban)
        df = pd.read_sql(query, conn)
        df["date"] = df["date"].astype(str)
        conn.close()

        return(df)

    # payouts page
    def getMLBPayouts(self, match_round_inp, season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = self.queries.getPayoutQuery(table="mlb_bets_payouts", week_col="match_round",
                                             season_col="mlb_season", week_inp=match_round_inp,
                                             season_inp=season_inp, min_ban=min_ban, max_ban=max_ban)
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # helper for history page
    def getMLBDepositDataAggregates(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getDepositAggregatesQuery(table="mlb_bets", week_col="match_round",
                                             season_col="mlb_season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        # calculate deposit aggs
        deposits = self.func.calculateDepositAggregates(df)
        return(deposits)

    # leaderboard page
    def getMLBBanAddresses(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getBANAddressesQuery(table="mlb_bets_agg", week_col="match_round",
                                             season_col="mlb_season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # leaderboard individual
    def getMLBWeekLeaderboards(self, match_round_inp, season_inp, ban_address):
        conn = self.engine.connect()
        query = self.queries.getLeaderboardsQuery(table1="mlb_bets_agg", table2= "mlb_bets_payouts",
                                                  week_col="match_round", season_col="mlb_season",
                                                  week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        # clean up cols
        rtn = self.func.cleanLeaderboardCols(df, ban_address=ban_address)

        # clean up MLB Rounds for display
        if len(match_round_inp.split(",")) > 0:
            rtn["match_round"] = "All"
        else:
            rtn["match_round"] = match_round_inp.strip('"').replace("'", "")

        return(rtn)

    # used to confirm deposit
    def getMLBGameOdds(self, match_round_inp, season_inp, team_inp):
        conn = self.engine.connect()
        query = self.queries.getGameOddsQuery(table="mlb_games", week_col="match_round",
                                             season_col="mlb_season", week_inp=match_round_inp,
                                             season_inp=season_inp, team_inp=team_inp)

        df = pd.read_sql(query, conn)
        conn.close()

        # cleans up datetimes, disabled, etc
        df = self.func.cleanGameOdds(df)
        return(df)

    def getMLBTeams(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getTeamsQuery(table="mlb_games", week_col="match_round",
                                             season_col="mlb_season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()
        return(df)
