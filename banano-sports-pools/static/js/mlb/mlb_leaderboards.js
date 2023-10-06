$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getLeaderboards("mlb", "match_round");
    });

    $("#week_inp,#season_inp").on("change", function() {
        getBanAddresses("mlb");
    });

    // init
    getCurrentWeek("mlb", "match_round");
});
