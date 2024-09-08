from flask import Flask, render_template, redirect, request, jsonify, make_response
from flask_talisman import Talisman
import json
import os
from fractions import Fraction
import pandas as pd
from validations import Validations
from makeDepositHelper import MakeDepositHelper
from databaseHelper import DataBaseHelper
import warnings
warnings.filterwarnings("ignore")

# Create an instance of Flask
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Talisman
if 'DYNO' in os.environ:
    Talisman(app, content_security_policy=None)

# helper classes
makeDepositHelper = MakeDepositHelper()
validations = Validations()
databaseHelper = DataBaseHelper()

# helper funcs
def odds_to_decimal(odds):
    if "+" in odds:
        rtn = (int(odds.strip("+"))/100) + 1
    else:
        rtn = (100/int(odds.strip("-"))) + 1

    rtn = '{0:.3f}'.format(rtn)
    return(rtn)

def odds_to_frac(odds):
    if "+" in odds:
        rtn = (int(odds.strip("+"))/100)
    else:
        rtn = (100/int(odds.strip("-")))

    rtn = Fraction(rtn).limit_denominator(100)
    rtn = str(rtn.numerator) + "/" + str(rtn.denominator)
    return rtn

# Route to render index.html template using data from Mongo
@app.route("/")
def home():
    # Return template and data
    return render_template("welcome.html")

@app.route("/roadmap")
def roadmap():
    # Return template and data
    return render_template("roadmap.html")

###################################
############ Web Pages#############
###################################

@app.route("/sports/html/<sport>/<page>")
def render_webpage(sport, page):
    # Return template and data
    return render_template(f"{sport}/{page}.html")

#######################################################
############# HELPER FUNCTIONS ########################
#######################################################

@app.route("/verify_ban", methods=["POST"])
def verify_ban():
    content = request.json["data"]
    ban_address = content["ban_address"]
    # print(ban_address)
    is_valid = validations.validate_address(ban_address)
    return(jsonify({"ban_address":ban_address, "verified":is_valid}))

#######################################################
#################### API ##############################
#######################################################

@app.route("/sports/api/get_current_week/<sport>", methods=["POST"])
def get_current_week(sport):
    content = request.json["data"]
    season_inp = int(content["season_inp"])

    # get current week
    if sport == "nfl":
        current_week = databaseHelper.nfl.getCurrentNFLWeek(season_inp)
    elif sport == "cwc":
        current_week = databaseHelper.cwc.getCurrentCWCWeek(season_inp)
    elif sport == "mlb":
        current_week = databaseHelper.mlb.getCurrentMLBWeek(season_inp)
    elif sport == "nba":
        current_week = databaseHelper.nba.getCurrentNBAWeek(season_inp)
    elif sport == "nhl":
        current_week = databaseHelper.nhl.getCurrentNHLWeek(season_inp)
    else:
        current_week = databaseHelper.rwc.getCurrentRWCWeek(season_inp)

    return(jsonify({"current_week": current_week}))

@app.route("/sports/api/get_game_data/<sport>", methods=["POST"])
def get_game_data(sport):
    content = request.json["data"]
    season_inp = int(content["season_inp"])
    week_inp = content["week_inp"]
    team_inp = content["team_inp"]

    # get data for sport
    if sport == "nfl":
        df = databaseHelper.nfl.getNFLGameOdds(week_inp, season_inp, team_inp)
        deposits = databaseHelper.nfl.getNFLDepositDataAggregates(week_inp, season_inp)
    elif sport == "cwc":
        df = databaseHelper.cwc.getCWCGameOdds(week_inp, season_inp, team_inp)
        deposits = databaseHelper.cwc.getCWCDepositDataAggregates(week_inp, season_inp)
    elif sport == "mlb":
        df = databaseHelper.mlb.getMLBGameOdds(week_inp, season_inp, team_inp)
        deposits = databaseHelper.mlb.getMLBDepositDataAggregates(week_inp, season_inp)
    elif sport == "nba":
        df = databaseHelper.nba.getNBAGameOdds(week_inp, season_inp, team_inp)
        deposits = databaseHelper.nba.getNBADepositDataAggregates(week_inp, season_inp)
    elif sport == "nhl":
        df = databaseHelper.nhl.getNHLGameOdds(week_inp, season_inp, team_inp)
        deposits = databaseHelper.nhl.getNHLDepositDataAggregates(week_inp, season_inp)
    else:
        df = databaseHelper.rwc.getRWCGameOdds(week_inp, season_inp, team_inp)
        deposits = databaseHelper.rwc.getRWCDepositDataAggregates(week_inp, season_inp)

    # merge deposits
    df = pd.merge(df, deposits, on="game_id", how="left")

    df.loc[:, ["team1_bets", "team2_bets", "bet_amount", "team1_perc", "team2_perc"]] = df.loc[:, ["team1_bets", "team2_bets", "bet_amount", "team1_perc", "team2_perc"]].fillna(0)
    df = df.sort_values(by=["gametime", "game_id"], ascending=True)
    df["team1_rec"] = (df.team2_perc - df.team1_perc) - (df.team2_odds_wp - df.team1_odds_wp) >= 0
    df["team2_rec"] = (df.team1_perc - df.team2_perc) - (df.team1_odds_wp - df.team2_odds_wp) >= 0

    # get decimal & frac odds
    df["team2_odds_dec"] = df.team2_odds.apply(odds_to_decimal)
    df["team1_odds_dec"] = df.team1_odds.apply(odds_to_decimal)
    df["team2_odds_frac"] = df.team2_odds.apply(odds_to_frac)
    df["team1_odds_frac"] = df.team1_odds.apply(odds_to_frac)

    # rearrange so started games are at the bottom
    df1 = df.loc[df.started].reset_index(drop=True)
    df2 = df.loc[~df.started].reset_index(drop=True)
    df = pd.concat([df2, df1], ignore_index=True)

    return(jsonify(json.loads(df.to_json(orient="records"))))

