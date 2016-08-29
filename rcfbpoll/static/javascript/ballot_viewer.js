$(function() {
	$( "#year-selector" ).change(function() {
        $("#ballot-selector").submit()
	});

	$( "#week-selector" ).change(function() {
        $("#ballot-selector").submit()
	});

	$( "#username-selector" ).change(function() {
        $("#ballot-selector").submit()
	});
});