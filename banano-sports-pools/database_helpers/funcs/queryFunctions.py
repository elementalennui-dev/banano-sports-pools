import pandas as pd
import numpy as np
import datetime
import pytz

class QueryFunctions():

    def __init__(self):
        pass

    #########################################################################
    ########################### QUERIES #####################################
    #########################################################################

    def getDepositQuery(self, table, week_col, season_col, week_inp, season_inp, min_ban, max_ban):
        query = f"""
                    SELECT
                        rowid,
                        block,
                        bet_amount,
                        ban_address,
                        game_id,
                        betting_team_num,
                        betting_team,
                        date,
                        timestamp,
                        {week_col},
                        {season_col}
                    from
                        {table}
                    where
                        {week_col} = '{week_inp}'
                        and {season_col} = {season_inp}
                        and bet_amount >= {min_ban}
                        and bet_amount <= {max_ban}
                        and is_active
                    order by
                        timestamp desc;
                """
        return(query)

    def getTeamsQuery(self, table, week_col, season_col, week_inp, season_inp):
        query = f"""
                select distinct
                    *
                from
                    (
                        select
                            team1_name as team_name
                        from
                            {table}
                        where
                            {week_col} = '{week_inp}'
                            and {season_col} = {season_inp}

                        union all

                        select
                            team2_name as team_name
                        from
                            {table}
                        where
                            {week_col} = '{week_inp}'
                            and {season_col} = {season_inp}
                        ) as x
                    order by
                        x.team_name asc;
                """
        return(query)

    def getPayoutQuery(self, table, week_col, season_col, week_inp, season_inp, min_ban, max_ban):
        query = f"""
                    SELECT
                        rowid,
                        block,
                        ban_address,
                        game_id,
                        total_bet,
                        winning_pool,
                        percent_of_pool,
                        losing_pool,
                        amount_won,
                        payout,
                        {week_col},
                        {season_col}
                    from
                        {table}
                    where
                        {week_col} = '{week_inp}'
                        and {season_col} = {season_inp}
                        and payout >= {min_ban}
                        and payout <= {max_ban}
                    order by
                        rowid desc;
                """
        return(query)

    def getDepositAggregatesQuery(self, table, week_col, season_col, week_inp, season_inp):
        query = f"""SELECT
                        *
                    from
                        {table}
                    where
                        {week_col} = '{week_inp}'
                        and {season_col} = {season_inp}
                        and is_active;"""
        return(query)

    def getBANAddressesQuery(self, table, week_col, season_col, week_inp, season_inp):
        query = f"""SELECT DISTINCT
                        ban_address
                    FROM
                        {table}
                    where
                        {week_col} in ({week_inp})
                        and {season_col} = {season_inp}
                    order by ban_address;"""

        return(query)

    def getLeaderboardsQuery(self, table1, table2, week_col, season_col, week_inp, season_inp):
        query = f"""SELECT
                ma.{season_col},
                ma.{week_col},
                ma.game_id,
                ma.ban_address,
                coalesce(pv.betting_team, ma.betting_team) as betting_team,
                coalesce(pv.total_bet, ma.bet_amount) as bet_amount,
                coalesce(pv.is_winner, False) as is_winner,
                coalesce(pv.is_tie, False) as is_tie,
                coalesce(pv.is_refund, False) as is_refund,
                pv.winning_pool,
                pv.percent_of_pool,
                pv.losing_pool,
                pv.losing_pool > pv.winning_pool as is_upset,
                pv.amount_won,
                coalesce(pv.payout, 0) as payout,
                case when not (pv.is_winner or pv.is_tie or pv.is_refund) then -1*ma.bet_amount else 0 end as amount_lost,
                pv.block
            FROM
                {table1} ma
                left join {table2} pv on ma.game_id = pv.game_id and ma.ban_address = pv.ban_address and ma.betting_team = pv.betting_team
            WHERE
                ma.{week_col} in ({week_inp})
                and ma.{season_col} = {season_inp}
            ORDER BY
                ma.game_id asc,
                ma.ban_address asc,
                ma.betting_team asc;
            """
        return(query)

    def getGameOddsQuery(self, table, week_col, season_col, week_inp, season_inp, team_inp):
        # check team
        if team_inp == 'All':
            team_clause = "1=1"
        else:
            team_clause = f"(team1_name = '{team_inp}' OR team2_name = '{team_inp}')"

        query = f"""SELECT
                        {season_col},
                        {week_col},
                        game_id,
                        odds_provider,
                        team1,
                        team2,
                        team1_name,
                        team2_name,
                        team1_id,
                        team2_id,
                        team1_logo,
                        team2_logo,
                        team2_odds,
                        team1_odds,
                        team2_odds_wp,
                        team1_odds_wp,
                        score1,
                        score2,
                        date as gametime,
                        date_str,
                        time,
                        weekday,
                        status
                    from
                        {table}
                    where
                        {week_col} = '{week_inp}'
                        and {season_col} = {season_inp}
                        and {team_clause};"""
        return(query)
