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

// gets the current Week, then populates payouts
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
            $("#week_inp").val(current_week);
            getPayouts(sport, week_col);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            alert("Something unexpected occurred and we were unable to process your request! Please submit a bug request to elementalennui on Discord.");
        }
    });
}

// call endpoint to query database
function getPayouts(sport, week_col) {
    let week_inp = $("#week_inp").val();
    let season_inp = $("#season_inp").val();
    let min_ban = $("#min_ban").val();
    let max_ban = $("#max_ban").val();

    // check if inputs are valid

    // create the payload
    let payload = {
        "week_inp": week_inp,
        "season_inp": season_inp,
        "min_ban": min_ban,
        "max_ban": max_ban
    }

    // Perform a POST request to the query URL
    $.ajax({
        type: "POST",
        url: `/sports/api/get_payouts/${sport}`,
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({ "data": payload }),
        success: function(returnedData) {
            renderTable(returnedData, week_col, sport);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            alert("Something unexpected occurred and we were unable to process your request! Please submit a bug request to elementalennui on Discord.");
        }
    });

}

function renderTable(inp_data, week_col, sport) {
    // init html string
    let html = "";

    // destroy datatable
    $('#payouts_table').DataTable().clear().destroy();

    // loop through all rows
    inp_data.forEach(function(row) {
        if (row.ban_address == ban_address_verified) {
            html += '<tr class="table-info">';
        } else {
            html += "<tr>";
        }

        // loop through each cell (order matters)
        html += `<td>${row[week_col]}</td>`;
        html += `<td>${row.game_id}</td>`;
        html += `<td><a target='_blank' href='https://creeper.banano.cc/account/${row.ban_address}'>${row.ban_address}</a></td>`;
        html += `<td>${row.total_bet}</td>`;
        html += `<td>${row.winning_pool}</td>`;
        html += `<td>${+row.percent_of_pool.toFixed(2)}</td>`;
        html += `<td>${row.losing_pool}</td>`;
        html += `<td>${row.amount_won}</td>`;
        html += `<td>${row.payout}</td>`;
        html += `<td><a target='_blank' href='https://creeper.banano.cc/hash/${row.block}'>View</a></td>`;

        // close the row
        html += "</tr>";
    });

    // shove the html in our elements
    // console.log(html);
    $("#payouts_table tbody").html("");
    $("#payouts_table tbody").append(html);

    // remake data table
    $('#payouts_table').DataTable({
        dom: "<'row'<'col-sm-12 col-md-6'B><'col-sm-12 col-md-3'l><'col-sm-12 col-md-3'f>>" +
            "<'row'<'col-sm-12'tr>>" +
            "<'row'<'col-sm-12 col-md-12'ip>>",
        pageLength: 10,
        lengthMenu: [10, 20, 50, 100],
        buttons: [
            { extend: 'copyHtml5' },
            {
                extend: 'excelHtml5',
                title: function() { return `${ban_address_verified}_${sport}_banano_sports_nfl_deposits_payouts`; },
            },
            {
                extend: 'csvHtml5',
                title: function() { return `${ban_address_verified}_${sport}_banano_sports_nfl_deposits_payouts`; },
            },
            {
                extend: 'pdfHtml5',
                title: function() { return `${ban_address_verified}_${sport}_banano_sports_nfl_deposits_payouts`; },
                orientation: 'portrait',
                pageSize: 'A3',
                text: 'PDF',
                titleAttr: 'PDF'
            }
        ]
    });;
}
