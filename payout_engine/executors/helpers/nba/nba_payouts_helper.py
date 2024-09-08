import pandas as pd
from sqlalchemy import text

class NBAPayoutsHelper():
    def __init__(self, payoutsHelper):
        self.payoutsHelper = payoutsHelper

    def getCurrentNBAWeek(self, nba_season):
        # get nba week
        query = f"""
                select
                    match_round
                from
                    nba_games nba
                where
                    nba.nba_season = {nba_season}
                    and nba."date" > (NOW() - INTERVAL '12 HOURS')
                order by
                    nba."date" asc
                limit 1;"""

        with self.payoutsHelper.engine.connect() as conn:
            result = conn.execute(text(query))
            match_round = list(result)[0][0]

        match_round = f"'{match_round}'"
        return(match_round)

    def sendNBAPayouts(self, nba_season, match_round):
        # get completed games
        games = pd.read_sql(f"select nba_season, match_round, game_id, date, team1, team2, score1, score2 from nba_games where nba_season = {nba_season} and match_round = {match_round} and date > (NOW() - INTERVAL '1 DAY') and status = 'STATUS_FINAL'", con=self.payoutsHelper.engine)

        if len(games) > 0:
            games["date"] = games["date"].dt.tz_localize("UTC").dt.tz_convert('US/Eastern')

            # get deposits
            bets = pd.read_sql(f"select * from nba_bets where nba_season = {nba_season} and match_round = {match_round}", con=self.payoutsHelper.engine)
            bets_agg = bets.groupby(["nba_season", "match_round", "game_id", "betting_team", "ban_address"], as_index=False)["bet_amount"].sum()
            if "bet_amount" not in bets_agg.columns:
                bets_agg["bet_amount"] = None

            # get payments to avoid double sending
            payments = pd.read_sql(f"select nba_season, match_round, game_id, betting_team, ban_address, block from nba_bets_payouts where nba_season = {nba_season} and match_round = {match_round}", con=self.payoutsHelper.engine)

            # join bets/games. Determine payments
            deposits = pd.merge(bets_agg, games, on=["nba_season", "match_round", "game_id"])
            deposits = pd.merge(deposits, payments, on=["nba_season", "match_round", "game_id", "betting_team", "ban_address"], how="left")

            rtn = self.payoutsHelper.sendPayments(deposits, "nba_bets_payouts", "nba_season", "match_round")
        else:
            print("No NBA games to payout.")
            rtn = {"ok": True, "message": "No games to payout"}
        return(rtn)
