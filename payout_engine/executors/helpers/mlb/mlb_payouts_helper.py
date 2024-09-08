import pandas as pd
from sqlalchemy import text

class MLBPayoutsHelper():
    def __init__(self, payoutsHelper):
        self.payoutsHelper = payoutsHelper

    def getCurrentMLBWeek(self, mlb_season):
        # get mlb week
        query = f"""
                select
                    match_round
                from
                    mlb_games mlb
                where
                    mlb.mlb_season = {mlb_season}
                    and mlb."date" > (NOW() - INTERVAL '1 DAY')
                order by
                    mlb."date" asc
                limit 1;"""

        with self.payoutsHelper.engine.connect() as conn:
            result = conn.execute(text(query))
            match_round = list(result)[0][0]

        match_round = f"'{match_round}'"
        return(match_round)

    def sendMLBPayouts(self, mlb_season, match_round):
        # get completed games
        games = pd.read_sql(f"select mlb_season, match_round, game_id, date, team1, team2, score1, score2 from mlb_games where mlb_season = {mlb_season} and match_round = {match_round} and date > (NOW() - INTERVAL '1 DAY') and status = 'STATUS_FINAL'", con=self.payoutsHelper.engine)

        if len(games) > 0:
            games["date"] = games["date"].dt.tz_localize("UTC").dt.tz_convert('US/Eastern')

            # get deposits
            bets = pd.read_sql(f"select * from mlb_bets where mlb_season = {mlb_season} and match_round = {match_round}", con=self.payoutsHelper.engine)
            bets_agg = bets.groupby(["mlb_season", "match_round", "game_id", "betting_team", "ban_address"], as_index=False)["bet_amount"].sum()
            if "bet_amount" not in bets_agg.columns:
                bets_agg["bet_amount"] = None

            # get payments to avoid double sending
            payments = pd.read_sql(f"select mlb_season, match_round, game_id, betting_team, ban_address, block from mlb_bets_payouts where mlb_season = {mlb_season} and match_round = {match_round}", con=self.payoutsHelper.engine)

            # join bets/games. Determine payments
            deposits = pd.merge(bets_agg, games, on=["mlb_season", "match_round", "game_id"])
            deposits = pd.merge(deposits, payments, on=["mlb_season", "match_round", "game_id", "betting_team", "ban_address"], how="left")

            rtn = self.payoutsHelper.sendPayments(deposits, "mlb_bets_payouts", "mlb_season", "match_round")
        else:
            print("No MLB games to payout.")
            rtn = {"ok": True, "message": "No games to payout"}
        return(rtn)
