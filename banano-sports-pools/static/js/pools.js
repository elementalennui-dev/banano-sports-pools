//theme set
var theme = "yeti";
var ban_address_verified = "";
var game_data = [];
const sprtsAddress = "ban_3sprts3a8hzysquk4mcy4ct4f6izp1mxtbnybiyrriprtjrn9da9cbd859qf";

if (window.name) {
    theme = JSON.parse(window.name).theme;
    ban_address_verified = JSON.parse(window.name).ban_address_verified;
}

// on page load
$(document).ready(function() {
    console.log("Page Loaded");

    // set theme
    if (theme) {
        $('head link').last().after('<link rel="stylesheet" type="text/css" href="https://stackpath.bootstrapcdn.com/bootswatch/4.5.2/' + theme + '/bootstrap.min.css">');
        $('#themeSelect').val(theme);
    } else {
        //order matters in CSS load
        $('head link').last().after('<link rel="stylesheet" type="text/css" href="https://stackpath.bootstrapcdn.com/bootswatch/4.5.2/' + $('#themeSelect').val() + '/bootstrap.min.css">');
        window.name = JSON.stringify({ //save to window, in case we move across pages
            ban_address_verified: ban_address_verified,
            theme: $('#themeSelect').val()
        });
    }

    // check if ban address in cache, if so, load the monkey
    if (ban_address_verified) {
        $("#post_verify_ban").show();
        $("#monkey").show();
        $("#pre_verify").hide();
        $("#ban_address").text(ban_address_verified.replace(ban_address_verified.substring(7, 61), "....."));
        $("#inp_wallet").text(ban_address_verified);

        $("#monkey").empty();
        $("#monkey").append(`<img loading="lazy" style="min-width: 100px; height: 100px; margin-top: -12px; float: right" src="https://monkey.banano.cc/api/v1/monkey/${ban_address_verified}">`);
    }

    // event listeners
    $('#themeSelect').change(function() {
        let styleSheets = $('head').find('link');
        styleSheets.each(function() {
            if ($(this).attr('href').includes('bootswatch')) {
                $(this).remove();
            }
        });

        // add new sheet
        $('head link').last().after('<link rel="stylesheet" type="text/css" href="https://stackpath.bootstrapcdn.com/bootswatch/4.5.2/' + $('#themeSelect').val() + '/bootstrap.min.css">');
        window.name = JSON.stringify({ //save to window, in case we move across pages
            ban_address_verified: ban_address_verified,
            theme: $('#themeSelect').val()
        });
    });

    $("#verify").on("click", function(x) {
        validateBanAddress();
    });

    // Set the width to animate the progress bar, along with time duration in milliseconds
    $(".progress-bar").animate({
        width: "100%",
    }, 2000);

    // need to clear cache as well as all elements on the page referencing the address
    $("#changeBanAddress").on("click", function(x) {
        $("#post_verify_ban").hide();
        $("#pre_verify").show();
        $("#monkey").hide();

        ban_address_verified = "";
        $("#ban_address").text(ban_address_verified);
        $("#inp_wallet").text(ban_address_verified);
        $("#inputBanano").val(ban_address_verified);

        window.name = JSON.stringify({ //save to window, in case we move across pages
            ban_address_verified: ban_address_verified,
            theme: $('#themeSelect').val()
        });
    });

    $("#copy_address").on("click", function(x) {
        // Get the text field
        var copyText = sprtsAddress;

        // Copy the text inside the text field
        navigator.clipboard.writeText(copyText);

        // Alert the copied text
        alert("Address Copied!");
    });

    //highlight games
    $("#rec_games").on("change", function(x) {
        recommendGames();
    });

    // modal click for deposits
    $("#next_modal_page").on("click", function(x) {

        let game_id = $("#game_id_splt").text();
        let game = game_data.filter(x => x.game_id == game_id)[0]

        // checks for quantity, less than 100, and before kickoff
        if (($("#quantity").val() != "") && ($("#quantity").val() != null)) {

            if ($("#quantity").val() > 1000) {
                alert("For now, the maximum of a single deposit is 1,000 BAN. :)")
                return false;
            }

            if (Date.now() < game.gametime) {
                $("#ban_deposit").text($("#quantity").val());
                $("#first_page").hide();
                $("#second_page").show();
                makeQRCode();
            } else {
                // alert("Cannot place a deposit on a game that's already started!");
                // return false;
                $("#ban_deposit").text($("#quantity").val());
                $("#first_page").hide();
                $("#second_page").show();
                makeQRCode();
            }
        } else {
            alert("Please enter an amount of BAN to deposit!");
            return false;
        }
    });

    // more modal controls
    $("#back_page_modal").on("click", function(x) {
        $("#second_page").hide();
        $("#first_page").show();
    });

    $("#deposit_modal").on("hidden.bs.modal", function() {
        $("#quantity").text("");
        $("#quantity").val("");
        $("#deposit_confirmation").children().last().remove();
        $(".modal-footer").hide();
        $("#third_page").hide();
        $("#second_page").hide();
        $("#first_page").show();
    });
});

