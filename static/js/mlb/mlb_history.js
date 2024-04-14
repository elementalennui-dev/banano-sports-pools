$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getDepositHistory("mlb", "match_round");
    });

    // get default week then load page
    getCurrentWeek("mlb", "match_round");
});
