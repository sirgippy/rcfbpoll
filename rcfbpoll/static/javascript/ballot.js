var btn_index = 0;

$(function() {
	$( "#teams-accordion" ).accordion({
		collapsible: true,
		active: false
	});
});

$('.nav-tabs a').click(function(){
	$(this).tab('show');
})

$(function() {
	$( ".teamlist" ).sortable({
		revert: true,
		connectWith: "#ballot",
		
		helper: function(event,li) {
			this.copyHelper = li.clone().insertAfter(li);
			$(this).data('copied',false);
			return li.clone();
		},
		
		stop: function(event,ui) {
			var copied = $(this).data('copied');
			
			if (!copied) {
				this.copyHelper.remove();
				$(this).sortable('cancel');
			} else if ($("#ballot").children().length > 25) {
				ballotSizeExceededWarning();
				this.copyHelper.remove();
				$(this).sortable('cancel');
			} else if (isAlreadyInBallot(ui.item)){
				ballotDuplicateWarning();
				this.copyHelper.remove();
				$(this).sortable('cancel');
			} else {
				transformTeamToBallotEntry(ui.item);
			}
			
			this.copyHelper = null;
		},
		
		over: function(event,ui) {
			this.copyHelper.hide();
		},
		
		out: function(event,ui) {
			this.copyHelper.show();
		}
	});
	
	$( "#ballot" ).sortable({
		revert: true,
		cancel: ':input,button,.rationale',
		receive: function (event,ui) {
			ui.sender.data('copied',true);
		}
	});
	
});

function ballotSizeExceededWarning() {
	var text = "";
	text += '<div class="alert alert-warning alert-dismissible" role="alert">'
	text += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
	text += '<strong>Warning:</strong> Ballot is full. Remove a team to add another.</div>'
	$("#alert-container").html($("#alert-container").html() + text);
}

function isAlreadyInBallot(item) {
    current_entries = $("#ballot")

	return false;
}

function ballotDuplicateWarning() {
	var text = "";
	text += '<div class="alert alert-warning alert-dismissible" role="alert">'
	text += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
	text += '<strong>Warning:</strong> Team is already on ballot.</div>'
	$("#alert-container").html($("#alert-container").html() + text);
}

function transformTeamToBallotEntry(item) {
	item.append('<span class="ui-icon ui-icon-closethick close-button"></button>');
	
	item.append('<button class="btn btn-primary btn-xs rationale-button" type="button" data-toggle="collapse" data-target="#rationale' + btn_index + '" aria-expanded="false">Reason</button>');
	
	item.find('.close-button').button().click(function() {
			$(this).closest('li').remove();
		});
		
	item.append('<div id="rationale' + btn_index + '" class="rationale collapse" type="text" contenteditable="true" aria-expanded="false"></div>');
	
	btn_index++;
}