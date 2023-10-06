$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getPayouts("rwc", "match_round");
    });

    getCurrentWeek("rwc", "match_round");
});
