var theme = "yeti";
var ban_address_verified = "";

if (window.name) {
    theme = JSON.parse(window.name).theme;
    ban_address_verified = JSON.parse(window.name).ban_address_verified;
}

$(document).ready(function() {
    console.log("Page Loaded");

    // set theme
    if (theme) {
        $('head link').last().after('<link rel="stylesheet" type="text/css" href="https://stackpath.bootstrapcdn.com/bootswatch/4.5.2/' + theme + '/bootstrap.min.css">');
        $('#themeSelect').val(theme);
    } else {
        //order matters in CSS load
        $('head link').last().after('<link rel="stylesheet" type="text/css" href="https://stackpath.bootstrapcdn.com/bootswatch/4.5.2/' + $('#themeSelect').val() + '/bootstrap.min.css">');
        window.name = JSON.stringify({ //save to window, in case we move across pages
            ban_address_verified: ban_address_verified,
            theme: $('#themeSelect').val()
        });
    }

    // event listeners
    $('#themeSelect').change(function() {
        let styleSheets = $('head').find('link');
        styleSheets.each(function() {
            if ($(this).attr('href').includes('bootswatch')) {
                $(this).remove();
            }
        });

        // add new sheet
        $('head link').last().after('<link rel="stylesheet" type="text/css" href="https://stackpath.bootstrapcdn.com/bootswatch/4.5.2/' + $('#themeSelect').val() + '/bootstrap.min.css">');
        window.name = JSON.stringify({ //save to window, in case we move across pages
            ban_address_verified: ban_address_verified,
            theme: $('#themeSelect').val()
        });
    });
});