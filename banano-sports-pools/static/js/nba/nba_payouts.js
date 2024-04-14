$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getPayouts("nba", "match_round");
    });

    getCurrentWeek("nba", "match_round");
});
