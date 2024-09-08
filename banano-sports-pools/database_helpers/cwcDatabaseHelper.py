import pandas as pd
from database_helpers.funcs.databaseFunctions import DatabaseFunctions
from database_helpers.funcs.queryFunctions import QueryFunctions
from sqlalchemy import text

#########################################################################
########################### RUGBY WORLD CUP #########################################
#########################################################################

class CWCDatabase():

    def __init__(self, engine):
        self.engine = engine
        self.func = DatabaseFunctions()
        self.queries = QueryFunctions()

    # Gets current week for dynamic pools page
    def getCurrentCWCWeek(self, season):
        conn = self.engine.connect()

        # get max week - if doesn't exist, use final from last season
        try:
            query = f"""
                    select
                        match_round
                    from
                        cricket_world_cup_games cwc
                    where
                        cwc.season = {season}
                        and cwc."date" > (NOW() - INTERVAL '1 DAY')
                    order by
                        cwc."date" asc
                    limit 1;"""

            curr_week = list(conn.execute(text(query)))[0][0]
        except:
            query = f"""
                    select
                        match_round
                    from
                        cricket_world_cup_games cwc
                    where
                        cwc."date" = (select max("date") from cricket_world_cup_games)
                    order by
                        cwc."date" asc
                    limit 1;"""

            curr_week = list(conn.execute(text(query)))[0][0]

        conn.close()

        return(curr_week)

    # pool deposits
    def getCWCDepositData(self, match_round_inp, season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = self.queries.getDepositQuery(table="cricket_world_cup_bets", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp,
                                             season_inp=season_inp, min_ban=min_ban, max_ban=max_ban)
        df = pd.read_sql(query, conn)
        df["date"] = df["date"].astype(str)
        conn.close()

        return(df)

    # payouts page
    def getCWCPayouts(self, match_round_inp, season_inp, min_ban, max_ban):
        conn = self.engine.connect()
        query = self.queries.getPayoutQuery(table="cricket_world_cup_bets_payouts", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp,
                                             season_inp=season_inp, min_ban=min_ban, max_ban=max_ban)
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # helper for history page
    def getCWCDepositDataAggregates(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getDepositAggregatesQuery(table="cricket_world_cup_bets", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        # calculate deposit aggs
        deposits = self.func.calculateDepositAggregates(df)
        return(deposits)

    # leaderboard page
    def getCWCBanAddresses(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getBANAddressesQuery(table="cricket_world_cup_bets_agg", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        return(df)

    # leaderboard individual
    def getCWCWeekLeaderboards(self, match_round_inp, season_inp, ban_address):
        conn = self.engine.connect()
        query = self.queries.getLeaderboardsQuery(table1="cricket_world_cup_bets_agg", table2= "cricket_world_cup_bets_payouts",
                                                  week_col="match_round", season_col="season",
                                                  week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()

        # clean up cols
        rtn = self.func.cleanLeaderboardCols(df, ban_address=ban_address)

        # clean up CWC Rounds for display
        if len(match_round_inp.split(",")) > 0:
            rtn["match_round"] = "All"
        else:
            rtn["match_round"] = match_round_inp.strip('"').replace("'", "")

        return(rtn)

    # used to confirm deposit
    def getCWCGameOdds(self, match_round_inp, season_inp, team_inp):
        conn = self.engine.connect()
        query = self.queries.getGameOddsQuery(table="cricket_world_cup_games", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp,
                                             season_inp=season_inp, team_inp=team_inp)

        df = pd.read_sql(query, conn)
        conn.close()

        # cleans up datetimes, disabled, etc
        df = self.func.cleanGameOdds(df)
        return(df)

    def getCWCTeams(self, match_round_inp, season_inp):
        conn = self.engine.connect()
        query = self.queries.getTeamsQuery(table="cricket_world_cup_games", week_col="match_round",
                                             season_col="season", week_inp=match_round_inp, season_inp=season_inp)
        df = pd.read_sql(query, conn)
        conn.close()
        return(df)
