$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getLeaderboards("nfl", "nfl_week");
    });

    $("#week_inp,#season_inp").on("change", function() {
        getBanAddresses("nfl");
    });

    // init
    getCurrentWeek("nfl", "nfl_week");
});