// gets the current Week, then populates games
function getCurrentWeek(sport) {
    let season_inp = $("#season_inp").val();
    let payload = {
        "season_inp": season_inp
    }

    $.ajax({
        type: "POST",
        url: `/sports/api/get_current_week/${sport}`,
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({ "data": payload }),
        success: function(returnedData) {

            // get games for current week
            let current_week = returnedData["current_week"];
            $("#week_inp").val(current_week);
            getGames(sport);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            alert("Something unexpected occurred and we were unable to process your request! Please submit a bug request to elementalennui#4641 on Discord.");
        }
    });
}

function recommendGames() {
    if ($("#rec_games").is(':checked')) {
        $(".is_rec").addClass("highlight");
    } else {
        $(".is_rec").removeClass("highlight");
    }
}

function makeQRCode() {
    let amount = $("#quantity").val();
    amount = Math.round(amount * 100, 0);
    $("#qrcode").empty();
    let qrUrl = `banano:${sprtsAddress}?amount=${amount}000000000000000000000000000`;
    let qrcode = new QRCode(document.getElementById('qrcode'), {
        text: qrUrl,
        width: 128,
        height: 128,
        colorDark: '#000',
        colorLight: '#fff',
        correctLevel: QRCode.CorrectLevel.H
    });

    // also populate links
    $("#sendBanLinks").empty();
    $("#sendBanLinks").html(`Send <a target="_blank" rel="noopener" href="https://vault.banano.cc/send?to=${sprtsAddress}&amp;amount=${$("#quantity").val()}">from BananoVault</a> • OR •
    <a href="${qrUrl}">from installed wallet</a>`)
}

function confirmDeposit(sport) {
    // disable button
    $("#confirm_deposit").prop("disabled", true);

    // create the payload
    let week_inp = $("#week_inp").val();
    let season_inp = $("#season_inp").val();

    var payload = {
        "ban_address": ban_address_verified,
        "team": $("#team_deposit").val(),
        "game_id": $("#game_id_splt").text(),
        "amount": $("#quantity").val(),
        "week_inp": week_inp,
        "season_inp": season_inp
    }

    $.ajax({
        type: "POST",
        url: `/sports/api/confirm_deposit/${sport}`,
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({ "data": payload }),
        success: function(returnedData) {

            // deposit confirmed! WOOOOOO
            if (returnedData["confirmed"]) {
                $(".modal-footer").show();
                $("#third_page").show();
                $("#second_page").hide();

                $("#deposit_confirmation").append(`<h4>${returnedData["message"]}</h4>`);
            } else {
                alert(returnedData["message"]);
            }

            //unfreeze
            $("#confirm_deposit").prop("disabled", false);

        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            alert("Something unexpected occurred and we were unable to process your request! Please submit a bug request to elementalennui#4641 on Discord.");
            $("#confirm_deposit").prop("disabled", false);
        }
    });
}

function validateBanAddress() {
    let ban_address = $("#inputBanano").val();

    // create the payload
    let payload = {
        "ban_address": ban_address
    }

    // Perform a POST request to the query URL
    $.ajax({
        type: "POST",
        url: "/verify_ban",
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({ "data": payload }),
        success: function(returnedData) {
            // populate the web elements referencing the ban address
            if (returnedData["verified"]) {
                $("#post_verify_ban").show();
                $("#monkey").show();
                $("#pre_verify").hide();
                $("#ban_address").text(ban_address.replace(ban_address.substring(7, 61), "....."));
                ban_address_verified = ban_address;
                $("#inp_wallet").text(ban_address_verified);

                window.name = JSON.stringify({ //save to window, in case we move across pages
                    ban_address_verified: ban_address_verified,
                    theme: $('#themeSelect').val()
                });

                $("#monkey").empty();
                $("#monkey").append(`<img loading="lazy" style="min-width: 100px; height: 100px; margin-top: -12px; float: right" src="https://monkey.banano.cc/api/v1/monkey/${ban_address_verified}">`);
            } else {
                alert("Your Ban Address was not verified! Please try again.");
                ban_address_verified = "";
            }

        },
        error: function(textStatus, errorThrown) {
            alert("Something unexpected occurred and we were unable to process your request! Please submit a bug request to elementalennui#4641 on Discord.");
        }
    });
}

