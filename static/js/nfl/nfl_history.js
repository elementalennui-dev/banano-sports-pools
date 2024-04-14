$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getDepositHistory("nfl", "nfl_week");
    });

    // get default week then load page
    getCurrentWeek("nfl", "nfl_week");
});
