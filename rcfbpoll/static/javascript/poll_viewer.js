$(function() {
	$( "#year-selector" ).selectmenu({
		change: function (event, ui){
		    $("#poll-selector").submit()
		}
	});

	$( "#week-selector" ).selectmenu({
		change: function (event, ui){
		    $("#poll-selector").submit()
		}
	});
});