// main function to get the active games for that week
function getGames(sport) {

    let week_inp = $("#week_inp").val();
    let season_inp = $("#season_inp").val();

    $.ajax({
        type: "GET",
        url: `/sports/api/get_game_data/${sport}/${week_inp}/${season_inp}`,
        contentType: "application/json; charset=utf-8",
        success: function(data) {
            // console.log(data);
            game_data = data;

            let team_num = 0;
            let row = "";
            let finished_row = false;
            $("#games").empty();

            game_data.forEach(function (x) {
                if (team_num % 3 == 0) {
                    $("#games").append(row);
                    finished_row = true;
                    row = '<div class="row">';
                }

                // show more disabled deposits text
                let display = "none";
                let display2 = "none";
                if (x.disabled == "disabled") {
                    display = "block";
                } else {
                    display2 = "block";
                }

                // calculate return payouts
                let return2 = (x.team2_bets + x.team1_bets) / x.team2_bets;
                if (isNaN(return2)) {
                    return2 = 1;
                } else if ((x.team2_bets === 0) & (x.team1_bets > 0)) {
                    return2 = (x.team2_bets + x.team1_bets);
                } else if ((x.team2_bets === 0) & (x.team1_bets === 0)) {
                    return2 = 1; //both are 0
                } else {
                    return2 = (x.team2_bets + x.team1_bets) / x.team2_bets;
                }

                let return1 = (x.team2_bets + x.team1_bets) / x.team1_bets;
                if (isNaN(return1)) {
                    return1 = 1;
                } else if ((x.team1_bets === 0) & (x.team2_bets > 0)) {
                    return1 = (x.team2_bets + x.team1_bets);
                } else if ((x.team1_bets === 0) & (x.team2_bets === 0)) {
                    return1 = 1; //both are 0
                } else {
                    return1 = (x.team2_bets + x.team1_bets) / x.team1_bets;
                }

                let team1_rec = "";
                if (x.team1_rec) team1_rec = "is_rec";

                let team2_rec = "";
                if (x.team2_rec) team2_rec = "is_rec";

                // create the dynamic game HTML (move to server side?)
                game = `<div class="col-md-4 text-center">
                            <p><strong>Game ID:</strong> ${x.game_id}</p>
                            <p><strong>Date:</strong> ${x.weekday}, ${x.date_str} ${x.time} (ET) | <strong>Pool Size:</strong> ${x.bet_amount} BAN</p>
                            <p><strong>${x.team2}:</strong> 1 BAN returns ${+return2.toFixed(2)} BAN | <strong>${x.team1}:</strong> 1 BAN returns ${+return1.toFixed(2)} BAN</p>
                            <div class="table-responsive">
                                <table class="table-bordered table-striped table-hover table">
                                    <thead>
                                        <tr>
                                            <th>Team</th>
                                            <th>Win Prob</th>
                                            <th>BAN Pool</th>
                                            <th>BAN Perc</th>
                                            <th>Score</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr class="${team2_rec}">
                                            <td class="text-center align-middle">
                                                <p><img src="${x.team2_logo}" width="48" height="48"><strong> ${x.team2}</strong></p>
                                            </td>
                                            <td class="text-center align-middle">
                                                <table style="font-size: 0.65rem;" class="table-bordered table-striped table-hover table">
                                                    <tr>
                                                        <th class="text-center align-middle">American</th>
                                                        <td class="text-center align-middle">${x.team2_odds}</td>
                                                    </tr>
                                                    <tr>
                                                        <th class="text-center align-middle">Fraction</th>
                                                        <td class="text-center align-middle">${x.team2_odds_frac}</td>
                                                    </tr>
                                                    <tr>
                                                        <th class="text-center align-middle">Decimal</th>
                                                        <td class="text-center align-middle">${x.team2_odds_dec}</td>
                                                    </tr>
                                                    <tr>
                                                        <th class="text-center align-middle">Implied</th>
                                                        <td class="text-center align-middle">${Math.floor(100*x.team2_odds_wp)}%</td>
                                                    </tr>
                                                </table>
                                            </td>
                                            <td class="text-center align-middle">
                                                <p>${x.team2_bets}</p>
                                            </td>
                                            <td class="text-center align-middle">
                                                <p>${Math.floor(100*x.team2_perc)}%</p>
                                            </td>
                                            <td class="text-center align-middle">
                                                <p>${x.score2}</p>
                                            </td>
                                        </tr>
                                        <tr class="${team1_rec}">
                                            <td class="text-center align-middle">
                                                <p><img src="${x.team1_logo}" width="48" height="48"><strong> ${x.team1}</strong></p>
                                            </td>
                                            <td>
                                                <table style="font-size: 0.7rem;" class="table-bordered table-striped table-hover table">
                                                    <tr>
                                                        <th class="text-center align-middle">American</th>
                                                        <td class="text-center align-middle">${x.team1_odds}</td>
                                                    </tr>
                                                    <tr>
                                                        <th class="text-center align-middle">Fraction</th>
                                                        <td class="text-center align-middle">${x.team1_odds_frac}</td>
                                                    </tr>
                                                    <tr>
                                                        <th class="text-center align-middle">Decimal</th>
                                                        <td class="text-center align-middle">${x.team1_odds_dec}</td>
                                                    </tr>
                                                    <tr>
                                                        <th class="text-center align-middle">Implied</th>
                                                        <td class="text-center align-middle">${Math.floor(100*x.team1_odds_wp)}%</td>
                                                    </tr>
                                                </table>
                                            </td>
                                            <td class="text-center align-middle">
                                                <p>${x.team1_bets}</p>
                                            </td>
                                            <td class="text-center align-middle">
                                                <p>${Math.floor(100*x.team1_perc)}%</p>
                                            </td>
                                            <td class="text-center align-middle">
                                                <p>${x.score1}</p>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <p style="display:${display}" class="text-danger"><i>Match is locked for new deposits</i></p>
                            <p style="display:${display2}" class="text-secondary"><i id="${x.game_id}_countdown"></i></p>
                            <button type="button" id="btn-${x.game_id}-${x.team1}-${x.team2}" ${x.disabled} class="btn btn-primary deposit_button">Place Deposit!</button>
                            <br>
                            <br>
                        </div>`;
                row += game;
                team_num += 1;
                finished_row = false;
            });

            // if row doesn't have three games, append anyway
            if (!finished_row) {
                $("#games").append(row);
            }

            // show/hide
            $("#progress_container").hide();
            $("#games").show();

            // countdown timer
            game_data.forEach(function(x) {
                setInterval(function() { countdownTimer(x.game_id, x.gametime); }, 1000);
            });

            recommendGames();

            // add event listeners
            $(".deposit_button").on("click", function(e) {
                // alert(`You clicked ${$(this).attr("id")}!`)
                if (ban_address_verified === "") {
                    alert("Please enter your BAN Address first!");
                    return false;
                } else {
                    let game_id_btn = $(this).attr("id");
                    let game_id_splt = game_id_btn.split("-")[1];
                    let team1_splt = game_id_btn.split("-")[2];
                    let team2_splt = game_id_btn.split("-")[3];

                    let game = game_data.filter(x => x.game_id == game_id_splt)[0];

                    $("#game_id_splt").text(game_id_splt);
                    $("#teams_splt").text(`${team1_splt} vs ${team2_splt}`);

                    $("#team_select").empty();
                    $("#team_select").append(`<select name="team_deposit" id="team_deposit">
                                                <option value="team2_${game.team2}">${game.team2_name}</option>
                                                <option value="team1_${game.team1}">${game.team1_name}</option>
                                            </select>`);

                    $('#deposit_modal').modal({ backdrop: 'static', keyboard: false });
                }
            });
        },
        error: function(textStatus, errorThrown) {
            console.log("FAILED to get data");
            alert("Something unexpected occurred and we were unable to process your request! Please submit a bug request to elementalennui#4641 on Discord.");
        }
    });
}

function countdownTimer(game_id, gametime) {
    const difference = +new Date(gametime) - +new Date();
    let remaining = "Time's up!";

    if (difference > 0) {
        const parts = {
            "day(s)": Math.floor(difference / (1000 * 60 * 60 * 24)),
            "hr": Math.floor((difference / (1000 * 60 * 60)) % 24),
            "min": Math.floor((difference / 1000 / 60) % 60),
            "sec": Math.floor((difference / 1000) % 60),
        };
        remaining = Object.keys(parts).map(part => {
            return `${parts[part]} ${part}`;
        }).join(" ");
        remaining += " until kickoff!"
    }

    $(`#${game_id}_countdown`).text(remaining);
}
