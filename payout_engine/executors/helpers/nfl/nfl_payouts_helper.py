import pandas as pd
from sqlalchemy import text

class NFLPayoutsHelper():
    def __init__(self, payoutsHelper):
        self.payoutsHelper = payoutsHelper

    def getCurrentNFLWeek(self, nfl_season):
        # get nfl week
        query = f"""
                select
                    coalesce(min(nfl_week), 23)
                from
                    nfl_games ng
                where
                    ng.nfl_season = {nfl_season}
                    and ng."date" > (NOW() - INTERVAL '1 DAY');"""

        with self.payoutsHelper.engine.connect() as conn:
            result = conn.execute(text(query))
            nfl_week = list(result)[0][0]

        return(nfl_week)

    def sendNFLPayouts(self, nfl_season, nfl_week):
        # get completed games
        games = pd.read_sql(f"select nfl_season, nfl_week, game_id, date, team1, team2, score1, score2 from nfl_games where nfl_season = {nfl_season} and nfl_week = {nfl_week} and date > (NOW() - INTERVAL '1 DAY') and status = 'STATUS_FINAL'", con=self.payoutsHelper.engine)

        if len(games) > 0:
            games["date"] = games["date"].dt.tz_localize("UTC").dt.tz_convert('US/Eastern')

            # get deposits
            bets = pd.read_sql(f"select * from nfl_bets where nfl_season = {nfl_season} and nfl_week = {nfl_week}", con=self.payoutsHelper.engine)
            bets_agg = bets.groupby(["nfl_season", "nfl_week", "game_id", "betting_team", "ban_address"], as_index=False)["bet_amount"].sum()
            if "bet_amount" not in bets_agg.columns:
                bets_agg["bet_amount"] = None

            # get payments to avoid double sending
            payments = pd.read_sql(f"select nfl_season, nfl_week, game_id, betting_team, ban_address, block from nfl_bets_payouts where nfl_season = {nfl_season} and nfl_week = {nfl_week}", con=self.payoutsHelper.engine)

            # join bets/games. Determine payments
            deposits = pd.merge(bets_agg, games, on=["nfl_season", "nfl_week", "game_id"])
            deposits = pd.merge(deposits, payments, on=["nfl_season", "nfl_week", "game_id", "betting_team", "ban_address"], how="left")

            rtn = self.payoutsHelper.sendPayments(deposits, "nfl_bets_payouts", "nfl_season", "nfl_week")
        else:
            print("No NFL games to payout.")
            rtn = {"ok": True, "message": "No games to payout"}
        return(rtn)
