$(document).ready(function() {

    $("#filter").click(function() {
        // alert("button clicked!");
        getPayouts("nfl", "nfl_week");
    });

    getCurrentWeek("nfl", "nfl_week");
});
