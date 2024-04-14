$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getLeaderboards("nhl", "match_round");
    });

    $("#week_inp,#season_inp").on("change", function() {
        getBanAddresses("nhl");
    });

    // init
    getCurrentWeek("nhl", "match_round");
});
