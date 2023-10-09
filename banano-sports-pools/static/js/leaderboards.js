var theme = "yeti";
var ban_address_verified = "";

if (window.name) {
    theme = JSON.parse(window.name).theme;
    ban_address_verified = JSON.parse(window.name).ban_address_verified;
}

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

    // tip
    makeTipQRCode();
});

// gets the current Week, then populates leaderboard
function getCurrentWeek(sport, week_col) {
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
            $("#week_inp").val(`'${current_week}'`);
            getBanAddresses(sport)
            getLeaderboards(sport, week_col);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            alert("Something unexpected occurred and we were unable to process your request! Please submit a bug request to elementalennui on Discord.");
        }
    });
}

// get ban addresses to filter by
function getBanAddresses(sport) {
    // Perform a POST request to the query URL
    let week_inp = $("#week_inp").val();
    let season_inp = $("#season_inp").val();
    let payload = {
        "week_inp": week_inp,
        'season_inp': season_inp
    }

    $.ajax({
        type: "POST",
        url: `/sports/api/get_ban_addresses/${sport}`,
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({ "data": payload }),
        success: function(returnedData) {
            // reset
            $("#ban_address").empty();
            $("#ban_address").append(`<option value="">All</option>`);
            returnedData.forEach(function(x) {
                let ban_address = x["ban_address"];
                $("#ban_address").append(`<option>${ban_address}</option>`);
            });

        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            alert("Something unexpected occurred and we were unable to process your request! Please submit a bug request to elementalennui on Discord.");
        }
    });
}

// call endpoint to query database
function getLeaderboards(sport, week_col) {
    let week_inp = $("#week_inp").val();
    let season_inp = $("#season_inp").val();
    let ban_address = $("#ban_address").val();

    // check if inputs are valid

    // create the payload
    let payload = {
        "week_inp": week_inp,
        "season_inp": season_inp,
        "ban_address": ban_address
    }

    // Perform a POST request to the query URL
    $.ajax({
        type: "POST",
        url: `/sports/api/get_leaderboards/${sport}`,
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({ "data": payload }),
        success: function(returnedData) {
            renderLeaderboards(returnedData, ban_address, week_col, sport);
            makeLeaderboardBarPlot(returnedData, ban_address);
            makeLeaderboardPiePlot(returnedData, ban_address);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            alert("Something unexpected occurred and we were unable to process your request! Please submit a bug request to elementalennui on Discord.");
        }
    });

}

