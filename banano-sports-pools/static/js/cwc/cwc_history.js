$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getDepositHistory("rwc", "match_round");
    });

    // get default week then load page
    getCurrentWeek("rwc", "match_round");
});
