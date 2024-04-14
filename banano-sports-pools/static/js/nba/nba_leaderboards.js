$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getLeaderboards("nba", "match_round");
    });

    $("#week_inp,#season_inp").on("change", function() {
        getBanAddresses("nba");
    });

    // init
    getCurrentWeek("nba", "match_round");
});
