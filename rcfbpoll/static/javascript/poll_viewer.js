$(function() {
	$( "#year-selector" ).selectmenu({
		change: function (event, ui){
		    $("#poll-selector").submit()
		},
		width: 90,
	});

	$( "#week-selector" ).selectmenu({
		change: function (event, ui){
		    $("#poll-selector").submit()
		},
		width: 150,
	});

	$( "#ppv" ).tooltip({
	    container: 'body'
	})
});