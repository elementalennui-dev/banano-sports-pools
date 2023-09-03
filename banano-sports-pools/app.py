from flask import Flask, render_template, redirect, request, jsonify, make_response
from flask_talisman import Talisman
import json
import datetime
import pytz
import os
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
############### NFL ###############
###################################

@app.route("/nfl/nfl_pools")
def nfl_pools():
    # Return template and data
    return render_template("nfl/nfl_pools.html")

@app.route("/nfl/nfl_history")
def nfl_history():
    # Return template and data
    return render_template("nfl/nfl_history.html")

@app.route("/nfl/nfl_payouts")
def nfl_payouts():
    # Return template and data
    return render_template("nfl/nfl_payouts.html")

@app.route("/nfl/nfl_leaderboards")
def nfl_leaderboards():
    # Return template and data
    return render_template("nfl/nfl_leaderboards.html")

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
#################### NFL ##############################
#######################################################

@app.route("/nfl/get_nfl_current_week", methods=["POST"])
def get_nfl_current_week():
    content = request.json["data"]
    nfl_season = int(content["nfl_season"])

    current_week = databaseHelper.getCurrentNFLWeek(nfl_season)
    return(jsonify({"current_week": current_week}))

@app.route("/nfl/get_nfl_data/<nfl_week>/<nfl_season>", methods=["GET"])
def get_nfl_data(nfl_week, nfl_season):
    df = databaseHelper.getNFLGameOdds(nfl_week, nfl_season)
    deposits = databaseHelper.getNFLDepositDataAggregates(nfl_week, nfl_season)

    # merge deposits
    df = pd.merge(df, deposits, on="game_id", how="left")

    df.loc[:, ["team1_bets", "team2_bets", "bet_amount", "team1_perc", "team2_perc"]] = df.loc[:, ["team1_bets", "team2_bets", "bet_amount", "team1_perc", "team2_perc"]].fillna(0)
    df = df.sort_values(by=["gametime", "game_id"], ascending=True)
    df["team1_rec"] = (df.team2_perc - df.team1_perc) - (df.team2_odds_wp - df.team1_odds_wp) >= 0
    df["team2_rec"] = (df.team1_perc - df.team2_perc) - (df.team1_odds_wp - df.team2_odds_wp) >= 0

    # rearrange so started games are at the bottom
    df1 = df.loc[df.started].reset_index(drop=True)
    df2 = df.loc[~df.started].reset_index(drop=True)
    df = df2.append(df1)

    return(jsonify(json.loads(df.to_json(orient="records"))))

@app.route("/nfl/get_nfl_history", methods=["POST"])
def get_nfl_history():
    content = request.json["data"]
    min_ban = float(content["min_ban"])
    max_ban = float(content["max_ban"])
    nfl_week = int(content["nfl_week"])
    nfl_season = int(content["nfl_season"])

    raw_deposits = databaseHelper.getNFLDepositData(nfl_week, nfl_season, min_ban, max_ban)
    return(jsonify(json.loads(raw_deposits.to_json(orient="records"))))

@app.route("/nfl/get_nfl_leaderboards", methods=["POST"])
def get_nfl_leaderboards():
    content = request.json["data"]
    ban_address = content["ban_address"]
    nfl_week = content["nfl_week"]
    nfl_season = content["nfl_season"]

    raw_stats = databaseHelper.getNFLWeekLeaderboards(nfl_week, nfl_season, ban_address)
    return(jsonify(json.loads(raw_stats.to_json(orient="records"))))

@app.route("/nfl/get_nfl_ban_addresses", methods=["POST"])
def get_nfl_ban_addresses():
    content = request.json["data"]
    nfl_week = content["nfl_week"]
    nfl_season = content["nfl_season"]
    raw_addresses = databaseHelper.getNFLBanAddresses(nfl_week, nfl_season)
    return(jsonify(json.loads(raw_addresses.to_json(orient="records"))))

@app.route("/nfl/get_nfl_payouts", methods=["POST"])
def get_nfl_payouts():
    content = request.json["data"]
    min_ban = float(content["min_ban"])
    max_ban = float(content["max_ban"])
    nfl_week = int(content["nfl_week"])
    nfl_season = int(content["nfl_season"])

    payouts = databaseHelper.getNFLPayouts(nfl_week, nfl_season, min_ban, max_ban)
    return(jsonify(json.loads(payouts.to_json(orient="records"))))

@app.route("/nfl/confirm_nfl_deposit", methods=["POST"])
def confirm_nfl_deposit():
    content = request.json["data"]
    ban_address = content["ban_address"]
    team = content["team"]
    team_abbr = team.split("_")[1]
    team_num = team.split("_")[0]
    game_id = content["game_id"]
    deposit_amount = float(content["amount"])
    nfl_week = int(content["nfl_week"])
    nfl_season = int(content["nfl_season"])

    confirmed = makeDepositHelper.confirmNFLDeposit(ban_address, game_id, team_num, team_abbr, deposit_amount, nfl_week, nfl_season)
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
