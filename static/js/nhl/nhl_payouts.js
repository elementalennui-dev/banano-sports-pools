$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getPayouts("nhl", "match_round");
    });

    getCurrentWeek("nhl", "match_round");
});
