import pandas as pd
from sqlalchemy import text

class NHLPayoutsHelper():
    def __init__(self, payoutsHelper):
        self.payoutsHelper = payoutsHelper

    def getCurrentNHLWeek(self, nhl_season):
        # get nhl week
        query = f"""
                select
                    match_round
                from
                    nhl_games nhl
                where
                    nhl.nhl_season = {nhl_season}
                    and nhl."date" > (NOW() - '12 HOURS')
                order by
                    nhl."date" asc
                limit 1;"""

        with self.payoutsHelper.engine.connect() as conn:
            result = conn.execute(text(query))
            match_round = list(result)[0][0]

        match_round = f"'{match_round}'"
        return(match_round)

    def sendNHLPayouts(self, nhl_season, match_round):
        # get completed games
        games = pd.read_sql(f"select nhl_season, match_round, game_id, date, team1, team2, score1, score2 from nhl_games where nhl_season = {nhl_season} and match_round = {match_round} and date > (NOW() - INTERVAL '1 DAY') and status = 'STATUS_FINAL'", con=self.payoutsHelper.engine)

        if len(games) > 0:
            games["date"] = games["date"].dt.tz_localize("UTC").dt.tz_convert('US/Eastern')

            # get deposits
            bets = pd.read_sql(f"select * from nhl_bets where nhl_season = {nhl_season} and match_round = {match_round}", con=self.payoutsHelper.engine)
            bets_agg = bets.groupby(["nhl_season", "match_round", "game_id", "betting_team", "ban_address"], as_index=False)["bet_amount"].sum()
            if "bet_amount" not in bets_agg.columns:
                bets_agg["bet_amount"] = None

            # get payments to avoid double sending
            payments = pd.read_sql(f"select nhl_season, match_round, game_id, betting_team, ban_address, block from nhl_bets_payouts where nhl_season = {nhl_season} and match_round = {match_round}", con=self.payoutsHelper.engine)

            # join bets/games. Determine payments
            deposits = pd.merge(bets_agg, games, on=["nhl_season", "match_round", "game_id"])
            deposits = pd.merge(deposits, payments, on=["nhl_season", "match_round", "game_id", "betting_team", "ban_address"], how="left")

            rtn = self.payoutsHelper.sendPayments(deposits, "nhl_bets_payouts", "nhl_season", "match_round")
        else:
            print("No NHL games to payout.")
            rtn = {"ok": True, "message": "No games to payout"}
        return(rtn)
