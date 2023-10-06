$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getLeaderboards("rwc", "match_round");
    });

    $("#week_inp,#season_inp").on("change", function() {
        getBanAddresses("rwc");
    });

    // init
    getCurrentWeek("rwc", "match_round");
});
