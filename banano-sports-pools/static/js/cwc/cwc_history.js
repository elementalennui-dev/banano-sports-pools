$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getDepositHistory("cwc", "match_round");
    });

    // get default week then load page
    getCurrentWeek("cwc", "match_round");
});
