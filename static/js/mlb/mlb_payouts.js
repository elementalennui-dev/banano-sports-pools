$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getPayouts("mlb", "match_round");
    });

    getCurrentWeek("mlb", "match_round");
});
