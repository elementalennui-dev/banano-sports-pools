$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getPayouts("cwc", "match_round");
    });

    getCurrentWeek("cwc", "match_round");
});
