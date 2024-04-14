$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getLeaderboards("cwc", "match_round");
    });

    $("#week_inp,#season_inp").on("change", function() {
        getBanAddresses("cwc");
    });

    // init
    getCurrentWeek("cwc", "match_round");
});