@app.route("/sports/api/get_teams/<sport>", methods=["POST"])
def get_teams(sport):
    content = request.json["data"]
    season_inp = int(content["season_inp"])
    week_inp = content["week_inp"]

    # get data for sport
    if sport == "nfl":
        df = databaseHelper.nfl.getNFLTeams(week_inp, season_inp)
    elif sport == "cwc":
        df = databaseHelper.cwc.getCWCTeams(week_inp, season_inp)
    elif sport == "mlb":
        df = databaseHelper.mlb.getMLBTeams(week_inp, season_inp)
    elif sport == "nba":
        df = databaseHelper.nba.getNBATeams(week_inp, season_inp)
    elif sport == "nhl":
        df = databaseHelper.nhl.getNHLTeams(week_inp, season_inp)
    else:
        df = databaseHelper.rwc.getRWCTeams(week_inp, season_inp)

    return(jsonify(json.loads(df.to_json(orient="records"))))

@app.route("/sports/api/get_history/<sport>", methods=["POST"])
def get_history(sport):
    content = request.json["data"]
    min_ban = float(content["min_ban"])
    max_ban = float(content["max_ban"])
    week_inp = content["week_inp"]
    season_inp = int(content["season_inp"])

    if sport == "nfl":
        raw_deposits = databaseHelper.nfl.getNFLDepositData(week_inp, season_inp, min_ban, max_ban)
    elif sport == "cwc":
        raw_deposits = databaseHelper.cwc.getCWCDepositData(week_inp, season_inp, min_ban, max_ban)
    elif sport == "mlb":
        raw_deposits = databaseHelper.mlb.getMLBDepositData(week_inp, season_inp, min_ban, max_ban)
    elif sport == "nba":
        raw_deposits = databaseHelper.nba.getNBADepositData(week_inp, season_inp, min_ban, max_ban)
    elif sport == "nhl":
        raw_deposits = databaseHelper.nhl.getNHLDepositData(week_inp, season_inp, min_ban, max_ban)
    else:
        raw_deposits = databaseHelper.rwc.getRWCDepositData(week_inp, season_inp, min_ban, max_ban)

    return(jsonify(json.loads(raw_deposits.to_json(orient="records"))))

@app.route("/sports/api/get_leaderboards/<sport>", methods=["POST"])
def get_leaderboards(sport):
    content = request.json["data"]
    ban_address = content["ban_address"]
    week_inp = content["week_inp"]
    season_inp = content["season_inp"]

    if sport == "nfl":
        raw_stats = databaseHelper.nfl.getNFLWeekLeaderboards(week_inp, season_inp, ban_address)
    elif sport == "cwc":
        raw_stats = databaseHelper.cwc.getCWCWeekLeaderboards(week_inp, season_inp, ban_address)
    elif sport == "mlb":
        raw_stats = databaseHelper.mlb.getMLBWeekLeaderboards(week_inp, season_inp, ban_address)
    elif sport == "nba":
        raw_stats = databaseHelper.nba.getNBAWeekLeaderboards(week_inp, season_inp, ban_address)
    elif sport == "nhl":
        raw_stats = databaseHelper.nhl.getNHLWeekLeaderboards(week_inp, season_inp, ban_address)
    else:
        raw_stats = databaseHelper.rwc.getRWCWeekLeaderboards(week_inp, season_inp, ban_address)

    return(jsonify(json.loads(raw_stats.to_json(orient="records"))))