// displays leaderboards
function renderLeaderboards(inp_data, ban_address, week_col, sport) {
    // init html string
    let html = "";

    if (ban_address !== "") {

        // destroy datatable
        $('#sql_table').hide();
        $('#sql_table_wrapper').hide();
        $("#indiv_table").show();
        $('#indiv_table_wrapper').show();
        $('#indiv_table').DataTable().clear().destroy();

        // loop through all rows
        inp_data.forEach(function(row) {
            if (row.ban_address == ban_address_verified) {
                html += '<tr class="table-info">';
            } else {
                html += "<tr>";
            }

            // loop through each cell (order matters)
            html += `<td>${row[week_col]}</td>`;
            html += `<td><a target='_blank' href='https://creeper.banano.cc/account/${row.ban_address}'>${row.ban_address}</a></td>`;
            html += `<td>${row.game_id}</td>`;
            html += `<td>${row.betting_team}</td>`;
            html += `<td>${row.is_winner}</td>`;
            html += `<td>${row.is_tie}</td>`;
            html += `<td>${row.bet_amount}</td>`;
            html += `<td>${row.payout}</td>`;
            html += `<td>${row.profit}</td>`;
            html += `<td>${+(100*row.return_perc).toFixed(2)}</td>`;

            // close the row
            html += "</tr>";
        });

        // shove the html in our elements
        // console.log(html);
        $("#indiv_table tbody").html("");
        $("#indiv_table tbody").append(html);

        // remake data table
        $('#indiv_table').DataTable({
            dom: "<'row'<'col-sm-12 col-md-6'B><'col-sm-12 col-md-3'l><'col-sm-12 col-md-3'f>>" +
                "<'row'<'col-sm-12'tr>>" +
                "<'row'<'col-sm-12 col-md-12'ip>>",
            pageLength: 10,
            lengthMenu: [10, 20, 50, 100],
            buttons: [
                { extend: 'copyHtml5' },
                {
                    extend: 'excelHtml5',
                    title: function() { return `${ban_address_verified}_${sport}_banano_sports_indiv_leaderboard`; },
                },
                {
                    extend: 'csvHtml5',
                    title: function() { return `${ban_address_verified}_${sport}_banano_sports_indiv_leaderboard`; },
                },
                {
                    extend: 'pdfHtml5',
                    title: function() { return `${ban_address_verified}_${sport}_banano_sports_indiv_leaderboard`; },
                    orientation: 'portrait',
                    pageSize: 'A3',
                    text: 'PDF',
                    titleAttr: 'PDF'
                }
            ]
        });

    } else {

        // destroy datatable
        $('#sql_table').show();
        $("#sql_table_wrapper").show();
        $("#indiv_table").hide();
        $("#indiv_table_wrapper").hide();
        $('#sql_table').DataTable().clear().destroy();

        // loop through all rows
        inp_data.forEach(function(row) {
            if (row.ban_address == ban_address_verified) {
                html += '<tr class="table-info">';
            } else {
                html += "<tr>";
            }

            // loop through each cell (order matters)
            html += `<td>${row[week_col]}</td>`;
            html += `<td><a target='_blank' href='https://creeper.banano.cc/account/${row.ban_address}'>${row.ban_address}</a></td>`;
            html += `<td>${row.game_id}</td>`;
            html += `<td>${row.is_winner}</td>`;
            html += `<td>${row.is_tie}</td>`;
            html += `<td>${+(100*row.win_perc).toFixed(2)}</td>`;
            html += `<td>${row.bet_amount}</td>`;
            html += `<td>${row.payout}</td>`;
            html += `<td>${row.profit}</td>`;
            html += `<td>${+(100*row.return_perc).toFixed(2)}</td>`;

            // close the row
            html += "</tr>";
        });

        // shove the html in our elements
        $("#sql_table tbody").html("");
        $("#sql_table tbody").append(html);

        // remake data table
        $('#sql_table').DataTable({
            dom: "<'row'<'col-sm-12 col-md-6'B><'col-sm-12 col-md-3'l><'col-sm-12 col-md-3'f>>" +
                "<'row'<'col-sm-12'tr>>" +
                "<'row'<'col-sm-12 col-md-12'ip>>",
            pageLength: 10,
            lengthMenu: [10, 20, 50, 100],
            buttons: [
                { extend: 'copyHtml5' },
                {
                    extend: 'excelHtml5',
                    title: function() { return `${ban_address_verified}__${sport}_banano_sports_leaderboard`; },
                },
                {
                    extend: 'csvHtml5',
                    title: function() { return `${ban_address_verified}_${sport}_banano_sports_leaderboard`; },
                },
                {
                    extend: 'pdfHtml5',
                    title: function() { return `${ban_address_verified}_${sport}_banano_sports_leaderboard`; },
                    orientation: 'portrait',
                    pageSize: 'A3',
                    text: 'PDF',
                    titleAttr: 'PDF'
                }
            ]
        });
    }
}

// Plot Pool Amount vs Profit
function makeLeaderboardBarPlot(inp_data, ban_address) {
    let trace1 = {};
    let trace2 = {};

    // plot address if available else games
    if (ban_address !== "") {
        trace1 = {
            x: inp_data.map(x => x.game_id),
            y: inp_data.map(x => x.bet_amount),
            name: 'Total Bet',
            type: 'bar'
          };

        trace2 = {
            x: inp_data.map(x => x.game_id),
            y: inp_data.map(x => x.profit),
            name: 'Profit',
            type: 'bar'
          };

    } else {
        trace1 = {
            x: inp_data.map(x => x.ban_address),
            y: inp_data.map(x => x.bet_amount),
            name: 'Total Bet',
            type: 'bar'
          };

        trace2 = {
            x: inp_data.map(x => x.ban_address),
            y: inp_data.map(x => x.profit),
            name: 'Profit',
            type: 'bar'
          };
    }

    let plot_data = [trace1, trace2];
    let layout = {
        barmode: 'group',
        title: `Total Bet vs Profit`,
        yaxis: {'title': "BAN Amount"}
    };

    Plotly.newPlot('bar_plot', plot_data, layout);
}

function makeLeaderboardPiePlot(inp_data, ban_address) {
    let trace1 = {};

    if (ban_address !== "") {
        trace1 = {
            values: inp_data.map(x => x.bet_amount),
            labels: inp_data.map(x => x.game_id),
            type: 'pie',
            hole: .4,
          };
    } else {
        trace1 = {
            values: inp_data.map(x => x.bet_amount),
            labels: inp_data.map(x => x.ban_address),
            type: 'pie',
            hole: .4,
          };
    }

    let plot_data = [trace1];
    let layout = {
        title: `Whale Watch! (Total Pool Deposits)`
    };

    Plotly.newPlot('pie_plot', plot_data, layout);
}
