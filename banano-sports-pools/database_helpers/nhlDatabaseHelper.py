import pandas as pd
from database_helpers.funcs.databaseFunctions import DatabaseFunctions
from database_helpers.funcs.queryFunctions import QueryFunctions
from sqlalchemy import text

#########################################################################
########################### NHL Playoffs #########################################
#########################################################################

class NHLDatabase():

    def __init__(self, engine):
        self.engine = engine
        self.func = DatabaseFunctions()
        self.queries = QueryFunctions()

    # Gets current week for dynamic pools page
    def getCurrentNHLWeek(self, season):
        conn = self.engine.connect()

        # get max week - if doesn't exist, use final from last season
        try:
            query = f"""
                    select
                        match_round
                    from
                        nhl_games nhl
                    where
                        nhl.nhl_season = {season}
                        and nhl."date" > (NOW() - '12 HOURS')
                    order by
                        nhl."date" asc
                    limit 1;"""

            curr_week = list(conn.execute(text(query)))[0][0]
        except:
            query = f"""
                    select
                        match_round
                    from
                        nhl_games nhl
                    where
                        nhl."date" = (select max("date") from nhl_games)
                    order by
                        nhl."date" asc
                    limit 1;"""
            curr_week = list(conn.execute(text(query)))[0][0]

        conn.close()

        return(curr_week)

    # pool deposits
    def getNHLDepositData(self, match_round_inp, season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = self.queries.getDepositQuery(table="nhl_bets", week_col="match_round",
                                             season_col="nhl_season", week_inp=match_round_inp,
                                             season_inp=season_inp, min_ban=min_ban, max_ban=max_ban)
        df = pd.read_sql(query, conn)
        df["date"] = df["date"].astype(str)
        conn.close()

        return(df)

    # payouts page
    def getNHLPayouts(self, match_round_inp, season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = self.queries.getPayoutQuery(table="nhl_bets_payouts", week_col="match_round",
                                             season_col="nhl_season", week_inp=match_round_inp,
                                             season_inp=season_inp, min_ban=min_ban, max_ban=max_ban)
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # helper for history page
    def getNHLDepositDataAggregates(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getDepositAggregatesQuery(table="nhl_bets", week_col="match_round",
                                             season_col="nhl_season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        # calculate deposit aggs
        deposits = self.func.calculateDepositAggregates(df)
        return(deposits)

    # leaderboard page
    def getNHLBanAddresses(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getBANAddressesQuery(table="nhl_bets_agg", week_col="match_round",
                                             season_col="nhl_season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # leaderboard individual
    def getNHLWeekLeaderboards(self, match_round_inp, season_inp, ban_address):
        conn = self.engine.connect()
        query = self.queries.getLeaderboardsQuery(table1="nhl_bets_agg", table2= "nhl_bets_payouts",
                                                  week_col="match_round", season_col="nhl_season",
                                                  week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        # clean up cols
        rtn = self.func.cleanLeaderboardCols(df, ban_address=ban_address)

        # clean up NHL Rounds for display
        if len(match_round_inp.split(",")) > 0:
            rtn["match_round"] = "All"
        else:
            rtn["match_round"] = match_round_inp.strip('"').replace("'", "")

        return(rtn)

    # used to confirm deposit
    def getNHLGameOdds(self, match_round_inp, season_inp, team_inp):
        conn = self.engine.connect()
        query = self.queries.getGameOddsQuery(table="nhl_games", week_col="match_round",
                                             season_col="nhl_season", week_inp=match_round_inp,
                                             season_inp=season_inp, team_inp=team_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        # cleans up datetimes, disabled, etc
        df = self.func.cleanGameOdds(df)
        return(df)

    def getNHLTeams(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getTeamsQuery(table="nhl_games", week_col="match_round",
                                             season_col="nhl_season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()
        return(df)
