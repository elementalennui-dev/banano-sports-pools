$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getDepositHistory("nhl", "match_round");
    });

    // get default week then load page
    getCurrentWeek("nhl", "match_round");
});