@app.route("/sports/api/get_ban_addresses/<sport>", methods=["POST"])
def get_ban_addresses(sport):
    content = request.json["data"]
    week_inp = content["week_inp"]
    season_inp = content["season_inp"]

    if sport == "nfl":
        raw_addresses = databaseHelper.nfl.getNFLBanAddresses(week_inp, season_inp)
    elif sport == "cwc":
        raw_addresses = databaseHelper.cwc.getCWCBanAddresses(week_inp, season_inp)
    elif sport == "mlb":
        raw_addresses = databaseHelper.mlb.getMLBBanAddresses(week_inp, season_inp)
    elif sport == "nba":
        raw_addresses = databaseHelper.nba.getNBABanAddresses(week_inp, season_inp)
    elif sport == "nhl":
        raw_addresses = databaseHelper.nhl.getNHLBanAddresses(week_inp, season_inp)
    else:
        raw_addresses = databaseHelper.rwc.getRWCBanAddresses(week_inp, season_inp)

    return(jsonify(json.loads(raw_addresses.to_json(orient="records"))))

@app.route("/sports/api/get_payouts/<sport>", methods=["POST"])
def get_payouts(sport):
    content = request.json["data"]
    min_ban = float(content["min_ban"])
    max_ban = float(content["max_ban"])
    week_inp = content["week_inp"]
    season_inp = int(content["season_inp"])

    if sport == "nfl":
        payouts = databaseHelper.nfl.getNFLPayouts(week_inp, season_inp, min_ban, max_ban)
    elif sport == "cwc":
        payouts = databaseHelper.cwc.getCWCPayouts(week_inp, season_inp, min_ban, max_ban)
    elif sport == "mlb":
        payouts = databaseHelper.mlb.getMLBPayouts(week_inp, season_inp, min_ban, max_ban)
    elif sport == "nba":
        payouts = databaseHelper.nba.getNBAPayouts(week_inp, season_inp, min_ban, max_ban)
    elif sport == "nhl":
        payouts = databaseHelper.nhl.getNHLPayouts(week_inp, season_inp, min_ban, max_ban)
    else:
        payouts = databaseHelper.rwc.getRWCPayouts(week_inp, season_inp, min_ban, max_ban)

    return(jsonify(json.loads(payouts.to_json(orient="records"))))

@app.route("/sports/api/confirm_deposit/<sport>", methods=["POST"])
def confirm_deposit(sport):
    content = request.json["data"]
    ban_address = content["ban_address"]
    team = content["team"]
    team_abbr = team.split("_")[1]
    team_num = team.split("_")[0]
    game_id = content["game_id"]
    deposit_amount = float(content["amount"])
    week_inp = content["week_inp"]
    season_inp = int(content["season_inp"])

    if sport == "nfl":
        confirmed = makeDepositHelper.confirmDeposit(ban_address, "nfl", game_id, team_num, team_abbr, deposit_amount, "nfl_bets", "nfl_week", "nfl_season", week_inp, season_inp)
    elif sport == "cwc":
        confirmed = makeDepositHelper.confirmDeposit(ban_address, "cwc", game_id, team_num, team_abbr, deposit_amount, "cricket_world_cup_bets", "match_round", "season", week_inp, season_inp)
    elif sport == "mlb":
        confirmed = makeDepositHelper.confirmDeposit(ban_address, "mlb", game_id, team_num, team_abbr, deposit_amount, "mlb_bets", "match_round", "mlb_season", week_inp, season_inp)
    elif sport == "nba":
        confirmed = makeDepositHelper.confirmDeposit(ban_address, "nba", game_id, team_num, team_abbr, deposit_amount, "nba_bets", "match_round", "nba_season", week_inp, season_inp)
    elif sport == "nhl":
        confirmed = makeDepositHelper.confirmDeposit(ban_address, "nhl", game_id, team_num, team_abbr, deposit_amount, "nhl_bets", "match_round", "nhl_season", week_inp, season_inp)
    else:
        confirmed = makeDepositHelper.confirmDeposit(ban_address, "rwc", game_id, team_num, team_abbr, deposit_amount, "rugby_world_cup_bets", "match_round", "season", week_inp, season_inp)

    return(jsonify(confirmed))

#############################################################

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["X-XSS-Protection"] = "1; mode=block"
    return r

#main
if __name__ == "__main__":
    app.run(debug=True)
