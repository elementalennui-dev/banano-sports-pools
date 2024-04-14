$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getDepositHistory("nba", "match_round");
    });

    // get default week then load page
    getCurrentWeek("nba", "match_round");
});
