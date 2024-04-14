// on page load
$(document).ready(function() {

    // load the main page of active deposits
    $("#week_inp, #season_inp").on("change", function (x) {
        $("#status_inp").val("All");
        $("#games").hide();
        $(".progress-bar").animate({
            width: "0%",
        }, 0);

        $("#progress_container").show();
        getGames("rwc");
        // Set the width to animate the progress bar, along with time duration in milliseconds
        $(".progress-bar").animate({
            width: "100%",
        }, 2000);
    });

    $("#confirm_deposit").on("click", function(x) {
        confirmDeposit("rwc");
    });

    // inits on page load
    getCurrentWeek("rwc");
});
