import pandas as pd

class RWCPayoutsHelper():
    def __init__(self, payoutsHelper):
        self.payoutsHelper = payoutsHelper

    def getCurrentRWCWeek(self, season):
        # get rwc week
        query = f"""
                select
                    coalesce(min(match_round), 'group')
                from
                    rugby_world_cup_games rwc
                where
                    rwc.season = {season}
                    and rwc."date" > (NOW() - INTERVAL '1 DAY');"""

        match_round = list(self.payoutsHelper.engine.execute(query))[0][0]
        match_round = f"'{match_round}'"
        return(match_round)

    def sendRWCPayouts(self, season, match_round):
        # get completed games
        games = pd.read_sql(f"select season, match_round, game_id, date, team1, team2, score1, score2 from rugby_world_cup_games where season = {season} and match_round = {match_round} and date > (NOW() - INTERVAL '1 DAY') and status = 'STATUS_FINAL';", con=self.payoutsHelper.engine)

        if len(games) > 0:
            games["date"] = games["date"].dt.tz_localize("UTC").dt.tz_convert('US/Eastern')

            # get deposits
            bets = pd.read_sql(f"select * from rugby_world_cup_bets where season = {season} and match_round = {match_round}", con=self.payoutsHelper.engine)
            bets_agg = bets.groupby(["season", "match_round", "game_id", "betting_team", "ban_address"], as_index=False)["bet_amount"].sum()
            if "bet_amount" not in bets_agg.columns:
                bets_agg["bet_amount"] = None

            # get payments to avoid double sending
            payments = pd.read_sql(f"select season, match_round, game_id, betting_team, ban_address, block from rugby_world_cup_bets_payouts where season = {season} and match_round = {match_round}", con=self.payoutsHelper.engine)

            # join bets/games. Determine payments
            deposits = pd.merge(bets_agg, games, on=["season", "match_round", "game_id"])
            deposits = pd.merge(deposits, payments, on=["season", "match_round", "game_id", "betting_team", "ban_address"], how="left")

            rtn = self.payoutsHelper.sendPayments(deposits, "rugby_world_cup_bets_payouts", "season", "match_round")
        else:
            print("No RWC games to payout.")
            rtn = {"ok": True, "message": "No games to payout"}
        return(rtn)
