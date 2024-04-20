// on page load
$(document).ready(function() {

    // load the main page of active deposits
    $("#week_inp, #season_inp, #team_inp").on("change", function (x) {
        let triggeredById = x.target.id;

        // trigger check
        if (triggeredById === 'week_inp' || triggeredById === 'season_inp') {
            // Logic for when week_inp or season_inp triggers the event
            $("#team_inp").val("All");
            getTeams("nfl");
        }

        $("#status_inp").val("All");
        $("#games").hide();
        $(".progress-bar").animate({
            width: "0%",
        }, 0);

        $("#progress_container").show();
        getGames("nfl");
        // Set the width to animate the progress bar, along with time duration in milliseconds
        $(".progress-bar").animate({
            width: "100%",
        }, 2000);
    })

    $("#confirm_deposit").on("click", function(x) {
        confirmDeposit("nfl");
    });

    // inits on page load
    getCurrentWeek("nfl");
});
